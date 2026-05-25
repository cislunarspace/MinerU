# Copyright (c) Opendatalab. All rights reserved.

import os
import subprocess
import sys
from pathlib import Path

try:
    from PyQt6.QtCore import QProcess, Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenuBar,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QSpinBox,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QCheckBox,
    )
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False


MAX_LOG_LINES = 500


class LLMConfigDialog(QDialog):
    """LLM configuration dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM 配置")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # API settings
        api_group = QGroupBox("API 设置")
        api_layout = QFormLayout(api_group)

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.deepseek.com/")
        api_layout.addRow("API 地址:", self.base_url_edit)

        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("deepseek-chat")
        api_layout.addRow("模型名称:", self.model_name_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入 API Key")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("API Key:", self.api_key_edit)

        layout.addWidget(api_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def load_config(self, config):
        """Load config into the dialog."""
        agent = config.get('llm_agent', {})
        self.base_url_edit.setText(agent.get('base_url', ''))
        self.model_name_edit.setText(agent.get('model_name', ''))
        self.api_key_edit.setText(agent.get('api_key', ''))

    def get_config(self):
        """Get config from the dialog."""
        return {
            'base_url': self.base_url_edit.text().strip(),
            'model_name': self.model_name_edit.text().strip(),
            'api_key': self.api_key_edit.text().strip(),
        }


def load_llm_config():
    """Load LLM config from conf.yaml."""
    import yaml
    from mineru.cli.llm_translate.config import get_conf

    conf = get_conf()
    return conf.get_conf()


def save_llm_config(config_dict):
    """Save LLM config to conf.yaml."""
    import yaml
    from pathlib import Path

    conf_path = Path(__file__).parent.parent.parent / "conf.yaml"
    with open(conf_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config_dict, f, allow_unicode=True, sort_keys=False)


class MinerUGui(QMainWindow if HAS_PYQT6 else object):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MinerU GUI Launcher")
        self.setMinimumSize(700, 700)
        self.process = None
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Menu bar
        self._create_menu_bar()

        # --- Mode selection ---
        mode_group = QGroupBox("功能模式")
        mode_layout = QHBoxLayout(mode_group)
        self.radio_wf1 = QRadioButton("工作流1: PDF → 翻译 PDF")
        self.radio_wf2 = QRadioButton("工作流2: Markdown → 翻译")
        self.radio_wf3 = QRadioButton("工作流3: PDF → Markdown")
        self.radio_wf1.setChecked(True)
        self.radio_wf1.toggled.connect(self._on_mode_changed)
        self.radio_wf2.toggled.connect(self._on_mode_changed)
        self.radio_wf3.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.radio_wf1)
        mode_layout.addWidget(self.radio_wf2)
        mode_layout.addWidget(self.radio_wf3)
        mode_layout.addStretch()
        layout.addWidget(mode_group)

        # --- Input path ---
        input_group = QGroupBox("输入路径")
        input_layout = QVBoxLayout(input_group)

        radio_layout = QHBoxLayout()
        self.radio_file = QRadioButton("文件")
        self.radio_folder = QRadioButton("文件夹")
        self.radio_file.setChecked(True)
        self.radio_file.toggled.connect(self._on_input_type_changed)
        radio_layout.addWidget(self.radio_file)
        radio_layout.addWidget(self.radio_folder)
        radio_layout.addStretch()
        input_layout.addLayout(radio_layout)

        path_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择输入文件或文件夹...")
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_input)
        path_layout.addWidget(self.input_path_edit)
        path_layout.addWidget(self.browse_btn)
        input_layout.addLayout(path_layout)
        layout.addWidget(input_group)

        # --- Output directory ---
        output_group = QGroupBox("输出目录")
        output_layout = QHBoxLayout(output_group)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("输出目录...")
        self.output_browse_btn = QPushButton("浏览...")
        self.output_browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_browse_btn)
        layout.addWidget(output_group)

        # --- MinerU options ---
        self.mineru_options_group = QGroupBox("MinerU 选项")
        mineru_options_layout = QHBoxLayout(self.mineru_options_group)
        mineru_options_layout.addWidget(QLabel("Backend:"))
        self.radio_gpu = QRadioButton("GPU")
        self.radio_cpu = QRadioButton("CPU")
        self.radio_gpu.setChecked(True)
        mineru_options_layout.addWidget(self.radio_gpu)
        mineru_options_layout.addWidget(self.radio_cpu)
        mineru_options_layout.addStretch()
        layout.addWidget(self.mineru_options_group)

        # --- Page range ---
        self.page_range_group = QGroupBox("页码范围")
        page_range_layout = QHBoxLayout(self.page_range_group)
        page_range_layout.addWidget(QLabel("从"))
        self.start_page_spin = QSpinBox()
        self.start_page_spin.setMinimum(1)
        self.start_page_spin.setValue(1)
        self.start_page_spin.setPrefix(" ")
        page_range_layout.addWidget(self.start_page_spin)
        page_range_layout.addWidget(QLabel("到"))
        self.end_page_spin = QSpinBox()
        self.end_page_spin.setMinimum(0)
        self.end_page_spin.setValue(0)
        self.end_page_spin.setSpecialValueText("结束")
        self.end_page_spin.setPrefix(" ")
        page_range_layout.addWidget(self.end_page_spin)
        page_range_layout.addStretch()
        layout.addWidget(self.page_range_group)

        # --- Header correction ---
        self.header_correction_group = QGroupBox("标题校正")
        header_layout = QHBoxLayout(self.header_correction_group)
        header_layout.addWidget(QLabel("方式:"))
        self.header_type_combo = QComboBox()
        self.header_type_combo.addItems(["no", "bookmark", "by_llm", "by_llm_easy"])
        self.header_type_combo.setCurrentText("bookmark")
        header_layout.addWidget(self.header_type_combo)
        header_layout.addStretch()
        layout.addWidget(self.header_correction_group)

        # --- Translation options ---
        self.translation_options_group = QGroupBox("翻译选项")
        trans_layout = QVBoxLayout(self.translation_options_group)
        self.generate_pdf_check = QCheckBox("翻译后生成 PDF")
        self.generate_pdf_check.setChecked(True)
        trans_layout.addWidget(self.generate_pdf_check)
        layout.addWidget(self.translation_options_group)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("运行")
        self.run_btn.clicked.connect(self._run)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        btn_layout.addStretch()
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # --- Log output ---
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group, stretch=1)

        # Initialize
        self._on_mode_changed()
        self._set_default_output_dir()

    def _create_menu_bar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        settings_menu = menubar.addMenu("设置")

        llm_config_action = settings_menu.addAction("LLM 配置...")
        llm_config_action.triggered.connect(self._show_llm_config)

    def _show_llm_config(self):
        config = load_llm_config()
        dialog = LLMConfigDialog(self)
        dialog.load_config(config)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            # Update config
            if 'llm_agent' not in config:
                config['llm_agent'] = {}
            config['llm_agent'].update(new_config)
            save_llm_config(config)
            # Reload config
            from mineru.cli.llm_translate import config as llm_config_module
            llm_config_module.reload_conf()
            QMessageBox.information(self, "配置已保存", "LLM 配置已保存到 conf.yaml")

    def _on_mode_changed(self):
        """Update UI based on selected mode."""
        is_wf1 = self.radio_wf1.isChecked()
        is_wf2 = self.radio_wf2.isChecked()
        is_wf3 = self.radio_wf3.isChecked()

        # MinerU options: show for wf1 and wf3
        self.mineru_options_group.setVisible(is_wf1 or is_wf3)

        # Page range: show for wf1
        self.page_range_group.setVisible(is_wf1)

        # Header correction: show for wf1 and wf2
        self.header_correction_group.setVisible(is_wf1 or is_wf2)

        # Translation options: show for wf1 and wf2
        self.translation_options_group.setVisible(is_wf1 or is_wf2)

        # Input type: wf1/wf3 use file, wf2 uses file only
        self.radio_file.setChecked(True)
        self.radio_folder.setVisible(is_wf1 or is_wf3)
        self.radio_file.setVisible(True)

        # Update placeholders
        if is_wf1:
            self.input_path_edit.setPlaceholderText("选择输入 PDF 文件...")
            self.output_dir_edit.setText(str(Path.home() / "Downloads" / "mineru-translation"))
        elif is_wf2:
            self.input_path_edit.setPlaceholderText("选择输入 Markdown 文件...")
            self.output_dir_edit.setText(str(Path.home() / "Downloads"))
        else:
            self.input_path_edit.setPlaceholderText("选择输入 PDF 文件或文件夹...")
            self.output_dir_edit.setText(str(Path.home() / "Downloads" / "mineru-output"))

    def _on_input_type_changed(self):
        """Update UI when input type changes."""
        # File mode - browse for single file
        # Folder mode - browse for directory
        pass

    def _set_default_output_dir(self):
        """Set default output directory."""
        self.output_dir_edit.setText(str(Path.home() / "Downloads" / "mineru-output"))

    def _browse_input(self):
        """Browse for input path."""
        if self.radio_wf2.isChecked():
            # Markdown file only
            path, _ = QFileDialog.getOpenFileName(
                self, "选择 Markdown 文件", "",
                "Markdown Files (*.md);;All Files (*)"
            )
        elif self.radio_folder.isChecked():
            path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择输入文件", "",
                "PDF Files (*.pdf);;All Files (*)"
            )

        if path:
            self.input_path_edit.setText(path)

    def _browse_output(self):
        """Browse for output directory."""
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_dir_edit.setText(path)

    def _find_pdf_for_markdown(self, md_path):
        """Find PDF file for markdown in the same directory."""
        md_path = Path(md_path)
        # Try same name with .pdf extension
        pdf_path = md_path.parent / f"{md_path.stem}.pdf"
        if pdf_path.exists():
            return str(pdf_path)

        # Try common patterns
        for pattern in ["*.pdf", "*.PDF"]:
            for pdf in md_path.parent.glob(pattern):
                if pdf.stem == md_path.stem:
                    return str(pdf)

        return None

    def _run(self):
        """Run the selected workflow."""
        input_path = self.input_path_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()

        # Validate input
        if not input_path:
            QMessageBox.warning(self, "输入错误", "输入路径不能为空")
            return

        p = Path(input_path)
        if not p.exists():
            QMessageBox.warning(self, "输入错误", f"路径不存在: {input_path}")
            return

        # Validate output
        if not output_dir:
            QMessageBox.warning(self, "输出错误", "输出目录不能为空")
            return

        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        if self.radio_wf1.isChecked():
            self._run_workflow1(input_path, output_dir)
        elif self.radio_wf2.isChecked():
            self._run_workflow2(input_path, output_dir)
        else:
            self._run_workflow3(input_path, output_dir)

    def _run_workflow1(self, input_path, output_dir):
        """Workflow 1: PDF → MinerU → Translate → PDF."""
        backend = "CPU" if self.radio_cpu.isChecked() else "GPU"
        start_page = self.start_page_spin.value()
        end_page = self.end_page_spin.value() or None
        header_type = self.header_type_combo.currentText()
        generate_pdf = self.generate_pdf_check.isChecked()

        working_dir = str(Path(__file__).parent.parent.parent)

        # Disable buttons to prevent concurrent execution
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        # Step 1: MinerU conversion
        self.log_text.append("=" * 50)
        self.log_text.append("步骤 1: MinerU 转换 PDF → Markdown")
        self.log_text.append("=" * 50)

        mineru_output = os.path.join(output_dir, "mineru_output")
        os.makedirs(mineru_output, exist_ok=True)

        cmd = ["uv", "run", "mineru"]
        cmd.extend(["-p", input_path])
        cmd.extend(["-o", mineru_output])
        if backend == "CPU":
            cmd.extend(["-b", "pipeline"])

        self._display_and_start(cmd, working_dir, wait_for_finish=True)

        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.waitForFinished(-1)

        # Find the generated markdown
        md_file = None
        for f in Path(mineru_output).rglob("*.md"):
            if "_content" not in f.name:  # Skip content list files
                md_file = f
                break

        if not md_file:
            self.log_text.append("错误: 未找到生成的 Markdown 文件")
            self._enable_buttons()
            return

        self.log_text.append(f"找到 Markdown: {md_file}")

        # Step 2: Translate
        self.log_text.append("")
        self.log_text.append("=" * 50)
        self.log_text.append("步骤 2: 翻译 Markdown")
        self.log_text.append("=" * 50)

        # Translate using llm_translate
        try:
            from mineru.cli.llm_translate import Translator
            translator = Translator()
            translated_md = translator.translate(str(md_file))
            self.log_text.append(f"翻译完成: {translated_md}")
        except Exception as e:
            self.log_text.append(f"翻译错误: {e}")
            self._enable_buttons()
            return

        # Step 3: Header correction (if needed)
        if header_type != "no":
            self.log_text.append("")
            self.log_text.append("=" * 50)
            self.log_text.append("步骤 3: 标题校正")
            self.log_text.append("=" * 50)

            try:
                from mineru.cli.llm_translate import get_corrector
                corrector = get_corrector(header_type)
                if corrector:
                    # Need PDF for bookmark correction
                    pdf_path = input_path if header_type == "bookmark" else None
                    if header_type == "bookmark":
                        self.log_text.append(f"使用书签校正，关联 PDF: {pdf_path}")
                    # Apply correction
                    corrected_md = str(translated_md).replace("_trans", "_correct")
                    success = corrector.do_correct(translated_md, corrected_md)
                    if success:
                        self.log_text.append(f"校正完成: {corrected_md}")
                        translated_md = corrected_md
                    else:
                        self.log_text.append("校正失败，使用原始翻译文件")
            except Exception as e:
                self.log_text.append(f"标题校正错误: {e}")

        # Step 4: Generate PDF (if requested)
        if generate_pdf:
            self.log_text.append("")
            self.log_text.append("=" * 50)
            self.log_text.append("步骤 4: 生成 PDF")
            self.log_text.append("=" * 50)

            try:
                import platform
                import shutil
                import subprocess

                md_path = Path(translated_md)
                # Copy to output dir
                dest_md = Path(output_dir) / md_path.name
                shutil.copy(md_path, dest_md)

                # Use pandoc to generate PDF
                if platform.system() == "Linux":
                    cmd = ["pandoc", str(dest_md), "-o", str(dest_md.with_suffix(".pdf")),
                           "--pdf-engine=prince", "-V", "mainfont=STSong", "-V", "CJKmainfont=STSong"]
                else:
                    cmd = ["pandoc", str(dest_md), "-o", str(dest_md.with_suffix(".pdf")),
                           "--pdf-engine=prince"]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_text.append(f"PDF 生成完成: {dest_md.with_suffix('.pdf')}")
                else:
                    self.log_text.append(f"PDF 生成失败: {result.stderr}")
            except Exception as e:
                self.log_text.append(f"PDF 生成错误: {e}")

        self.log_text.append("")
        self.log_text.append("=" * 50)
        self.log_text.append("工作流 1 完成!")
        self.log_text.append("=" * 50)
        self._enable_buttons()
        self._notify("MinerU", "工作流 1 完成")

    def _run_workflow2(self, input_path, output_dir):
        """Workflow 2: Markdown → Translate → (PDF)."""
        header_type = self.header_type_combo.currentText()
        generate_pdf = self.generate_pdf_check.isChecked()

        # Disable buttons to prevent concurrent execution
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        # Find associated PDF
        pdf_path = self._find_pdf_for_markdown(input_path)
        if pdf_path:
            self.log_text.append(f"找到关联 PDF: {pdf_path}")
        else:
            self.log_text.append("未找到关联 PDF，标题校正将使用 LLM 方式")
            if header_type == "bookmark":
                header_type = "by_llm"
                self.log_text.append(f"标题校正方式已改为: {header_type}")

        # Translate
        self.log_text.append("")
        self.log_text.append("=" * 50)
        self.log_text.append("步骤 1: 翻译 Markdown")
        self.log_text.append("=" * 50)

        try:
            from mineru.cli.llm_translate import Translator
            translator = Translator()
            translated_md = translator.translate(input_path)
            self.log_text.append(f"翻译完成: {translated_md}")
        except Exception as e:
            self.log_text.append(f"翻译错误: {e}")
            self._enable_buttons()
            return

        # Header correction
        if header_type != "no":
            self.log_text.append("")
            self.log_text.append("=" * 50)
            self.log_text.append("步骤 2: 标题校正")
            self.log_text.append("=" * 50)

            try:
                from mineru.cli.llm_translate import get_corrector
                corrector = get_corrector(header_type)
                if corrector:
                    corrected_md = str(translated_md).replace("_trans", "_correct")
                    success = corrector.do_correct(translated_md, corrected_md)
                    if success:
                        self.log_text.append(f"校正完成: {corrected_md}")
                        translated_md = corrected_md
                    else:
                        self.log_text.append("校正失败，使用原始翻译文件")
            except Exception as e:
                self.log_text.append(f"标题校正错误: {e}")

        # Generate PDF if requested
        if generate_pdf:
            self.log_text.append("")
            self.log_text.append("=" * 50)
            self.log_text.append("步骤 3: 生成 PDF")
            self.log_text.append("=" * 50)

            try:
                import platform
                import shutil
                import subprocess

                md_path = Path(translated_md)
                dest_md = Path(output_dir) / md_path.name
                shutil.copy(md_path, dest_md)

                if platform.system() == "Linux":
                    cmd = ["pandoc", str(dest_md), "-o", str(dest_md.with_suffix(".pdf")),
                           "--pdf-engine=prince", "-V", "mainfont=STSong", "-V", "CJKmainfont=STSong"]
                else:
                    cmd = ["pandoc", str(dest_md), "-o", str(dest_md.with_suffix(".pdf")),
                           "--pdf-engine=prince"]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_text.append(f"PDF 生成完成: {dest_md.with_suffix('.pdf')}")
                else:
                    self.log_text.append(f"PDF 生成失败: {result.stderr}")
            except Exception as e:
                self.log_text.append(f"PDF 生成错误: {e}")

        self.log_text.append("")
        self.log_text.append("=" * 50)
        self.log_text.append("工作流 2 完成!")
        self.log_text.append("=" * 50)
        self._enable_buttons()
        self._notify("MinerU", "工作流 2 完成")

    def _run_workflow3(self, input_path, output_dir):
        """Workflow 3: PDF → MinerU → Markdown."""
        backend = "CPU" if self.radio_cpu.isChecked() else "GPU"
        cmd = ["uv", "run", "mineru"]
        cmd.extend(["-p", input_path])
        cmd.extend(["-o", output_dir])
        if backend == "CPU":
            cmd.extend(["-b", "pipeline"])

        working_dir = str(Path(__file__).parent.parent.parent)
        self._display_and_start(cmd, working_dir)

    def _display_and_start(self, cmd, working_dir, wait_for_finish=False):
        """Display command in log and start the process."""
        self.log_text.clear()

        def quote(s):
            return f"'{s}'" if ' ' in s else s
        display_cmd = ' '.join(quote(a) for a in cmd)
        self.log_text.append(f"$ {display_cmd}\n")

        self.process = QProcess(self)
        self.process.setWorkingDirectory(working_dir)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_output)
        self.process.readyReadStandardError.connect(self._on_output)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)

        self.process.start(cmd[0], cmd[1:])

        if wait_for_finish:
            self.process.waitForFinished(-1)

    def _enable_buttons(self):
        """Re-enable run button."""
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def _cancel(self):
        """Cancel the running process."""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.log_text.append("\n[进程已被用户取消]")
            self._notify("MinerU", "任务已取消")

    def _on_output(self):
        """Handle process output."""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            if data:
                self.log_text.append(data.rstrip())
                # Trim excess lines
                doc = self.log_text.document()
                if doc.blockCount() > MAX_LOG_LINES:
                    cursor = self.log_text.cursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.movePosition(
                        cursor.MoveOperation.Down,
                        cursor.MoveMode.KeepAnchor,
                        doc.blockCount() - MAX_LOG_LINES,
                    )
                    cursor.removeSelectedText()
                # Auto-scroll
                sb = self.log_text.verticalScrollBar()
                sb.setValue(sb.maximum())

    def _on_finished(self, exit_code, exit_status):
        """Handle process finished."""
        self.log_text.append(f"\n[进程结束，退出码 {exit_code}]")
        self._enable_buttons()
        self.process = None
        if exit_code == 0:
            self._notify("MinerU", "任务完成")
        else:
            self._notify("MinerU", f"任务失败 (退出码: {exit_code})")

    def _on_error(self, error):
        """Handle process error."""
        self.log_text.append(f"\n[进程错误: {error.name}]")
        self._enable_buttons()
        self.process = None
        self._notify("MinerU", f"进程错误: {error.name}")

    def _notify(self, title, body):
        """Send desktop notification."""
        try:
            subprocess.Popen(["notify-send", title, body])
        except FileNotFoundError:
            pass

    def closeEvent(self, event):
        """Handle window close."""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            reply = QMessageBox.question(
                self, "确认退出",
                "有任务正在运行，是否终止?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.process.kill()
                self.process.waitForFinished(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point."""
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("Error: PyQt6 is not installed.")
        print("Install it with: uv pip install PyQt6")
        print("Or: pip install PyQt6")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MinerUGui()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

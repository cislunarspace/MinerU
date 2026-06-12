# Copyright (c) Opendatalab. All rights reserved.

import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

try:
    from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal
    from PyQt6.QtWidgets import (
        QComboBox,
        QDialog,
        QFileDialog,
        QFormLayout,
        QGridLayout,
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


def build_command(input_path, output_dir, backend, api_url=None):
    cmd = ["uv", "run", "mineru", "-p", input_path, "-o", output_dir]
    if backend == "CPU":
        cmd.extend(["-b", "pipeline"])
    if api_url:
        cmd.extend(["--api-url", api_url])
    return cmd


def validate_input(input_path):
    if not input_path or not input_path.strip():
        return "Input path is empty"

    if not Path(input_path).exists():
        return f"Path does not exist: {input_path}"

    return None


class LLMConfigDialog(QDialog):
    """LLM configuration dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("模型接口设置")
        self.setMinimumWidth(420)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # API settings
        api_group = QGroupBox("模型接口")
        api_layout = QFormLayout(api_group)

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.deepseek.com/")
        api_layout.addRow("服务端点:", self.base_url_edit)

        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("deepseek-chat")
        api_layout.addRow("模型标识:", self.model_name_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入 API Key")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("访问密钥:", self.api_key_edit)

        layout.addWidget(api_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("应用配置")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("关闭")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
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


class WorkflowWorker(QObject):
    """Worker object for running workflows in background."""

    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)  # success, message

    def __init__(self, gui_parent=None):
        super().__init__()
        self._is_running = True
        self._workflow_done = False
        self.parent = gui_parent  # Reference to the GUI window

    def log(self, message):
        """Log a message from the worker (thread-safe)."""
        self.log_signal.emit(message)

    def stop(self):
        """Request the worker to stop."""
        self._is_running = False

    def is_running(self):
        """Check if the worker should continue running."""
        return self._is_running and not self._workflow_done

    def isFinished(self):
        """Check if workflow is done."""
        return self._workflow_done

    def do_work(self, workflow_func=None):
        """Execute the workflow function."""
        try:
            self._is_running = True
            if workflow_func is None:
                workflow_func = self.workflow_func
            workflow_func(self)
        except Exception as e:
            self.log_signal.emit(f"错误: {e}")
            self.finished_signal.emit(False, str(e))
        finally:
            self._workflow_done = True

    def run_process(self, cmd, cwd):
        """Run a process and stream output line by line."""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        self.parent.mineru_process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

        # Keep a local reference so a concurrent cancel/reset cannot turn this
        # into a None.wait() call while we are still draining the pipe.
        process = self.parent.mineru_process
        assert process.stdout is not None
        for line in iter(process.stdout.readline, ""):
            if not self._is_running:
                break
            self.log(line.rstrip())

        returncode = process.wait()
        self.parent.mineru_process = None
        return returncode


class MinerUGui(QMainWindow if HAS_PYQT6 else object):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MinerU 控制台")
        self.setMinimumSize(720, 680)
        self.process = None
        self._api_server_process = None
        self._api_url = None
        self._api_temp_dir = None
        self._api_server_lock = threading.Lock()
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 16)

        # Header row: title + status
        header_layout = QHBoxLayout()
        self.title_label = QLabel("MinerU 控制台")
        font = self.title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.status_text = QLabel("就绪")
        self.status_text.setEnabled(False)
        header_layout.addWidget(self.status_text)
        layout.addLayout(header_layout)

        # Menu bar
        self._create_menu_bar()

        # --- Mode selection ---
        mode_group = QGroupBox("处理模式")
        mode_layout = QHBoxLayout(mode_group)
        self.radio_wf1 = QRadioButton("PDF 转译排版图")
        self.radio_wf2 = QRadioButton("Markdown 转译排版图")
        self.radio_wf3 = QRadioButton("仅提取 Markdown")
        self.radio_wf1.setChecked(True)
        self.radio_wf1.toggled.connect(self._on_mode_changed)
        self.radio_wf2.toggled.connect(self._on_mode_changed)
        self.radio_wf3.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.radio_wf1)
        mode_layout.addWidget(self.radio_wf2)
        mode_layout.addWidget(self.radio_wf3)
        mode_layout.addStretch()
        layout.addWidget(mode_group)

        # --- Input and output paths ---
        paths_group = QGroupBox("路径")
        paths_layout = QFormLayout(paths_group)
        paths_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        paths_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Input type row
        input_type_layout = QHBoxLayout()
        self.radio_file = QRadioButton("文件")
        self.radio_folder = QRadioButton("文件夹")
        self.radio_file.setChecked(True)
        self.radio_file.toggled.connect(self._on_input_type_changed)
        input_type_layout.addWidget(self.radio_file)
        input_type_layout.addWidget(self.radio_folder)
        input_type_layout.addStretch()
        paths_layout.addRow("输入类型:", input_type_layout)

        # Input path row
        input_path_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择输入文件或文件夹...")
        self.browse_btn = QPushButton("选择…")
        self.browse_btn.setFixedWidth(70)
        self.browse_btn.clicked.connect(self._browse_input)
        input_path_layout.addWidget(self.input_path_edit)
        input_path_layout.addWidget(self.browse_btn)
        paths_layout.addRow("输入路径:", input_path_layout)

        # Output dir row
        output_path_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("输出目录...")
        self.output_browse_btn = QPushButton("选择…")
        self.output_browse_btn.setFixedWidth(70)
        self.output_browse_btn.clicked.connect(self._browse_output)
        output_path_layout.addWidget(self.output_dir_edit)
        output_path_layout.addWidget(self.output_browse_btn)
        paths_layout.addRow("输出目录:", output_path_layout)

        layout.addWidget(paths_group)

        # --- Options grid ---
        options_group = QGroupBox("处理选项")
        options_layout = QGridLayout(options_group)
        options_layout.setColumnStretch(1, 1)
        options_layout.setColumnStretch(3, 1)

        # Backend
        options_layout.addWidget(QLabel("运算后端:"), 0, 0)
        backend_layout = QHBoxLayout()
        self.radio_gpu = QRadioButton("GPU 加速")
        self.radio_cpu = QRadioButton("CPU 兼容")
        self.radio_gpu.setChecked(True)
        backend_layout.addWidget(self.radio_gpu)
        backend_layout.addWidget(self.radio_cpu)
        backend_layout.addStretch()
        options_layout.addLayout(backend_layout, 0, 1)

        # Page range
        options_layout.addWidget(QLabel("处理页码:"), 0, 2)
        page_range_layout = QHBoxLayout()
        self.page_from_label = QLabel("从")
        self.start_page_spin = QSpinBox()
        self.start_page_spin.setMinimum(1)
        self.start_page_spin.setValue(1)
        self.start_page_spin.setPrefix(" ")
        page_range_layout.addWidget(self.page_from_label)
        page_range_layout.addWidget(self.start_page_spin)
        self.page_to_label = QLabel("到")
        self.end_page_spin = QSpinBox()
        self.end_page_spin.setMinimum(0)
        self.end_page_spin.setValue(0)
        self.end_page_spin.setSpecialValueText("结束")
        self.end_page_spin.setPrefix(" ")
        page_range_layout.addWidget(self.page_to_label)
        page_range_layout.addWidget(self.end_page_spin)
        page_range_layout.addStretch()
        options_layout.addLayout(page_range_layout, 0, 3)

        # Header correction
        options_layout.addWidget(QLabel("目录校正:"), 1, 0)
        header_layout = QHBoxLayout()
        self.header_type_combo = QComboBox()
        self.header_type_combo.addItems(["no", "bookmark", "by_llm", "by_llm_easy"])
        self.header_type_combo.setCurrentText("bookmark")
        header_layout.addWidget(self.header_type_combo)
        header_layout.addStretch()
        options_layout.addLayout(header_layout, 1, 1)

        # Generate PDF
        options_layout.addWidget(QLabel("输出选项:"), 1, 2)
        output_options_layout = QHBoxLayout()
        self.generate_pdf_check = QCheckBox("转换后生成 PDF")
        self.generate_pdf_check.setChecked(True)
        output_options_layout.addWidget(self.generate_pdf_check)
        output_options_layout.addStretch()
        options_layout.addLayout(output_options_layout, 1, 3)

        layout.addWidget(options_group)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.open_output_btn = QPushButton("打开输出目录")
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.clicked.connect(self._open_output_dir)
        self.run_btn = QPushButton("开始处理")
        self.run_btn.setDefault(True)
        self.run_btn.clicked.connect(self._run)
        self.cancel_btn = QPushButton("停止")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.open_output_btn)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # --- Log output ---
        log_group = QGroupBox("运行日志")
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

        settings_menu = menubar.addMenu("模型")

        llm_config_action = settings_menu.addAction("API 设置...")
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
            QMessageBox.information(self, "配置已应用", "模型接口配置已保存到 conf.yaml")

    def _on_mode_changed(self):
        """Update UI based on selected mode."""
        is_wf1 = self.radio_wf1.isChecked()
        is_wf2 = self.radio_wf2.isChecked()
        is_wf3 = self.radio_wf3.isChecked()

        # Show/hide option rows based on workflow
        self.radio_gpu.setVisible(is_wf1 or is_wf3)
        self.radio_cpu.setVisible(is_wf1 or is_wf3)
        self.page_from_label.setVisible(is_wf1)
        self.start_page_spin.setVisible(is_wf1)
        self.page_to_label.setVisible(is_wf1)
        self.end_page_spin.setVisible(is_wf1)
        self.header_type_combo.setVisible(is_wf1 or is_wf2)
        self.generate_pdf_check.setVisible(is_wf1 or is_wf2)

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

    def _ensure_api_server(self):
        """Start the API server if not running. Returns the API URL.
        Must be called from worker thread to avoid blocking GUI."""
        with self._api_server_lock:
            if (self._api_server_process is not None
                    and self._api_server_process.poll() is None):
                return self._api_url

            self._cleanup_api_server()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
                sock.listen(1)
                port = int(sock.getsockname()[1])

            self._api_temp_dir = tempfile.TemporaryDirectory(prefix="mineru-gui-api-")
            output_root = str(Path(self._api_temp_dir.name) / "output")
            os.makedirs(output_root, exist_ok=True)

            working_dir = str(Path(__file__).parent.parent.parent)
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["MINERU_API_OUTPUT_ROOT"] = output_root

            self._api_server_process = subprocess.Popen(
                [sys.executable, "-m", "mineru.cli.fast_api",
                 "--host", "127.0.0.1", "--port", str(port)],
                cwd=working_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True,
            )
            self._api_url = f"http://127.0.0.1:{port}"

        api_url = self._api_url
        for _ in range(300):
            if self._api_server_process.poll() is not None:
                raise RuntimeError(
                    f"API server exited with code {self._api_server_process.returncode}"
                )
            try:
                response = urlopen(f"{api_url}/health", timeout=2)
                if response.status == 200:
                    return api_url
            except (URLError, OSError):
                pass
            time.sleep(1)

        raise RuntimeError("API server failed to start within 300 seconds")

    def _cleanup_api_server(self):
        if self._api_server_process is not None:
            try:
                self._api_server_process.terminate()
                self._api_server_process.wait(timeout=5)
            except Exception:
                try:
                    self._api_server_process.kill()
                except Exception:
                    pass
            self._api_server_process = None
        if self._api_temp_dir is not None:
            try:
                self._api_temp_dir.cleanup()
            except Exception:
                pass
            self._api_temp_dir = None
        self._api_url = None

    def _stop_api_server(self):
        with self._api_server_lock:
            self._cleanup_api_server()

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
        input_error = validate_input(input_path)
        if input_error:
            QMessageBox.warning(self, "输入错误", input_error)
            return

        # Validate output
        if not output_dir:
            QMessageBox.warning(self, "输出错误", "输出目录不能为空")
            return

        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        # Disable buttons to prevent concurrent execution
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self._set_status("running")

        # Clear log
        self.log_text.clear()

        # Initialize process tracking
        self.mineru_process = None
        self._last_output_dir = output_dir

        # Create worker and thread (worker must have no parent to be movable)
        self.worker = WorkflowWorker(self)  # Pass GUI as parent reference
        self.worker_thread = QThread(self)
        self.worker.moveToThread(self.worker_thread)

        # Build workflow function before moving worker to thread
        workflow_func = self._build_workflow(input_path, output_dir)
        self.worker.workflow_func = workflow_func

        # Connect signals with explicit queued connection so the slot always
        # runs in the GUI thread, never in the worker thread.
        self.worker.log_signal.connect(self._append_log)
        self.worker.finished_signal.connect(
            self._on_workflow_finished,
            type=Qt.ConnectionType.QueuedConnection,
        )

        # Connect started signal to worker method so it runs in worker thread
        self.worker_thread.started.connect(self.worker.do_work)

        # Start thread
        self.worker_thread.start()

    def _build_workflow(self, input_path, output_dir):
        """Build selected workflow function without executing it."""
        if self.radio_wf1.isChecked():
            return self._create_workflow1(input_path, output_dir)
        elif self.radio_wf2.isChecked():
            return self._create_workflow2(input_path, output_dir)
        else:
            return self._create_workflow3(input_path, output_dir)

    def _append_log(self, message):
        """Append message to log text area (called from worker thread)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def _on_workflow_finished(self, success, message):
        """Handle workflow finished (called from worker thread)."""
        # Stop the worker thread
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(1000)
        self._enable_buttons()
        self._set_status("error" if not success else "success",
                         "失败" if not success else "完成")
        self.open_output_btn.setEnabled(success)
        if success:
            self._notify("MinerU", message)
        else:
            self._notify("MinerU", f"任务失败: {message}")

    def _set_status(self, state, text=""):
        """Update status text.

        state: idle | running | error | success
        """
        if text:
            self.status_text.setText(text)
        elif state == "idle":
            self.status_text.setText("就绪")
        elif state == "running":
            self.status_text.setText("处理中")
        elif state == "error":
            self.status_text.setText("异常")
        elif state == "success":
            self.status_text.setText("完成")

    def _create_workflow1(self, input_path, output_dir):
        """Create Workflow 1: PDF → MinerU → Translate → PDF."""
        backend = "CPU" if self.radio_cpu.isChecked() else "GPU"
        header_type = self.header_type_combo.currentText()
        generate_pdf = self.generate_pdf_check.isChecked()
        working_dir = str(Path(__file__).parent.parent.parent)

        def workflow(worker):
            worker.log("=" * 50)
            worker.log("步骤 1: MinerU 转换 PDF → Markdown")
            worker.log("=" * 50)

            try:
                api_url = self._ensure_api_server()
            except RuntimeError as e:
                worker.log(f"API 服务器启动失败: {e}")
                worker.finished_signal.emit(False, str(e))
                return

            mineru_output = os.path.join(output_dir, "mineru_output")
            os.makedirs(mineru_output, exist_ok=True)

            cmd = build_command(input_path, mineru_output, backend, api_url=api_url)

            # Run mineru with process tracking for killability
            worker.log(f"$ {' '.join(cmd)}")
            returncode = worker.run_process(cmd, working_dir)

            if returncode != 0:
                worker.log(f"MinerU 转换失败，退出码: {returncode}")
                worker.finished_signal.emit(False, "MinerU 转换失败")
                return

            # Find the generated markdown
            md_file = None
            for f in Path(mineru_output).rglob("*.md"):
                if "_content" not in f.name:
                    md_file = f
                    break

            if not md_file:
                worker.log("错误: 未找到生成的 Markdown 文件")
                worker.finished_signal.emit(False, "未找到 Markdown")
                return

            worker.log(f"找到 Markdown: {md_file}")

            # Step 2: Translate
            worker.log("")
            worker.log("=" * 50)
            worker.log("步骤 2: 翻译 Markdown")
            worker.log("=" * 50)

            try:
                from mineru.cli.llm_translate import Translator
                translator = Translator()
                translated_md = translator.translate(str(md_file))
                worker.log(f"翻译完成: {translated_md}")
            except Exception as e:
                worker.log(f"翻译错误: {e}")
                worker.finished_signal.emit(False, str(e))
                return

            # Step 3: Header correction
            if header_type != "no":
                worker.log("")
                worker.log("=" * 50)
                worker.log("步骤 3: 标题校正")
                worker.log("=" * 50)

                try:
                    from mineru.cli.llm_translate import get_corrector
                    corrector = get_corrector(header_type)
                    if corrector:
                        if header_type == "bookmark":
                            worker.log(f"使用书签校正，关联 PDF: {input_path}")
                        corrected_md = str(translated_md).replace("_trans", "_correct")
                        success = corrector.do_correct(translated_md, corrected_md)
                        if success:
                            worker.log(f"校正完成: {corrected_md}")
                            translated_md = corrected_md
                        else:
                            worker.log("校正失败，使用原始翻译文件")
                except Exception as e:
                    worker.log(f"标题校正错误: {e}")

            # Step 4: Generate PDF
            if generate_pdf:
                worker.log("")
                worker.log("=" * 50)
                worker.log("步骤 4: 生成 PDF")
                worker.log("=" * 50)

                try:
                    import platform
                    import shutil

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
                        worker.log(f"PDF 生成完成: {dest_md.with_suffix('.pdf')}")
                    else:
                        worker.log(f"PDF 生成失败: {result.stderr}")
                except Exception as e:
                    worker.log(f"PDF 生成错误: {e}")

            worker.log("")
            worker.log("=" * 50)
            worker.log("工作流 1 完成!")
            worker.log("=" * 50)
            worker.finished_signal.emit(True, "工作流 1 完成")

        return workflow

    def _create_workflow2(self, input_path, output_dir):
        """Create Workflow 2: Markdown → Translate → PDF."""
        header_type = self.header_type_combo.currentText()
        generate_pdf = self.generate_pdf_check.isChecked()

        def workflow(worker):
            nonlocal header_type
            # Find associated PDF
            pdf_path = self._find_pdf_for_markdown(input_path)
            if pdf_path:
                worker.log(f"找到关联 PDF: {pdf_path}")
            else:
                worker.log("未找到关联 PDF，标题校正将使用 LLM 方式")
                if header_type == "bookmark":
                    header_type = "by_llm"
                    worker.log(f"标题校正方式已改为: {header_type}")

            # Translate
            worker.log("")
            worker.log("=" * 50)
            worker.log("步骤 1: 翻译 Markdown")
            worker.log("=" * 50)

            try:
                from mineru.cli.llm_translate import Translator
                translator = Translator()
                translated_md = translator.translate(input_path)
                worker.log(f"翻译完成: {translated_md}")
            except Exception as e:
                worker.log(f"翻译错误: {e}")
                worker.finished_signal.emit(False, str(e))
                return

            # Header correction
            if header_type != "no":
                worker.log("")
                worker.log("=" * 50)
                worker.log("步骤 2: 标题校正")
                worker.log("=" * 50)

                try:
                    from mineru.cli.llm_translate import get_corrector
                    corrector = get_corrector(header_type)
                    if corrector:
                        corrected_md = str(translated_md).replace("_trans", "_correct")
                        success = corrector.do_correct(translated_md, corrected_md)
                        if success:
                            worker.log(f"校正完成: {corrected_md}")
                            translated_md = corrected_md
                        else:
                            worker.log("校正失败，使用原始翻译文件")
                except Exception as e:
                    worker.log(f"标题校正错误: {e}")

            # Generate PDF
            if generate_pdf:
                worker.log("")
                worker.log("=" * 50)
                worker.log("步骤 3: 生成 PDF")
                worker.log("=" * 50)

                try:
                    import platform
                    import shutil

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
                        worker.log(f"PDF 生成完成: {dest_md.with_suffix('.pdf')}")
                    else:
                        worker.log(f"PDF 生成失败: {result.stderr}")
                except Exception as e:
                    worker.log(f"PDF 生成错误: {e}")

            worker.log("")
            worker.log("=" * 50)
            worker.log("工作流 2 完成!")
            worker.log("=" * 50)
            worker.finished_signal.emit(True, "工作流 2 完成")

        return workflow

    def _create_workflow3(self, input_path, output_dir):
        """Create Workflow 3: PDF → MinerU → Markdown."""
        backend = "CPU" if self.radio_cpu.isChecked() else "GPU"
        working_dir = str(Path(__file__).parent.parent.parent)

        def workflow(worker):
            try:
                api_url = self._ensure_api_server()
            except RuntimeError as e:
                worker.log(f"API 服务器启动失败: {e}")
                worker.finished_signal.emit(False, str(e))
                return

            cmd = build_command(input_path, output_dir, backend, api_url=api_url)

            worker.log(f"$ {' '.join(cmd)}")

            returncode = worker.run_process(cmd, working_dir)

            if returncode == 0:
                worker.log("=" * 50)
                worker.log("工作流 3 完成!")
                worker.log("=" * 50)
                worker.finished_signal.emit(True, "工作流 3 完成")
            else:
                worker.log(f"工作流 3 失败，退出码: {returncode}")
                worker.finished_signal.emit(False, f"失败 (退出码: {returncode})")

        return workflow

    def _cancel(self):
        """Cancel the running process."""
        # Kill subprocess if running
        if hasattr(self, 'mineru_process') and self.mineru_process is not None:
            try:
                self.mineru_process.terminate()
                self.mineru_process.wait(timeout=5)
            except Exception:
                try:
                    self.mineru_process.kill()
                except Exception:
                    pass
            self.mineru_process = None

        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            self.worker._is_running = False
            self.worker_thread.quit()
            self.worker_thread.wait(3000)
            self.log_text.append("\n[进程已被用户停止]")
            self._set_status("idle")
            self._enable_buttons()
            self.open_output_btn.setEnabled(False)
            self._notify("MinerU", "任务已停止")

    def _enable_buttons(self):
        """Re-enable run button."""
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if self.status_text.text() == "处理中":
            self._set_status("idle")

    def _open_output_dir(self):
        """Open the last output directory in the platform file manager."""
        output_dir = getattr(self, "_last_output_dir", None)
        if not output_dir:
            return
        directory = Path(output_dir)
        if not directory.exists():
            QMessageBox.warning(self, "路径不存在", f"输出目录不存在: {directory}")
            return
        if directory.is_file():
            directory = directory.parent
        if sys.platform.startswith("linux"):
            try:
                subprocess.Popen(["xdg-open", str(directory)])
            except FileNotFoundError:
                QMessageBox.warning(self, "无法打开", "未找到 xdg-open 命令")
        elif sys.platform == "darwin":
            try:
                subprocess.Popen(["open", str(directory)])
            except FileNotFoundError:
                QMessageBox.warning(self, "无法打开", "未找到 open 命令")
        elif sys.platform == "win32":
            try:
                subprocess.Popen(["explorer", str(directory)])
            except FileNotFoundError:
                QMessageBox.warning(self, "无法打开", "未找到 explorer 命令")

    def _notify(self, title, body):
        """Send a plain desktop notification."""
        if sys.platform.startswith("linux"):
            try:
                subprocess.Popen(["notify-send", title, body])
            except FileNotFoundError:
                pass
        # Cross-platform seam: extend here for macOS / Windows adapters.

    def _close_or_cancel(self, event):
        """Shared logic for close/cancel prompt."""
        self._stop_api_server()

        # Kill subprocess if running
        if hasattr(self, 'mineru_process') and self.mineru_process is not None:
            try:
                self.mineru_process.terminate()
                self.mineru_process.wait(timeout=5)
            except Exception:
                try:
                    self.mineru_process.kill()
                except Exception:
                    pass
            self.mineru_process = None

        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "有任务正在运行，是否终止?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker._is_running = False
                self.worker_thread.quit()
                self.worker_thread.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def closeEvent(self, event):
        """Handle window close."""
        self._close_or_cancel(event)


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

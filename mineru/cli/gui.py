# Copyright (c) Opendatalab. All rights reserved.

import os
import sys
from pathlib import Path

try:
    from PyQt6.QtCore import QProcess, Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False


def build_command(input_path: str, output_dir: str, backend: str) -> list[str]:
    """Build the mineru CLI command list."""
    cmd = ["uv", "run", "mineru"]
    cmd.extend(["-p", input_path])
    cmd.extend(["-o", output_dir])
    if backend == "CPU":
        cmd.extend(["-b", "pipeline"])
    return cmd


def validate_input(path: str) -> str | None:
    """Validate input path. Returns error message or None if valid."""
    if not path or not path.strip():
        return "Input path is required."
    p = Path(path)
    if not p.exists():
        return f"Path does not exist: {path}"
    return None


_BaseWindow = QMainWindow if HAS_PYQT6 else object


class MinerUGui(_BaseWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MinerU GUI Launcher")
        self.setMinimumSize(600, 500)
        self.process = None
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Input path ---
        input_group = QGroupBox("Input Path")
        input_layout = QVBoxLayout(input_group)

        # Radio buttons for file/folder mode
        radio_layout = QHBoxLayout()
        self.radio_file = QRadioButton("File")
        self.radio_folder = QRadioButton("Folder")
        self.radio_file.setChecked(True)
        radio_layout.addWidget(self.radio_file)
        radio_layout.addWidget(self.radio_folder)
        radio_layout.addStretch()
        input_layout.addLayout(radio_layout)

        # Path input + browse button
        path_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Select input file or folder...")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_input)
        path_layout.addWidget(self.input_path_edit)
        path_layout.addWidget(self.browse_btn)
        input_layout.addLayout(path_layout)

        layout.addWidget(input_group)

        # --- Output directory ---
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout(output_group)
        default_output = str(Path.home() / "Downloads" / "mineru-output")
        self.output_dir_edit = QLineEdit(default_output)
        self.output_dir_edit.setPlaceholderText("Output directory...")
        self.output_browse_btn = QPushButton("Browse...")
        self.output_browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_browse_btn)
        layout.addWidget(output_group)

        # --- Backend selection ---
        backend_group = QGroupBox("Backend")
        backend_layout = QHBoxLayout(backend_group)
        self.radio_gpu = QRadioButton("GPU (hybrid-auto-engine)")
        self.radio_cpu = QRadioButton("CPU (pipeline)")
        self.radio_gpu.setChecked(True)
        backend_layout.addWidget(self.radio_gpu)
        backend_layout.addWidget(self.radio_cpu)
        backend_layout.addStretch()
        layout.addWidget(backend_group)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Log output ---
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group, stretch=1)

    def _browse_input(self):
        if self.radio_folder.isChecked():
            path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Input File", "",
                "PDF Files (*.pdf);;All Files (*)"
            )
        if path:
            self.input_path_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_dir_edit.setText(path)

    def _run(self):
        input_path = self.input_path_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()

        # Validate input
        error = validate_input(input_path)
        if error:
            QMessageBox.warning(self, "Invalid Input", error)
            return

        # Validate output
        if not output_dir:
            QMessageBox.warning(self, "Invalid Output", "Output directory is required.")
            return

        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        # Determine backend
        backend = "CPU" if self.radio_cpu.isChecked() else "GPU"

        # Build command
        cmd = build_command(input_path, output_dir, backend)

        # Clear log and start process
        self.log_text.clear()
        self.log_text.append(f"$ {' '.join(cmd)}\n")

        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(Path(__file__).resolve().parent.parent.parent))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_output)
        self.process.readyReadStandardError.connect(self._on_output)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)

        self.process.start(cmd[0], cmd[1:])

        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def _cancel(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.log_text.append("\n[Process cancelled by user]")

    def _on_output(self):
        if self.process:
            data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            if data:
                self.log_text.append(data.rstrip())
                # Auto-scroll to bottom
                sb = self.log_text.verticalScrollBar()
                sb.setValue(sb.maximum())

    def _on_finished(self, exit_code, exit_status):
        self.log_text.append(f"\n[Process finished with exit code {exit_code}]")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.process = None

    def _on_error(self, error):
        self.log_text.append(f"\n[Process error: {error.name}]")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.process = None

    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "A mineru process is still running. Terminate it?",
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

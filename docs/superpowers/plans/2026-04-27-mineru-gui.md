# MinerU PyQt6 GUI Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file PyQt6 desktop GUI that wraps the `mineru` CLI with GPU/CPU backend selection, real-time log output, and cancel support.

**Architecture:** One Python file (`mineru/cli/gui.py`) containing a `QMainWindow` with input path selector, output directory selector, backend radio buttons, run/cancel buttons, and a log text area. `QProcess` runs `uv run mineru` commands. Tests cover command construction and input validation logic.

**Tech Stack:** Python 3.10+, PyQt6, QProcess, Click (existing)

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `mineru/cli/gui.py` | Create | PyQt6 GUI application - all UI and logic |
| `tests/unittest/test_gui.py` | Create | Unit tests for command builder and validator |
| `pyproject.toml` | Modify | Add `gui` optional dependency and `mineru-gui` entry point |

---

### Task 1: Add PyQt6 dependency and entry point to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `gui` optional dependency**

Add after the `gradio` optional dependency block (line 108):

```toml
gui = [
    "PyQt6>=6.6.0",
]
```

- [ ] **Step 2: Add `mineru-gui` entry point**

Add after the `mineru-gradio` entry point (line 136):

```toml
mineru-gui = "mineru.cli.gui:main"
```

- [ ] **Step 3: Verify pyproject.toml is valid**

Run: `cd /home/ouyangjiahong/codes/MinerU && python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`
Expected: no output (valid TOML)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add PyQt6 optional dependency and mineru-gui entry point"
```

---

### Task 2: Write command builder and validator tests

**Files:**
- Create: `tests/unittest/test_gui.py`

- [ ] **Step 1: Create test file with command builder tests**

```python
# tests/unittest/test_gui.py
import os
import pytest
from pathlib import Path


class TestBuildCommand:
    """Tests for the build_command function."""

    def test_gpu_file_input(self):
        from mineru.cli.gui import build_command
        cmd = build_command("/path/to/file.pdf", "/output", "GPU")
        assert cmd == ["uv", "run", "mineru", "-p", "/path/to/file.pdf", "-o", "/output"]

    def test_cpu_file_input(self):
        from mineru.cli.gui import build_command
        cmd = build_command("/path/to/file.pdf", "/output", "CPU")
        assert cmd == ["uv", "run", "mineru", "-p", "/path/to/file.pdf", "-o", "/output", "-b", "pipeline"]

    def test_gpu_folder_input(self):
        from mineru.cli.gui import build_command
        cmd = build_command("/path/to/folder/", "/output", "GPU")
        assert cmd == ["uv", "run", "mineru", "-p", "/path/to/folder/", "-o", "/output"]

    def test_cpu_folder_input(self):
        from mineru.cli.gui import build_command
        cmd = build_command("/path/to/folder/", "/output", "CPU")
        assert cmd == ["uv", "run", "mineru", "-p", "/path/to/folder/", "-o", "/output", "-b", "pipeline"]


class TestValidateInput:
    """Tests for the validate_input function."""

    def test_valid_file_path(self, tmp_path):
        from mineru.cli.gui import validate_input
        f = tmp_path / "test.pdf"
        f.touch()
        assert validate_input(str(f)) is None

    def test_valid_folder_path(self, tmp_path):
        from mineru.cli.gui import validate_input
        assert validate_input(str(tmp_path)) is None

    def test_empty_path(self):
        from mineru.cli.gui import validate_input
        error = validate_input("")
        assert error is not None
        assert "empty" in error.lower() or "required" in error.lower()

    def test_nonexistent_path(self):
        from mineru.cli.gui import validate_input
        error = validate_input("/nonexistent/path/that/does/not/exist")
        assert error is not None
        assert "not exist" in error.lower() or "found" in error.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ouyangjiahong/codes/MinerU && python -m pytest tests/unittest/test_gui.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mineru.cli.gui'`

- [ ] **Step 3: Commit**

```bash
git add tests/unittest/test_gui.py
git commit -m "test: add GUI command builder and validator tests"
```

---

### Task 3: Implement build_command and validate_input

**Files:**
- Create: `mineru/cli/gui.py`

- [ ] **Step 1: Create gui.py with command builder and validator**

```python
# Copyright (c) Opendatalab. All rights reserved.

import os
import sys
from pathlib import Path


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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /home/ouyangjiahong/codes/MinerU && python -m pytest tests/unittest/test_gui.py -v`
Expected: all 8 tests PASS

- [ ] **Step 3: Commit**

```bash
git add mineru/cli/gui.py
git commit -m "feat: add build_command and validate_input for GUI"
```

---

### Task 4: Implement the PyQt6 GUI class

**Files:**
- Modify: `mineru/cli/gui.py`

- [ ] **Step 1: Add the full GUI implementation**

Replace the contents of `mineru/cli/gui.py` with:

```python
# Copyright (c) Opendatalab. All rights reserved.

import os
import sys
from pathlib import Path

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


class MinerUGui(QMainWindow):
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
```

- [ ] **Step 2: Run unit tests to verify they still pass**

Run: `cd /home/ouyangjiahong/codes/MinerU && python -m pytest tests/unittest/test_gui.py -v`
Expected: all 8 tests PASS

- [ ] **Step 3: Commit**

```bash
git add mineru/cli/gui.py
git commit -m "feat: implement PyQt6 GUI for mineru CLI launcher"
```

---

### Task 5: Manual smoke test

**Files:**
- None (manual verification)

- [ ] **Step 1: Install PyQt6 and launch the GUI**

Run: `cd /home/ouyangjiahong/codes/MinerU && uv pip install PyQt6 && uv run python mineru/cli/gui.py`

Expected: A window appears with the MinerU GUI layout. Verify:
- Radio buttons for File/Folder toggle correctly
- Browse button opens file dialog (file mode) or folder dialog (folder mode)
- Output directory defaults to `~/Downloads/mineru-output`
- GPU/CPU radio buttons work
- Run button is enabled, Cancel is disabled initially
- Clicking Run with an empty input shows a warning dialog

- [ ] **Step 2: Test a real command (optional, requires mineru setup)**

If mineru is configured, try running with a sample PDF to verify:
- Log area shows the command being run
- stdout/stderr appears in real-time
- Cancel button terminates the process
- Exit code is shown when finished

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address issues found during smoke test"
```

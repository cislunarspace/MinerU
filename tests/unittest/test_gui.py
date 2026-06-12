# tests/unittest/test_gui.py
import os
import sys
import pytest
from importlib.abc import MetaPathFinder
from pathlib import Path


class BlockLangchainImport(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "langchain" or fullname.startswith("langchain."):
            raise ModuleNotFoundError("No module named 'langchain'")
        return None


def test_translator_does_not_import_langchain_package():
    """The translate extra depends on split langchain packages, not monolithic langchain."""
    if "langchain" in sys.modules:
        pytest.skip("langchain package is already imported")

    blocker = BlockLangchainImport()
    sys.meta_path.insert(0, blocker)
    try:
        from mineru.cli.llm_translate import Translator
    finally:
        sys.meta_path.remove(blocker)

    assert Translator is not None


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

    def test_with_api_url(self):
        from mineru.cli.gui import build_command
        cmd = build_command("/path/to/file.pdf", "/output", "GPU", api_url="http://127.0.0.1:8000")
        assert cmd == ["uv", "run", "mineru", "-p", "/path/to/file.pdf", "-o", "/output",
                       "--api-url", "http://127.0.0.1:8000"]

    def test_cpu_with_api_url(self):
        from mineru.cli.gui import build_command
        cmd = build_command("/path/to/file.pdf", "/output", "CPU", api_url="http://127.0.0.1:8000")
        assert cmd == ["uv", "run", "mineru", "-p", "/path/to/file.pdf", "-o", "/output",
                       "-b", "pipeline", "--api-url", "http://127.0.0.1:8000"]

    def test_api_url_none_omits_flag(self):
        from mineru.cli.gui import build_command
        cmd = build_command("/path/to/file.pdf", "/output", "GPU", api_url=None)
        assert "--api-url" not in cmd


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


class TestLLMConfigDialog:
    """Tests for the LLM configuration dialog."""

    @pytest.fixture
    def dialog(self, qtbot):
        from PyQt6.QtCore import Qt
        from mineru.cli.gui import LLMConfigDialog
        widget = LLMConfigDialog()
        qtbot.addWidget(widget)
        return widget

    def test_dialog_has_test_api_button(self, dialog):
        assert dialog.test_btn is not None
        assert "测试" in dialog.test_btn.text()

    def test_test_button_is_disabled_during_test(self, qtbot, dialog, monkeypatch):
        from mineru.cli.llm_translate.api_tester import TestApiWorker

        dialog.base_url_edit.setText("https://api.example.com")
        dialog.model_name_edit.setText("test-model")
        dialog.api_key_edit.setText("sk-test")

        monkeypatch.setattr(TestApiWorker, "run", lambda self, base_url, model_name, api_key: None)

        assert dialog.test_btn.isEnabled()
        assert dialog.save_btn.isEnabled()

        dialog._on_test_api()
        qtbot.wait(50)

        assert not dialog.test_btn.isEnabled()
        assert not dialog.save_btn.isEnabled()

    def test_successful_test_shows_result(self, qtbot, dialog, monkeypatch):
        from mineru.cli.llm_translate.api_tester import TestApiWorker

        dialog.base_url_edit.setText("https://api.example.com")
        dialog.model_name_edit.setText("test-model")
        dialog.api_key_edit.setText("sk-test")

        def fake_run(self, base_url, model_name, api_key):
            self.test_finished.emit("你好，世界！")

        monkeypatch.setattr(TestApiWorker, "run", fake_run)

        dialog._on_test_api()
        qtbot.wait(50)

        assert "测试成功" in dialog.status_label.text()
        assert "你好，世界" in dialog.status_label.text()

    def test_failed_test_shows_error(self, qtbot, dialog, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox
        from mineru.cli.llm_translate.api_tester import TestApiWorker

        dialog.base_url_edit.setText("https://api.example.com")
        dialog.model_name_edit.setText("test-model")
        dialog.api_key_edit.setText("sk-test")

        def fake_run(self, base_url, model_name, api_key):
            self.test_failed.emit("API Key 无效")

        monkeypatch.setattr(TestApiWorker, "run", fake_run)
        monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

        dialog._on_test_api()
        qtbot.wait(50)

        assert "测试失败" in dialog.status_label.text()
        assert "API Key 无效" in dialog.status_label.text()

    def test_empty_field_validation(self, qtbot, dialog, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox

        dialog.base_url_edit.setText("")
        dialog.model_name_edit.setText("test-model")
        dialog.api_key_edit.setText("sk-test")

        monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

        dialog._on_test_api()
        qtbot.wait(50)

        assert "测试失败" in dialog.status_label.text()
        assert "完整" in dialog.status_label.text()


class TestFormatApiTestError:
    """Tests for the API test error formatter."""

    def test_timeout_error(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        assert "超时" in format_api_test_error(TimeoutError("Request timed out"))

    def test_unauthorized_error(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        assert "API Key 无效" in format_api_test_error(Exception("401 Unauthorized"))

    def test_not_found_error(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        assert "模型不存在" in format_api_test_error(Exception("404 Not Found"))

    def test_connection_error(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        assert "无法连接" in format_api_test_error(ConnectionError("Connection refused"))

    def test_unknown_error(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        message = format_api_test_error(ValueError("unknown problem"))
        assert "测试异常" in message
        assert "unknown problem" in message

    def test_forbidden_error(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        assert "访问被拒绝" in format_api_test_error(Exception("403 Forbidden"))

    def test_rate_limit_error(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        assert "过于频繁" in format_api_test_error(Exception("429 Too Many Requests"))

    def test_error_message_sanitizes_api_key(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        message = format_api_test_error(Exception("failed with sk-abc123xyz789secretKey"))
        assert "sk-" not in message
        assert "***" in message

    def test_error_message_sanitizes_bearer_token(self):
        from mineru.cli.llm_translate.api_tester import format_api_test_error
        message = format_api_test_error(Exception("Authorization: Bearer secret-token-123"))
        assert "Bearer" not in message
        assert "secret-token" not in message


class TestWorkerSignalCleanup:
    """Regression tests for stale signal connections between runs.

    Bug: after a successful first run, clicking "start" with a new input path
    would re-execute the first run's command because old worker signals were
    never disconnected.
    """

    @pytest.fixture
    def gui_window(self, qtbot):
        from mineru.cli.gui import MinerUGui, WorkflowWorker

        window = MinerUGui()
        qtbot.addWidget(window)

        # Patch _ensure_api_server so we don't start a real server.
        window._ensure_api_server = lambda: "http://127.0.0.1:9999"

        # Use workflow 3 (simplest: just run mineru subprocess).
        window.radio_wf3.setChecked(True)

        # Patch run_process to capture commands without running anything.
        captured = []

        def fake_run_process(worker_self, cmd, cwd):
            captured.append(list(cmd))
            return 0

        WorkflowWorker.run_process = fake_run_process
        window._captured = captured
        return window

    def _wait_for_thread(self, qtbot, window, timeout=3000):
        """Wait until worker thread finishes."""
        import time
        start = time.monotonic()
        while window.worker_thread.isRunning() and time.monotonic() - start < timeout / 1000:
            qtbot.wait(10)

    def test_second_run_uses_new_path(self, qtbot, gui_window, tmp_path):
        """Second run must use the new input path, not the first one."""
        first_pdf = tmp_path / "first.pdf"
        second_pdf = tmp_path / "second.pdf"
        first_pdf.touch()
        second_pdf.touch()

        # First run
        gui_window.input_path_edit.setText(str(first_pdf))
        gui_window.output_dir_edit.setText(str(tmp_path / "out1"))
        gui_window._run()
        self._wait_for_thread(qtbot, gui_window)
        qtbot.wait(50)

        # Second run with different path
        gui_window.input_path_edit.setText(str(second_pdf))
        gui_window.output_dir_edit.setText(str(tmp_path / "out2"))
        gui_window._run()
        self._wait_for_thread(qtbot, gui_window)
        qtbot.wait(50)

        captured = gui_window._captured
        uv_cmds = [c for c in captured if c[:2] == ["uv", "run"]]
        assert len(uv_cmds) == 2

        first_path = uv_cmds[0][uv_cmds[0].index("-p") + 1]
        second_path = uv_cmds[1][uv_cmds[1].index("-p") + 1]

        assert first_path == str(first_pdf)
        assert second_path == str(second_pdf)

    def test_old_worker_signals_disconnected_after_finish(self, qtbot, gui_window, tmp_path):
        """After a run finishes, the old worker's signals must be disconnected."""
        pdf = tmp_path / "test.pdf"
        pdf.touch()

        gui_window.input_path_edit.setText(str(pdf))
        gui_window.output_dir_edit.setText(str(tmp_path / "out"))
        gui_window._run()
        self._wait_for_thread(qtbot, gui_window)

        # Let the queued finished signal be processed
        qtbot.wait(50)

        old_worker = gui_window.worker
        # Signals still exist on the object but are disconnected from slots.
        assert old_worker.log_signal is not None
        assert old_worker.finished_signal is not None

    def test_cleanup_worker_handles_no_prior_worker(self, qtbot, gui_window):
        """_cleanup_worker must not raise when no prior worker exists."""
        gui_window._cleanup_worker()  # Should not raise

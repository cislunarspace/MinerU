# tests/unittest/test_gui_failure_handling.py
"""End-to-end failure-path coverage for the GUI workflows.

These tests drive the real MinerUGui (offscreen Qt) and patch
WorkflowWorker.run_process so we can simulate mineru CLI failure
scenarios without spawning a real subprocess.
"""
import json
import os
import pathlib
import sys
import tempfile
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def gui_app():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture
def gui_window(gui_app, monkeypatch, tmp_path):
    from mineru.cli.gui import MinerUGui, WorkflowWorker

    win = MinerUGui()
    monkeypatch.setattr(win, "_ensure_api_server", lambda: "http://127.0.0.1:9999")
    win.radio_wf3.setChecked(True)

    monkeypatch.setattr(win, "_make_failure_report_path", lambda: tmp_path / "report.json")

    # Pre-create the file the fake run_process will write into. This lets
    # _resolve_failure_message find it and shape the finished message.
    tmp_path.joinpath("report.json").write_text(
        json.dumps(
            {
                "failures": [
                    {"task_index": 1, "documents": ["bad_scan"], "message": "invalid xref"},
                    {"task_index": 2, "documents": ["paper_x"], "message": "timeout"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    yield win


def _wait_for_finish(win, gui_app, timeout_s=8):
    deadline = time.monotonic() + timeout_s
    while win.worker_thread.isRunning() and time.monotonic() < deadline:
        gui_app.processEvents()
    gui_app.processEvents()
    time.sleep(0.05)
    gui_app.processEvents()


def _patch_run_process(monkeypatch, returncode, side_effect=None):
    from mineru.cli.gui import WorkflowWorker

    def fake(self, cmd, cwd):
        if side_effect is not None:
            side_effect()
        return returncode

    monkeypatch.setattr(WorkflowWorker, "run_process", fake)


def _drive_run(win, gui_app, monkeypatch, input_path, output_dir):
    win.input_path_edit.setText(str(input_path))
    win.output_dir_edit.setText(str(output_dir))
    win._run()
    _wait_for_finish(win, gui_app)


def _capture_finished(win):
    captured = {}

    def hook(success, message):
        captured["value"] = (success, message)

    orig = win._on_workflow_finished
    def cap_finished(success, message):
        captured["value"] = (success, message)
        orig(success, message)
    win._on_workflow_finished = cap_finished
    return captured


class TestWorkflow3FailurePath:
    def test_task_level_failure_carries_document_names(self, gui_window, gui_app, monkeypatch, tmp_path):
        _patch_run_process(monkeypatch, returncode=1)
        captured = _capture_finished(gui_window)

        in_dir = tmp_path / "in"; in_dir.mkdir()
        (in_dir / "a.pdf").write_bytes(b"%PDF-1.4")
        out_dir = tmp_path / "out"
        _drive_run(gui_window, gui_app, monkeypatch, in_dir, out_dir)

        assert captured["value"][0] is False
        message = captured["value"][1]
        assert "bad_scan" in message
        assert "paper_x" in message or "2" in message

    def test_run_btn_re_enabled_after_failure(self, gui_window, gui_app, monkeypatch, tmp_path):
        _patch_run_process(monkeypatch, returncode=1)
        _capture_finished(gui_window)

        in_dir = tmp_path / "in"; in_dir.mkdir()
        (in_dir / "a.pdf").write_bytes(b"%PDF-1.4")
        out_dir = tmp_path / "out"
        _drive_run(gui_window, gui_app, monkeypatch, in_dir, out_dir)

        assert gui_window.run_btn.isEnabled() is True
        assert gui_window.cancel_btn.isEnabled() is False

    def test_open_output_btn_disabled_after_failure(self, gui_window, gui_app, monkeypatch, tmp_path):
        _patch_run_process(monkeypatch, returncode=1)
        _capture_finished(gui_window)

        in_dir = tmp_path / "in"; in_dir.mkdir()
        (in_dir / "a.pdf").write_bytes(b"%PDF-1.4")
        out_dir = tmp_path / "out"
        _drive_run(gui_window, gui_app, monkeypatch, in_dir, out_dir)

        assert gui_window.open_output_btn.isEnabled() is False

    def test_retry_after_failure_executes_second_run(self, gui_window, gui_app, monkeypatch, tmp_path):
        # First run fails, second run succeeds.
        run_count = {"n": 0}

        def fake(self, cmd, cwd):
            run_count["n"] += 1
            if run_count["n"] == 1:
                # simulate failure: leave a failure report, return 1
                return 1
            # simulate success: overwrite report with empty list, return 0
            pathlib.Path(cmd[cmd.index("--failure-report-path") + 1]).write_text(
                json.dumps({"failures": []}), encoding="utf-8"
            )
            return 0

        monkeypatch.setattr("mineru.cli.gui.WorkflowWorker.run_process", fake)
        captured = _capture_finished(gui_window)

        in_dir = tmp_path / "in"; in_dir.mkdir()
        (in_dir / "a.pdf").write_bytes(b"%PDF-1.4")
        out_dir = tmp_path / "out"

        # First run (failure)
        gui_window.input_path_edit.setText(str(in_dir))
        gui_window.output_dir_edit.setText(str(out_dir))
        gui_window._run()
        _wait_for_finish(gui_window, gui_app)
        assert captured["value"][0] is False

        # Second run (retry, success)
        gui_window._run()
        _wait_for_finish(gui_window, gui_app)
        assert captured["value"][0] is True
        assert run_count["n"] == 2

    def test_exception_in_run_process_is_handled(self, gui_window, gui_app, monkeypatch, tmp_path):
        from mineru.cli.gui import WorkflowWorker

        def boom(self, cmd, cwd):
            raise RuntimeError("mineru crashed unexpectedly")

        monkeypatch.setattr(WorkflowWorker, "run_process", boom)
        captured = _capture_finished(gui_window)

        in_dir = tmp_path / "in"; in_dir.mkdir()
        (in_dir / "a.pdf").write_bytes(b"%PDF-1.4")
        out_dir = tmp_path / "out"
        _drive_run(gui_window, gui_app, monkeypatch, in_dir, out_dir)

        assert captured["value"][0] is False
        assert "mineru crashed unexpectedly" in captured["value"][1]
        assert gui_window.run_btn.isEnabled() is True

    def test_failure_report_temp_file_cleaned_up(self, gui_window, gui_app, monkeypatch, tmp_path):
        _patch_run_process(monkeypatch, returncode=1)
        _capture_finished(gui_window)

        in_dir = tmp_path / "in"; in_dir.mkdir()
        (in_dir / "a.pdf").write_bytes(b"%PDF-1.4")
        out_dir = tmp_path / "out"

        report_path = gui_window._make_failure_report_path()
        report_path.write_text(json.dumps({"failures": []}), encoding="utf-8")
        gui_window._make_failure_report_path = lambda: report_path

        _drive_run(gui_window, gui_app, monkeypatch, in_dir, out_dir)

        assert not report_path.exists()

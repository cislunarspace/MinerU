# tests/unittest/test_failure_report.py
import json
from pathlib import Path

import pytest

from mineru.cli.client import TaskFailure, write_failure_report


class TestWriteFailureReport:
    def test_writes_failures_sorted_by_task_index(self, tmp_path):
        report_path = tmp_path / "failure_report.json"
        failures = [
            TaskFailure(task_index=3, document_stems=("third",), message="err 3"),
            TaskFailure(task_index=1, document_stems=("first",), message="err 1"),
        ]

        write_failure_report(failures, report_path)

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        assert [item["task_index"] for item in payload["failures"]] == [1, 3]
        assert payload["failures"][0]["documents"] == ["first"]
        assert payload["failures"][0]["message"] == "err 1"

    def test_creates_parent_directory(self, tmp_path):
        report_path = tmp_path / "nested" / "dir" / "report.json"

        write_failure_report([], report_path)

        assert report_path.exists()
        assert json.loads(report_path.read_text(encoding="utf-8")) == {"failures": []}

    def test_empty_failures_writes_empty_array(self, tmp_path):
        report_path = tmp_path / "empty.json"

        write_failure_report([], report_path)

        assert json.loads(report_path.read_text(encoding="utf-8")) == {"failures": []}

    def test_does_not_include_traceback_or_env_fields(self, tmp_path):
        report_path = tmp_path / "report.json"
        failures = [
            TaskFailure(task_index=1, document_stems=("a",), message="boom"),
        ]

        write_failure_report(failures, report_path)

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        assert set(payload["failures"][0].keys()) == {
            "task_index",
            "documents",
            "message",
        }

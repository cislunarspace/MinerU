# tests/unittest/test_failure_report_gui.py
import json
from pathlib import Path

from mineru.cli.gui import (
    build_command,
    format_failure_details,
    format_failure_summary,
    load_failure_report,
)


class TestBuildCommandWithFailureReport:
    def test_failure_report_path_omitted_when_none(self):
        cmd = build_command("/in.pdf", "/out", "GPU", api_url="http://x")
        assert "--failure-report-path" not in cmd

    def test_failure_report_path_appended(self):
        cmd = build_command(
            "/in.pdf", "/out", "GPU",
            api_url="http://x", failure_report_path="/tmp/r.json",
        )
        assert "--failure-report-path" in cmd
        assert cmd[cmd.index("--failure-report-path") + 1] == "/tmp/r.json"


class TestLoadFailureReport:
    def test_missing_file_returns_none(self, tmp_path):
        assert load_failure_report(tmp_path / "nope.json") is None

    def test_none_path_returns_none(self):
        assert load_failure_report(None) is None

    def test_malformed_json_returns_none(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        assert load_failure_report(p) is None

    def test_wrong_shape_returns_none(self, tmp_path):
        p = tmp_path / "wrong.json"
        p.write_text(json.dumps({"oops": 1}), encoding="utf-8")
        assert load_failure_report(p) is None

    def test_valid_report_returns_failures_list(self, tmp_path):
        p = tmp_path / "ok.json"
        p.write_text(
            json.dumps({"failures": [{"task_index": 1, "documents": ["a"], "message": "m"}]}),
            encoding="utf-8",
        )
        result = load_failure_report(p)
        assert result is not None
        assert result[0]["documents"] == ["a"]


class TestFormatFailureSummary:
    def test_empty_failures_returns_fallback(self):
        assert format_failure_summary([]) == "失败"
        assert format_failure_summary(None) == "失败"

    def test_single_failure_names_document(self):
        assert format_failure_summary(
            [{"task_index": 1, "documents": ["bad"], "message": "x"}]
        ) == "失败：bad 处理失败"

    def test_multiple_failures_names_first_and_count(self):
        failures = [
            {"task_index": 1, "documents": ["bad"], "message": "x"},
            {"task_index": 2, "documents": ["other"], "message": "y"},
        ]
        assert format_failure_summary(failures) == "失败：bad 等 2 个文件处理失败"


class TestFormatFailureDetails:
    def test_empty_returns_empty_list(self):
        assert format_failure_details([]) == []

    def test_single_failure_one_line(self):
        lines = format_failure_details(
            [{"task_index": 1, "documents": ["a"], "message": "boom"}]
        )
        assert lines == ["失败详情：", "- a: boom"]

    def test_multi_document_failure_expands(self):
        lines = format_failure_details(
            [{"task_index": 1, "documents": ["a", "b"], "message": "m"}]
        )
        assert lines == ["失败详情：", "- a: m", "- b: m"]

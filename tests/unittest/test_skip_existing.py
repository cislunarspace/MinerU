# tests/unittest/test_skip_existing.py
from pathlib import Path

import pytest

from mineru.cli.client import InputDocument, should_skip_document


def _doc(stem="a", suffix="pdf", order=0, effective_pages=1):
    return InputDocument(
        path=Path(f"/tmp/{stem}.{suffix}"),
        suffix=suffix,
        stem=stem,
        effective_pages=effective_pages,
        order=order,
    )


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "out"


class TestShouldSkipDocument:
    def test_no_output_returns_false(self, output_dir):
        doc = _doc(stem="a")
        assert should_skip_document(doc, output_dir, backend="pipeline", parse_method="auto") is False

    def test_pipeline_output_exists_returns_true(self, output_dir):
        doc = _doc(stem="a")
        parse_dir = output_dir / "a" / "auto"
        parse_dir.mkdir(parents=True)
        (parse_dir / "a.md").write_text("hello", encoding="utf-8")
        assert should_skip_document(doc, output_dir, backend="pipeline", parse_method="auto") is True

    def test_vlm_output_exists_returns_true(self, output_dir):
        doc = _doc(stem="a")
        parse_dir = output_dir / "a" / "vlm"
        parse_dir.mkdir(parents=True)
        (parse_dir / "a.md").write_text("hello", encoding="utf-8")
        assert should_skip_document(doc, output_dir, backend="vlm-auto-engine", parse_method="auto") is True

    def test_hybrid_output_exists_returns_true(self, output_dir):
        doc = _doc(stem="a")
        parse_dir = output_dir / "a" / "hybrid_auto"
        parse_dir.mkdir(parents=True)
        (parse_dir / "a.md").write_text("hello", encoding="utf-8")
        assert should_skip_document(doc, output_dir, backend="hybrid-auto-engine", parse_method="auto") is True

    def test_office_doc_uses_office_dir(self, output_dir):
        doc = _doc(stem="a", suffix="docx")
        parse_dir = output_dir / "a" / "office"
        parse_dir.mkdir(parents=True)
        (parse_dir / "a.md").write_text("hello", encoding="utf-8")
        assert should_skip_document(doc, output_dir, backend="pipeline", parse_method="auto") is True

    def test_middle_json_alone_does_not_count(self, output_dir):
        doc = _doc(stem="a")
        parse_dir = output_dir / "a" / "auto"
        parse_dir.mkdir(parents=True)
        (parse_dir / "a_middle.json").write_text("{}", encoding="utf-8")
        assert should_skip_document(doc, output_dir, backend="pipeline", parse_method="auto") is False

    def test_content_list_does_not_count(self, output_dir):
        doc = _doc(stem="a")
        parse_dir = output_dir / "a" / "auto"
        parse_dir.mkdir(parents=True)
        (parse_dir / "a_content_list.json").write_text("[]", encoding="utf-8")
        assert should_skip_document(doc, output_dir, backend="pipeline", parse_method="auto") is False

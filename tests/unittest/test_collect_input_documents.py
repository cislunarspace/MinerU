# tests/unittest/test_collect_input_documents.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCollectInputDocuments:
    """Tests for the collect_input_documents function."""

    @pytest.fixture(autouse=True)
    def mock_functions(self):
        """Mock functions that require actual file content."""
        with patch("mineru.cli.client.probe_pdf_effective_pages", return_value=1) as mock_probe:
            with patch("mineru.cli.client.guess_suffix_by_path") as mock_guess:
                # Return 'pdf' for any .pdf file, 'docx' for .docx, etc.
                def guess_side_effect(path):
                    suffix = path.suffix.lower()
                    if suffix == ".pdf":
                        return "pdf"
                    elif suffix == ".docx":
                        return "docx"
                    elif suffix == ".pptx":
                        return "pptx"
                    elif suffix == ".xlsx":
                        return "xlsx"
                    elif suffix == ".png":
                        return "png"
                    elif suffix == ".jpg":
                        return "jpg"
                    return suffix.lstrip(".")

                mock_guess.side_effect = guess_side_effect
                yield mock_probe, mock_guess

    def test_recursive_scanning_top_level_pdf(self, tmp_path):
        """Test that PDFs in the top-level directory are collected."""
        from mineru.cli.client import collect_input_documents

        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 1
        assert result[0].path.name == "test.pdf"

    def test_recursive_scanning_nested_pdf(self, tmp_path):
        """Test that PDFs in subdirectories are collected."""
        from mineru.cli.client import collect_input_documents

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        pdf_file = subdir / "nested.pdf"
        pdf_file.touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 1
        assert result[0].path.name == "nested.pdf"

    def test_recursive_scanning_deep_nested_pdf(self, tmp_path):
        """Test that PDFs in deeply nested directories are collected."""
        from mineru.cli.client import collect_input_documents

        deep_dir = tmp_path / "a" / "b" / "c"
        deep_dir.mkdir(parents=True)
        pdf_file = deep_dir / "deep.pdf"
        pdf_file.touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 1
        assert result[0].path.name == "deep.pdf"

    def test_recursive_scanning_multiple_pdfs(self, tmp_path):
        """Test that multiple PDFs from different directories are collected."""
        from mineru.cli.client import collect_input_documents

        subdir1 = tmp_path / "dir1"
        subdir2 = tmp_path / "dir2"
        subdir1.mkdir()
        subdir2.mkdir()

        (subdir1 / "file1.pdf").touch()
        (subdir2 / "file2.pdf").touch()
        (tmp_path / "file0.pdf").touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 3
        names = [r.path.name for r in result]
        assert "file0.pdf" in names
        assert "file1.pdf" in names
        assert "file2.pdf" in names

    def test_recursive_scanning_case_insensitive_suffix(self, tmp_path):
        """Test that PDF files with mixed case suffixes are collected."""
        from mineru.cli.client import collect_input_documents

        (tmp_path / "lower.pdf").touch()
        (tmp_path / "UPPER.PDF").touch()
        (tmp_path / "Mixed.Pdf").touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 3

    def test_recursive_scanning_excludes_non_pdf_files(self, tmp_path):
        """Test that non-PDF files are excluded."""
        from mineru.cli.client import collect_input_documents

        (tmp_path / "test.pdf").touch()
        (tmp_path / "test.jpg").touch()
        (tmp_path / "test.docx").touch()
        (tmp_path / "test.txt").touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 1
        assert result[0].path.suffix.lower() == ".pdf"

    def test_recursive_scanning_includes_hidden_directories(self, tmp_path):
        """Test that PDFs in hidden directories (starting with .) are collected."""
        from mineru.cli.client import collect_input_documents

        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "hidden.pdf").touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 1
        assert result[0].path.name == "hidden.pdf"

    def test_recursive_scanning_sorts_by_path(self, tmp_path):
        """Test that PDFs are sorted by their full path."""
        from mineru.cli.client import collect_input_documents

        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        (dir_b / "x.pdf").touch()
        (dir_a / "y.pdf").touch()

        result = collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

        assert len(result) == 2
        # a/y.pdf should come before b/x.pdf
        assert result[0].path.stem == "y"
        assert result[1].path.stem == "x"

    def test_recursive_scanning_empty_directory(self, tmp_path):
        """Test that empty directories raise an error."""
        from mineru.cli.client import collect_input_documents

        with pytest.raises(Exception):
            collect_input_documents(tmp_path, start_page_id=0, end_page_id=None)

    def test_single_file_input(self, tmp_path):
        """Test that single file input works correctly."""
        from mineru.cli.client import collect_input_documents

        pdf_file = tmp_path / "single.pdf"
        pdf_file.touch()

        result = collect_input_documents(pdf_file, start_page_id=0, end_page_id=None)

        assert len(result) == 1
        assert result[0].path == pdf_file


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

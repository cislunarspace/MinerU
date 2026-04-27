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

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

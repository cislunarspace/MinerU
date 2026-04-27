# MinerU PyQt6 GUI Launcher - Design Spec

## Overview

A single-file PyQt6 desktop GUI that wraps the `mineru` CLI tool, providing a simple interface for running PDF/document parsing with GPU or CPU backends.

## Requirements

- **4 command combinations**: file/folder input × GPU/CPU backend
- **Real-time log output**: stdout/stderr displayed in the GUI
- **Cancel support**: kill running mineru process
- **Configurable paths**: input file/folder and output directory via browse buttons
- **Backend selection**: GPU (`hybrid-auto-engine`, default) or CPU (`pipeline`)

## UI Layout

```
┌─────────────────────────────────────────────┐
│  MinerU GUI Launcher                        │
├─────────────────────────────────────────────┤
│  输入路径:  [○ 文件  ○ 文件夹]               │
│  [/path/to/input................] [浏览...]  │
│                                             │
│  输出目录:  [~/Downloads/mineru-output/...]  │
│  [................................] [浏览...] │
│                                             │
│  后端:      [GPU (hybrid-auto-engine)]       │
│             [CPU (pipeline)         ]        │
│                                             │
│  [▶ 运行]  [■ 取消]                         │
│                                             │
│  ─────────── 日志输出 ───────────            │
│  [stdout/stderr 实时显示区域]                │
└─────────────────────────────────────────────┘
```

## Command Construction

```python
cmd = ["uv", "run", "mineru"]
cmd.extend(["-p", input_path])
cmd.extend(["-o", output_dir])
if backend == "CPU":
    cmd.extend(["-b", "pipeline"])
# GPU uses default (hybrid-auto-engine), no -b flag needed
```

## Execution

- Use `QProcess` for native Qt event loop integration
- Signals: `readyReadStandardOutput`, `readyReadStandardError`, `finished`, `errorOccurred`
- State machine: `idle` → `running` → `idle`/`error`
- Working directory: set QProcess working directory to the MinerU project root (where `pyproject.toml` lives) so `uv run mineru` resolves correctly

## File Location

- **GUI code**: `mineru/cli/gui.py`
- **Entry point**: `mineru-gui = "mineru.cli.gui:main"` in `pyproject.toml`
- **Optional dependency**: `PyQt6>=6.6.0` under `[project.optional-dependencies] gui`

## Error Handling

1. Input path validation before running
2. Auto-create output directory if missing
3. Friendly error if PyQt6 not installed
4. Process error handling via `errorOccurred` signal
5. Confirm on window close if process running
6. Auto-scroll log area on new output

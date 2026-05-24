#!/bin/bash
cd /home/ouyangjiahong/codes/MinerU
exec env QT_QPA_PLATFORM=xcb /home/ouyangjiahong/.local/bin/uv run python mineru/cli/gui.py

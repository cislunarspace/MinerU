# Copyright (c) Opendatalab. All rights reserved.
"""Industrial console QSS and visual assets for MinerU GUI."""

import sys


def application_font() -> str:
    """Return a reasonable monospace/system font family string."""
    if sys.platform == "darwin":
        return "SF Mono, Menlo, Monaco, monospace"
    if sys.platform == "win32":
        return "Consolas, 'Microsoft YaHei', monospace"
    return "'JetBrains Mono', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', monospace"


def sans_font() -> str:
    """Return a reasonable sans-serif/system font family string."""
    if sys.platform == "darwin":
        return "-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif"
    if sys.platform == "win32":
        return "'Segoe UI', 'Microsoft YaHei', sans-serif"
    return "'Inter', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', sans-serif"


STATUS_LED_STYLE = """
QLabel#statusLed {
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
    border-radius: 5px;
    background-color: #2a2a2a;
    border: 1px solid #1a1a1a;
}
QLabel#statusLed[state="idle"] {
    background-color: #2a2a2a;
}
QLabel#statusLed[state="running"] {
    background-color: #00e676;
    box-shadow: 0 0 8px #00e676;
}
QLabel#statusLed[state="error"] {
    background-color: #ff1744;
    box-shadow: 0 0 8px #ff1744;
}
QLabel#statusLed[state="success"] {
    background-color: #00b0ff;
}
"""


def console_stylesheet() -> str:
    """Industrial dark console QSS for PyQt6."""
    mono = application_font()
    sans = sans_font()

    return f"""
    QMainWindow {{
        background-color: #121212;
    }}

    QWidget {{
        font-family: {sans};
        color: #e0e0e0;
    }}

    QGroupBox {{
        font-family: {sans};
        font-size: 12px;
        font-weight: 600;
        color: #9e9e9e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
        padding-left: 12px;
        padding-right: 12px;
        padding-bottom: 12px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        top: -8px;
        background-color: #121212;
        padding: 0 6px;
    }}

    QRadioButton, QCheckBox {{
        font-family: {sans};
        font-size: 13px;
        color: #e0e0e0;
        spacing: 8px;
    }}

    QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 7px;
        border: 2px solid #555;
        background-color: #1a1a1a;
    }}

    QRadioButton::indicator:checked {{
        background-color: #00e676;
        border: 2px solid #00e676;
    }}

    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 2px;
        border: 2px solid #555;
        background-color: #1a1a1a;
    }}

    QCheckBox::indicator:checked {{
        background-color: #00e676;
        border: 2px solid #00e676;
    }}

    QComboBox {{
        background-color: #1a1a1a;
        color: #e0e0e0;
        border: 1px solid #333;
        border-radius: 3px;
        padding: 5px 10px;
        min-width: 140px;
        font-size: 13px;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #888;
        width: 0;
        height: 0;
    }}

    QComboBox QAbstractItemView {{
        background-color: #1a1a1a;
        color: #e0e0e0;
        selection-background-color: #00e676;
        selection-color: #000;
        border: 1px solid #333;
    }}

    QLineEdit {{
        background-color: #1a1a1a;
        color: #e0e0e0;
        border: 1px solid #333;
        border-radius: 3px;
        padding: 6px 10px;
        font-size: 13px;
    }}

    QLineEdit:focus {{
        border: 1px solid #00e676;
    }}

    QSpinBox {{
        background-color: #1a1a1a;
        color: #e0e0e0;
        border: 1px solid #333;
        border-radius: 3px;
        padding: 5px;
        font-size: 13px;
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        width: 18px;
        background-color: #252525;
        border: 1px solid #333;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: #333;
    }}

    QPushButton {{
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: 1px solid #333;
        border-radius: 3px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    QPushButton:hover {{
        background-color: #2a2a2a;
        border: 1px solid #555;
    }}

    QPushButton:pressed {{
        background-color: #151515;
    }}

    QPushButton#primaryButton {{
        background-color: #00e676;
        color: #000;
        border: 1px solid #00e676;
    }}

    QPushButton#primaryButton:hover {{
        background-color: #00c853;
        border: 1px solid #00c853;
    }}

    QPushButton#dangerButton {{
        background-color: #ff1744;
        color: #fff;
        border: 1px solid #ff1744;
    }}

    QPushButton#dangerButton:hover {{
        background-color: #d50000;
        border: 1px solid #d50000;
    }}

    QPushButton#dangerButton:disabled {{
        background-color: #3a1e24;
        color: #666;
        border: 1px solid #3a1e24;
    }}

    QTextEdit {{
        background-color: #0a0a0a;
        color: #a0ffa0;
        border: 1px solid #2a2a2a;
        border-radius: 3px;
        font-family: {mono};
        font-size: 12px;
        padding: 10px;
        selection-background-color: #00e676;
        selection-color: #000;
    }}

    QMenuBar {{
        background-color: #121212;
        color: #e0e0e0;
        border-bottom: 1px solid #2a2a2a;
    }}

    QMenuBar::item:selected {{
        background-color: #1a1a1a;
        color: #00e676;
    }}

    QMenu {{
        background-color: #1a1a1a;
        color: #e0e0e0;
        border: 1px solid #333;
    }}

    QMenu::item:selected {{
        background-color: #00e676;
        color: #000;
    }}

    QLabel {{
        font-size: 13px;
        color: #bdbdbd;
    }}

    QLabel#statusLabel {{
        font-family: {mono};
        font-size: 12px;
        color: #9e9e9e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    QLabel#logTimestamp {{
        font-family: {mono};
        font-size: 11px;
        color: #757575;
    }}

    QProgressBar {{
        border: 1px solid #2a2a2a;
        border-radius: 2px;
        text-align: center;
        background-color: #0a0a0a;
        color: #000;
    }}

    QProgressBar::chunk {{
        background-color: #00e676;
    }}

    QMessageBox {{
        background-color: #1a1a1a;
    }}

    QMessageBox QLabel {{
        color: #e0e0e0;
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
    }}
    """

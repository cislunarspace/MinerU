# Copyright (c) Opendatalab. All rights reserved.
"""Lightweight API connectivity tester for LLM translation settings."""

import re

try:
    from PyQt6.QtCore import QObject, QThread, pyqtSignal
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False
    QObject = object
    QThread = None
    pyqtSignal = None


_TEST_PROMPT = (
    "请将以下文本翻译成中文，直接返回翻译结果，不要解释：\n{content}"
)
_TEST_CONTENT = "Hello, world!"
_TEST_TIMEOUT = 30

_SECRET_PATTERNS = [
    re.compile(r"\b(sk-[a-zA-Z0-9]{20,})\b"),
    re.compile(r"\b(Bearer\s+[a-zA-Z0-9_\-\.]+)\b", re.IGNORECASE),
    re.compile(r"\b(api[_-]?key\s*[:=]\s*[\"']?[a-zA-Z0-9_\-\.]+[\"']?)\b", re.IGNORECASE),
]


def _sanitize_error_message(message):
    """Remove potential API keys or tokens from error messages."""
    sanitized = message
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("***", sanitized)
    return sanitized


def format_api_test_error(error):
    """Return a user-friendly Chinese message for an API test error."""
    error_message = _sanitize_error_message(str(error))
    error_type = type(error).__name__

    lowered = error_message.lower()
    if "timeout" in lowered or "timed out" in lowered:
        return "请求超时，请检查网络连接或服务端点是否可达"

    if "401" in error_message or "unauthorized" in lowered:
        return "API Key 无效或未授权"

    if "404" in error_message or "not found" in lowered:
        return "模型不存在或服务端点错误"

    if "403" in error_message or "forbidden" in lowered:
        return "访问被拒绝，请检查 API Key 权限"

    if "429" in error_message or "rate limit" in lowered:
        return "请求过于频繁，请稍后再试"

    if "connection" in lowered or "connect" in lowered:
        return "无法连接到模型接口，请检查服务端点"

    if "api_key" in lowered or "apikey" in lowered:
        return "API Key 无效或未授权"

    return f"测试异常 ({error_type})：{error_message}"


class TestApiWorker(QObject):
    """Worker object for testing LLM API connectivity in background."""

    test_finished = pyqtSignal(str)
    test_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._thread = None
        self._is_running = False

    def is_running(self):
        """Return whether a test is currently running."""
        return self._is_running

    def run(self, base_url, model_name, api_key):
        """Run the API test in a background QThread."""
        if self._is_running:
            return

        self._is_running = True
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(
            lambda: self._do_test(base_url, model_name, api_key)
        )
        self._thread.start()

    def _do_test(self, base_url, model_name, api_key):
        try:
            from mineru.cli.llm_translate.llm_agent import LLmAgent

            agent = LLmAgent(
                base_url=base_url,
                model_name=model_name,
                api_key=api_key,
                timeout=_TEST_TIMEOUT,
                max_retries=0,
                use_cache=False,
            )
            result = agent.ask_llm(_TEST_PROMPT, _TEST_CONTENT)
            self.test_finished.emit(result.strip())
        except Exception as e:
            self.test_failed.emit(format_api_test_error(e))
        finally:
            self._is_running = False
            thread = self._thread
            if thread is not None:
                thread.finished.connect(thread.deleteLater)
                thread.quit()

    def wait(self, timeout_ms=3000):
        """Wait for the background thread to finish."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.wait(timeout_ms)

    def stop(self):
        """Request the worker to stop and wait for the thread."""
        self._is_running = False
        self.wait()


__all__ = ["TestApiWorker", "format_api_test_error"]

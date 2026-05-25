# LLM Translation module for MinerU
#
# This module provides translation functionality using LLM APIs.
# It includes:
# - LLM agent management
# - Markdown translation
# - Header correction

from mineru.cli.llm_translate.config import get_conf, get_default_config, reload_conf

__all__ = [
    "get_conf",
    "get_default_config",
    "reload_conf",
    "llm_agent_factory",
    "LLmAgent",
    "Translator",
    "get_corrector",
    "LlmTranslator",
]


def __getattr__(name):
    if name in {"llm_agent_factory", "LLmAgent"}:
        from mineru.cli.llm_translate.llm_agent import LLmAgent, llm_agent_factory

        values = {
            "llm_agent_factory": llm_agent_factory,
            "LLmAgent": LLmAgent,
        }
    elif name in {"Translator", "get_corrector"}:
        from mineru.cli.llm_translate.translator import Translator, get_corrector

        values = {
            "Translator": Translator,
            "get_corrector": get_corrector,
        }
    elif name == "LlmTranslator":
        from mineru.cli.llm_translate.llm_trans import LlmTranslator

        values = {"LlmTranslator": LlmTranslator}
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    globals().update(values)
    return values[name]

import logging

from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from mineru.cli.llm_translate.config import get_conf
from mineru.cli.llm_translate.llm_rate_control import RateControl
from mineru.cli.llm_translate.llm_cache import LLmCache


LOGGER = logging.getLogger(__name__)


class LLmAgent:
    def __init__(self, base_url, model_name, api_key, timeout=60, max_retries=2, use_cache=False, cache_file_name=None,
                 streaming=False):
        self.base_url = base_url
        self.model_name = model_name
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_cache = use_cache
        self.cache_file_name = cache_file_name
        self.streaming = streaming
        if use_cache:
            cache_dir = Path(__file__).parent.parent.parent.parent / "cache"
            cache_dir.mkdir(exist_ok=True)
            self.llmcache = LLmCache(cache_dir / f"{cache_file_name}.txt")

    def format_prompt(self, prompt, prompt_var):
        prompt = PromptTemplate.from_template(prompt)
        if isinstance(prompt_var, str):
            prompt_str = prompt.format(**{prompt.input_variables[0]: prompt_var})
        else:
            prompt_str = prompt.format(**prompt_var)
        return prompt_str

    def ask_llm_by_api(self, prompt, prompt_var):
        prompt_str = self.format_prompt(prompt, prompt_var)

        llm = ChatOpenAI(base_url=self.base_url, model_name=self.model_name, api_key=self.api_key, timeout=self.timeout,
                         max_retries=self.max_retries, temperature=0, streaming=self.streaming)
        response = llm.invoke(prompt_str)
        return self.normalize_response_content(response.content)

    def normalize_response_content(self, content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return ''.join(part.get('text', str(part)) if isinstance(part, dict) else str(part) for part in content)
        return str(content)

    def in_cache(self, prompt, prompt_var):
        if not self.use_cache:
            return False

        prompt_str = self.format_prompt(prompt, prompt_var)
        return prompt_str in self.llmcache

    def ask_llm(self, prompt, prompt_var):
        LOGGER.debug('prompt: %s, prompt_val: %s', prompt, str(prompt_var)[:100])
        prompt_str = self.format_prompt(prompt, prompt_var)
        LOGGER.debug('prompt_str: %s', prompt_str)

        if self.use_cache:
            text = self.llmcache.get(prompt_str)
            if text is None:
                text = self.ask_llm_by_api(prompt, prompt_var)
                self.llmcache.save_one(prompt_str, text)
        else:
            text = self.ask_llm_by_api(prompt, prompt_var)

        LOGGER.debug('text: %s', text)

        return text


class LLmAgentFactory:
    def __init__(self):
        self.agent_dict = {}

    def generate(self, llm_agent_name):
        if llm_agent_name in self.agent_dict:
            return self.agent_dict[llm_agent_name]

        conf = get_conf()
        llm_agent_conf = conf.get_conf()[llm_agent_name]
        base_url = llm_agent_conf['base_url']
        model_name = llm_agent_conf['model_name']
        api_key = llm_agent_conf['api_key']
        timeout = llm_agent_conf['timeout']

        rate_control = llm_agent_conf['rate_control']
        max_retries = llm_agent_conf['max_retries'] if not rate_control else 0

        use_cache = llm_agent_conf['use_cache']
        cache_file_name = llm_agent_conf['cache_file_name']

        streaming = llm_agent_conf['streaming']

        real_agent = LLmAgent(base_url, model_name, api_key, timeout=timeout, max_retries=max_retries,
                              use_cache=use_cache, cache_file_name=cache_file_name, streaming=streaming)

        if rate_control:
            rate_control_conf = conf.get_conf()[rate_control]
            rpm = rate_control_conf['rpm']
            tpm = rate_control_conf['tpm']
            wait_seconds = rate_control_conf['wait_seconds']
            max_retry = rate_control_conf['max_retry']
            window_gap = rate_control_conf['window_gap']
            token_encoding = rate_control_conf['token_encoding']
            rate_control_agent = RateControl(real_agent, rpm=rpm, tpm=tpm, wait_seconds=wait_seconds,
                                             max_retry=max_retry, window_gap=window_gap, token_encoding=token_encoding)
            self.agent_dict[llm_agent_name] = rate_control_agent
            return rate_control_agent
        else:
            self.agent_dict[llm_agent_name] = real_agent
            return real_agent


llm_agent_factory = LLmAgentFactory()

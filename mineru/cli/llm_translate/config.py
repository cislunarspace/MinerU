import yaml
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)


class Config:
    def __init__(self, conf_path=None, arg_to_conf_dict_path=None):
        if conf_path is None:
            conf_path = Path(__file__).parent.parent.parent.parent / "conf.yaml"
        if arg_to_conf_dict_path is None:
            arg_to_conf_dict_path = Path(__file__).parent / "dict" / "arg_to_conf_dict.yaml"

        with open(conf_path, 'rt', encoding='utf-8') as f:
            self.conf = yaml.safe_load(f)

        with open(arg_to_conf_dict_path, 'rt', encoding='utf-8') as f:
            self.arg_to_conf_dict = yaml.safe_load(f)

    def get_conf(self):
        return self.conf

    def set_by_key_path(self, key_name_path: str, value):
        key_names = key_name_path.split('.')
        conf_item = self.conf
        for index, key_name in enumerate(key_names):
            if index == len(key_names) - 1:
                conf_item[key_name] = value
            else:
                conf_item = conf_item[key_name]

    def override_conf(self, argparse_dict: dict):
        for argparse_name, argparse_value in argparse_dict.items():
            if argparse_name in self.arg_to_conf_dict:
                key_name_path = self.arg_to_conf_dict[argparse_name]
                self.set_by_key_path(key_name_path, argparse_value)

    def save(self, conf_path=None):
        if conf_path is None:
            conf_path = Path(__file__).parent.parent.parent.parent / "conf.yaml"
        with open(conf_path, 'wt', encoding='utf-8') as f:
            yaml.safe_dump(self.conf, f, allow_unicode=True, sort_keys=False)


def get_default_config():
    """Return default configuration dict."""
    return {
        'llm_agent': {
            'base_url': 'https://api.deepseek.com/',
            'model_name': 'deepseek-chat',
            'api_key': '',
            'timeout': 120,
            'max_retries': 2,
            'use_cache': True,
            'cache_file_name': 'default',
            'rate_control': None,
            'streaming': False,
        },
        'llm_translator': {
            'need_format_code': True,
            'need_correct_imagepath': True,
            'timeout': 120,
            'max_workers': 4,
            'llm_agent_name': 'llm_agent',
            'title_add_size': 200,
            'chunk_size': 2048,
        },
        'header_corrector': {
            'allow_distance': 3,
            'allow_diff_chars': ['$', ' ', ' '],
            'title_chunk_size': 1024,
            'allow_miss_num': 8,
            'allow_miss_depth': 4,
            'llm_agent_name': 'llm_agent',
        },
        'code_format': {
            'languages': ['cpp', 'python'],
            'format_all_code': True,
            'remove_code_in_line': True,
            'code_in_line_length': 60,
            'line_length': 80,
            'split_before_chars': ['.', '-', '+', '/', '*'],
            'split_after_chars': [' ', ',', '(', ')', ';', ':'],
            'force_split': True,
            'indentation': 4,
        },
        'doc_convertor': {
            'correct_header_type': 'bookmark',
            'font': 'STSONG',
            'sure_has_font': False,
        },
    }


# Global config instance - lazy loaded
_conf = None


def get_conf():
    """Get or create the global config instance."""
    global _conf
    if _conf is None:
        conf_path = Path(__file__).parent.parent.parent.parent / "conf.yaml"
        if conf_path.exists():
            _conf = Config(conf_path)
        else:
            # Create default config
            _conf = Config()
            _conf.conf = get_default_config()
    return _conf


def reload_conf():
    """Force reload the config from file."""
    global _conf
    _conf = Config()
    return _conf

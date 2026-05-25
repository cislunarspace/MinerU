import logging
import os
from pathlib import Path

from mineru.cli.llm_translate.llm_trans import LlmTranslator
from mineru.cli.llm_translate.config import get_conf


LOGGER = logging.getLogger(__name__)


class Translator:
    def __init__(self):
        self.llm_translator = LlmTranslator()

    def translate(self, md_path, start_page=1, end_page=None):
        """
        Translate markdown file.

        Args:
            md_path: Path to markdown file
            start_page: Start page (for logging)
            end_page: End page (for logging)

        Returns:
            Path to translated markdown file
        """
        md_trans_path = self.llm_translator.do_translate(md_path)
        LOGGER.info('translate finish, md_trans_path: %s', md_trans_path)
        return md_trans_path


def get_corrector(correct_header_type):
    """
    Get header corrector based on type.

    Args:
        correct_header_type: One of 'no', 'bookmark', 'by_llm', 'by_llm_easy'

    Returns:
        Header corrector instance or None
    """
    from mineru.cli.llm_translate.corrector.header_factory import HeaderFactory

    if correct_header_type == 'no':
        return None
    elif correct_header_type in {'by_llm', 'by_llm_easy'}:
        easy_header = correct_header_type == 'by_llm_easy'
        return HeaderFactory(easy_header).generate()
    elif correct_header_type == 'bookmark':
        # For bookmark correction, we need the PDF
        # This should be handled at a higher level
        return None
    else:
        raise ValueError(f'Unknown correct_header_type: {correct_header_type}')

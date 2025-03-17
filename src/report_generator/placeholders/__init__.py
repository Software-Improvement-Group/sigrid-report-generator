from typing import Set, Type

from .base import Placeholder
from .misc import placeholders as misc_placeholders
from .text import placeholders as text_placeholders

PlaceholderCollection = Set[Type[Placeholder]]

placeholders: PlaceholderCollection = text_placeholders | misc_placeholders

from .text import text_placeholder, parameterized_text_placeholder

__all__ = ['Placeholder', 'text_placeholder', 'parameterized_text_placeholder', 'PlaceholderCollection', 'placeholders']

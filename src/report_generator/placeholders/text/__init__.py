import inspect

from . import implementations as _all_implementations
from .base import text_placeholder, parameterized_text_placeholder

_placeholders_map = {
    name: obj for name, obj in inspect.getmembers(_all_implementations, inspect.isclass)
    if hasattr(obj, '__placeholder__')
}

placeholders = set(_placeholders_map.values())

__all__ = list(_placeholders_map.keys())

#  Copyright Software Improvement Group
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import inspect

from . import implementations as _all_implementations
from .base import parameterized_text_placeholder, text_placeholder

_placeholders_map = {
    name: obj for name, obj in inspect.getmembers(_all_implementations, inspect.isclass)
    if hasattr(obj, '__placeholder__')
}

placeholders = set(_placeholders_map.values())

__all__ = list(_placeholders_map.keys())

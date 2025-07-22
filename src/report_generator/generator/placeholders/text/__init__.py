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

from . import architecture, maintainability, metadata, modernization, osh
from .base import parameterized_text_placeholder, text_placeholder

_modules_to_scan = [architecture, maintainability, metadata, modernization, osh]

_placeholders_map = {}
for module in _modules_to_scan:
    module_placeholders = {
        name: obj for name, obj in inspect.getmembers(module, inspect.isclass)
        if hasattr(obj, '__placeholder__')
    }
    _placeholders_map.update(module_placeholders)

placeholders = set(_placeholders_map.values())
__all__ = list(_placeholders_map.keys())

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

from . import (
    architecture_treemap,
    maintainability_delta_quality_treemap,
    maintainability_treemap,
    osh_treemap,
    security_treemap,
    test_code_treemap,
    volume_treemap,
)

_all_implementations = {
    **maintainability_treemap.__dict__,
    **maintainability_delta_quality_treemap.__dict__,
    **volume_treemap.__dict__,
    **test_code_treemap.__dict__,
    **security_treemap.__dict__,
    **architecture_treemap.__dict__,
    **osh_treemap.__dict__,
}

_placeholders_map = {
    name: obj
    for name, obj in _all_implementations.items()
    if inspect.isclass(obj)
    and hasattr(obj, "__placeholder__")
    and not inspect.isabstract(obj)
}

placeholders = set(_placeholders_map.values())

__all__ = list(_placeholders_map.keys())

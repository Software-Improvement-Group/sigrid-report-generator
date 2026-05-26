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

from . import functional_suitability_top_systems, maintainability_top_systems, refactoring_candidates, reliability_findings, security_findings

_all_implementations = {
    **refactoring_candidates.__dict__,
    **security_findings.__dict__,
    **reliability_findings.__dict__,
    **maintainability_top_systems.__dict__,
    **functional_suitability_top_systems.__dict__,
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

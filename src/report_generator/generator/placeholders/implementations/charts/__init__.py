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
    findings_scatterplots,
    maintainability_delta_quality_charts,
    maintainability_galaxy_charts,
    osh_charts,
    security_findings,
)

_all_implementations = {
    **security_findings.__dict__,
    **osh_charts.__dict__,
    **maintainability_galaxy_charts.__dict__,
    **findings_scatterplots.__dict__,
    **maintainability_delta_quality_charts.__dict__,
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

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

import math


def findings_x_axis_max(value: int) -> int:
    """Round up to the next half-order-of-magnitude step, with a minimum of 20."""
    value = max(value, 10)
    magnitude = 10 ** math.floor(math.log10(value))
    step = magnitude // 2
    return (value // step + 1) * step

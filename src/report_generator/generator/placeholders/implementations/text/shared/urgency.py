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

from pptx.dml.color import RGBColor

_URGENCY_RED = RGBColor(0xDC, 0x49, 0x3C)
_URGENCY_ORANGE = RGBColor(0xF0, 0x97, 0x1A)
_URGENCY_YELLOW = RGBColor(0xF1, 0xCF, 0x63)
_URGENCY_GREEN = RGBColor(0x7A, 0xCD, 0x75)

MEDIUM_RISK_THRESHOLD = 30

_URGENCY_WIDTHS: dict[str, float | None] = {
    "strong": 0.62,
    "moderate": 0.83,
    "weak": 0.54,
    "review": 0.62,
}


def urgency_width(value: str) -> float | None:
    return _URGENCY_WIDTHS.get(value)


def urgency_color(distr: dict) -> RGBColor:
    if distr["critical"] > 0:
        return _URGENCY_RED
    if distr["high"] > 0 or distr["medium"] > MEDIUM_RISK_THRESHOLD:
        return _URGENCY_ORANGE
    if distr["medium"] > 0:
        return _URGENCY_YELLOW
    return _URGENCY_GREEN

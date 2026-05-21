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

from dataclasses import dataclass

from pptx.dml.color import RGBColor

MEDIUM_RISK_THRESHOLD = 30

_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_BLACK = RGBColor(0x00, 0x00, 0x00)


@dataclass(frozen=True)
class UrgencyColors:
    shape: RGBColor
    text: RGBColor


_URGENCY_COLORS: list[UrgencyColors] = [
    UrgencyColors(shape=RGBColor(0xDC, 0x49, 0x3C), text=_WHITE),  # critical
    UrgencyColors(
        shape=RGBColor(0xF0, 0x97, 0x1A), text=_BLACK
    ),  # high / medium > threshold
    UrgencyColors(shape=RGBColor(0xF1, 0xCF, 0x63), text=_BLACK),  # medium
    UrgencyColors(shape=RGBColor(0x7A, 0xCD, 0x75), text=_WHITE),  # low / none
]

_URGENCY_WIDTHS: dict[str, float | None] = {
    "strong": 0.62,
    "moderate": 0.83,
    "weak": 0.54,
    "review": 0.62,
}


def _urgency_level(distr: dict) -> int:
    if distr["critical"] > 0:
        return 0
    if distr["high"] > 0 or distr["medium"] > MEDIUM_RISK_THRESHOLD:
        return 1
    if distr["medium"] > 0:
        return 2
    return 3


def urgency_colors(distr: dict) -> UrgencyColors:
    return _URGENCY_COLORS[_urgency_level(distr)]


def exploit_probability_colors(probability: float) -> UrgencyColors:
    if probability == 0.0:
        return _URGENCY_COLORS[3]  # green: no exploitable vulnerabilities
    if probability > 0.50:
        return _URGENCY_COLORS[0]  # red
    if probability > 0.15:
        return _URGENCY_COLORS[1]  # orange
    return _URGENCY_COLORS[2]  # yellow


def exploit_probability_label(probability: float) -> str:
    if probability > 0.50:
        return "weak"
    if probability > 0.15:
        return "moderate"
    return "strong"


def urgency_width(value: str) -> float | None:
    return _URGENCY_WIDTHS.get(value)

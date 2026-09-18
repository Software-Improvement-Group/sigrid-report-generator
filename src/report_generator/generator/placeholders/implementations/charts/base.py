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
from abc import ABC, abstractmethod

from report_generator.generator.placeholders.implementations.base import (
    Placeholder,
    PlaceholderDocType,
)
from report_generator.generator.placeholders.rendering.pptx import find_charts


class ChartPlaceholder(Placeholder, ABC):
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def resolve_pptx(cls, presentation, key: str, value_cb):
        charts = find_charts(presentation, key)
        if not charts:
            return
        cls._populate_chart(charts, value_cb)

    @staticmethod
    @abstractmethod
    def _populate_chart(charts, value_cb) -> None:
        pass


def findings_x_axis_max(value: int) -> int:
    """Round up to the next half-order-of-magnitude step, with a minimum of 20."""
    value = max(value, 15)
    magnitude = 10 ** math.floor(math.log10(value))
    step = magnitude // 2
    return (value // step + 1) * step

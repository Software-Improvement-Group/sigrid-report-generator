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

from typing import ClassVar

from report_generator.generator.domain import architecture_data, maintainability_data
from report_generator.generator.placeholders.implementations.shared.color_rating_base import (
    AbstractColorRatingPlaceholder,
)
from report_generator.generator.utils.constants import (
    ArchMetric,
    ArchSubcharacteristic,
    MaintMetric,
    MetricEnum,
)


class MaintColorRatingPlaceholder(AbstractColorRatingPlaceholder):
    """Fills the rating value and colors the shape to the corresponding rating color for a maintainability metric."""

    key = "COLOR_MAINT_RATING_{parameter}"
    allowed_parameters: ClassVar[list] = list(MaintMetric)

    @classmethod
    def value(cls, metric: MaintMetric):
        metric_key = metric.to_json_name()
        return maintainability_data.data[metric_key]


class ArchColorRatingPlaceholder(AbstractColorRatingPlaceholder):
    """Fills the rating value and colors the shape to the corresponding rating color for an architecture metric."""

    key = "COLOR_ARCH_RATING_{parameter}"
    allowed_parameters: ClassVar[list] = list(ArchMetric) + list(ArchSubcharacteristic)

    @classmethod
    def value(cls, metric: MetricEnum):
        metric_key = metric.to_json_name()
        return architecture_data.get_score_for_prop_or_subchar(metric_key)

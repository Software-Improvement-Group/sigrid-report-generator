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

from abc import ABC
from typing import Callable

from pptx import Presentation

from report_generator.generator import report_utils
from report_generator.generator.constants import ArchMetric, ArchSubcharacteristic, MaintMetric, MetricEnum
from report_generator.generator.data_models import architecture_data, maintainability_data
from report_generator.generator.formatters import formatters
from report_generator.generator.placeholders.base import ParameterizedPlaceholder


class _AbstractColorRatingPlaceholder(ParameterizedPlaceholder, ABC):
    """Fills this rating value, but also colors the shape the placeholder is in to correspond to the correct maintainability rating color (e.g. yellow for 3 stars)."""

    @classmethod
    def resolve_pptx(cls, presentation: Presentation, key: str, value_cb: Callable):
        shapes = report_utils.pptx.find_shapes_with_text(presentation, key)
        paragraphs = report_utils.pptx.find_text_in_presentation(presentation, key)

        if len(shapes) == 0 and len(paragraphs) == 0:
            return

        rating = value_cb()

        rating_color = report_utils.pptx.determine_rating_color(rating)
        rating_rounded = formatters.maintainability_round(rating)

        for shape in shapes:
            report_utils.pptx.set_shape_color(shape, rating_color)

        report_utils.pptx.update_many_paragraphs(paragraphs, key, rating_rounded)


class ArchColorRatingPlaceholder(_AbstractColorRatingPlaceholder):
    key = "COLOR_ARCH_RATING_{parameter}"
    allowed_parameters = list(ArchMetric) + list(ArchSubcharacteristic)

    @classmethod
    def value(cls, metric: MetricEnum = None):
        metric_key = metric.to_json_name()
        return architecture_data.get_score_for_prop_or_subchar(metric_key)


class MaintColorRatingPlaceholder(_AbstractColorRatingPlaceholder):
    key = "COLOR_MAINT_RATING_{parameter}"
    allowed_parameters = list(MaintMetric)

    @classmethod
    def value(cls, metric: MetricEnum = None):
        metric_key = metric.to_json_name()
        return maintainability_data.data[metric_key]

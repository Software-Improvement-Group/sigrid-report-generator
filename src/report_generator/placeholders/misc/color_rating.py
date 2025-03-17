from abc import ABC
from typing import Callable

from pptx import Presentation

from report_generator import constants, report_utils
from report_generator.data_models import architecture_data, maintainability_data
from report_generator.formatters import formatters
from report_generator.placeholders.base import ParameterizedPlaceholder, Parameter


def _to_json_name(metric):
    metric = metric.replace("_", " ").title().replace(" ", "")
    return metric[0].lower() + metric[1:]


class _AbstractColorRatingPlaceholder(ParameterizedPlaceholder, ABC):
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
    allowed_parameters = constants.ARCH_METRICS + constants.ARCH_SUBCHARACTERISTICS

    @classmethod
    def value(cls, metric: Parameter = None):
        metric_key = _to_json_name(metric)
        return architecture_data.get_score_for_prop_or_subchar(metric_key)


class MaintColorRatingPlaceholder(_AbstractColorRatingPlaceholder):
    key = "COLOR_MAINT_RATING_{parameter}"
    allowed_parameters = constants.MAINT_METRICS

    @classmethod
    def value(cls, metric: Parameter = None):
        metric_key = _to_json_name(metric)
        return maintainability_data.data[metric_key]

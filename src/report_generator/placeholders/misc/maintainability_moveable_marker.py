from abc import ABC
from typing import Callable

from pptx import Presentation

from report_generator import report_utils
from report_generator.data_models import maintainability_data, architecture_data
from report_generator.formatters.formatters import maintainability_round
from report_generator.placeholders import Placeholder

_RATING_MARKER_MOVE_SIZE = 2200000


def _distance_to_average(rating):
    return -1 * (3.0 - rating)


class _AbstractMoveableMarkerPlaceholder(Placeholder, ABC):
    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable[[], str]) -> None:
        paragraphs = []
        for slide in presentation.slides:
            paragraphs.extend(report_utils.pptx.find_text_in_slide(slide, key))

        if len(paragraphs) == 0:
            return

        value = value_cb()
        value_float = float(value)

        for paragraph in paragraphs:
            report_utils.pptx.update_paragraph(paragraph, key, value)

            # noinspection PyProtectedMember
            marker = paragraph._parent._parent._parent._parent
            marker.left = int(marker.left + _RATING_MARKER_MOVE_SIZE * _distance_to_average(value_float))


class MaintainabilityMovableMarkerPlaceholder(_AbstractMoveableMarkerPlaceholder):
    key = "MARKER_MAINT_RATING"

    @classmethod
    def value(cls, parameter=None):
        return maintainability_round(maintainability_data.maintainability_rating)


class ArchitectureMovableMarkerPlaceholder(_AbstractMoveableMarkerPlaceholder):
    key = "MARKER_ARCH_RATING"

    @classmethod
    def value(cls, parameter=None):
        return maintainability_round(architecture_data.ratings["architecture"])

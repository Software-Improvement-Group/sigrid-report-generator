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
from enum import Enum, auto
from typing import Callable

from pptx.dml.color import RGBColor
from pptx.presentation import Presentation
from pptx.util import Inches

from report_generator.generator.placeholders import rendering
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.base import (
    ParameterizedPlaceholder,
    Placeholder,
)
from report_generator.generator.placeholders.rendering.common import (
    FontColor,
    FontProperties,
)


class WidthAnchor(Enum):
    LEFT = auto()  # shape grows/shrinks to the right; left edge stays fixed
    RIGHT = auto()  # shape grows/shrinks to the left; right edge stays fixed


class AbstractColoredShapePlaceholder(Placeholder, ABC):
    """Colors a shape and replaces its placeholder text with a given value."""

    @classmethod
    def _find(cls, presentation: Presentation, key: str):
        shapes = rendering.pptx.find_shapes_with_text(presentation, key)
        paragraphs = rendering.pptx.find_text_in_presentation(presentation, key)
        return shapes, paragraphs

    @classmethod
    def _apply(
        cls,
        shapes,
        paragraphs,
        key: str,
        shape_color: RGBColor,
        display_value: str,
        width_inches: float | None = None,
        width_anchor: WidthAnchor = WidthAnchor.LEFT,
        text_color: RGBColor | None = None,
    ):
        for shape in shapes:
            rendering.pptx.set_shape_color(shape, shape_color)
            if width_inches is not None:
                new_width = Inches(width_inches)
                if width_anchor == WidthAnchor.RIGHT:
                    shape.left += shape.width - new_width
                shape.width = new_width
        font = (
            FontProperties(color=FontColor(rgb=text_color))
            if text_color is not None
            else None
        )
        rendering.pptx.update_many_paragraphs(paragraphs, key, display_value, font)

    @classmethod
    def resolve_pptx(
        cls,
        presentation: Presentation,
        key: str,
        shape_color: RGBColor,
        display_value: str,
    ):
        shapes, paragraphs = cls._find(presentation, key)
        if not shapes and not paragraphs:
            return
        cls._apply(shapes, paragraphs, key, shape_color, display_value)


class AbstractColorRatingPlaceholder(
    AbstractColoredShapePlaceholder, ParameterizedPlaceholder, ABC
):
    """Fills this rating value and colors the shape to correspond to the rating color (e.g. yellow for 3 stars)."""

    @classmethod
    def resolve_pptx(cls, presentation: Presentation, key: str, value_cb: Callable):
        shapes, paragraphs = cls._find(presentation, key)
        if not shapes and not paragraphs:
            return
        rating = value_cb()
        cls._apply(
            shapes,
            paragraphs,
            key,
            shape_color=rendering.pptx.determine_rating_color(rating),
            display_value=formatters.star_rating_round(rating),
        )

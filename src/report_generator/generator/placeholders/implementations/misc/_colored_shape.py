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

from collections.abc import Callable
from dataclasses import dataclass

from pptx.presentation import Presentation

from report_generator.generator.placeholders import rendering
from report_generator.generator.placeholders.rendering.common import (
    CommonRGBColor,
    FontColor,
    FontProperties,
)
from report_generator.generator.placeholders.rendering.pptx import ShapeProperties


@dataclass(frozen=True)
class ColoredShape:
    """How the shapes holding a key are styled, and the text that replaces the key."""

    shape_props: ShapeProperties
    display_value: str
    text_color: CommonRGBColor | None = None


def apply_colored_shape(
    presentation: Presentation, key: str, build: Callable[[], ColoredShape]
):
    """Styles every shape holding `key` and replaces the key's text, skipping `build` when `key` is absent."""
    shapes = rendering.pptx.find_shapes_with_text(presentation, key)
    paragraphs = rendering.pptx.find_text_in_presentation(presentation, key)
    if not shapes and not paragraphs:
        return
    colored = build()
    for shape in shapes:
        rendering.pptx.apply_shape_properties(shape, colored.shape_props)
    rendering.pptx.update_many_paragraphs(
        paragraphs, key, colored.display_value, _font_for(colored.text_color)
    )


def _font_for(text_color: CommonRGBColor | None) -> FontProperties | None:
    if text_color is None:
        return None
    return FontProperties(color=FontColor(rgb=text_color))

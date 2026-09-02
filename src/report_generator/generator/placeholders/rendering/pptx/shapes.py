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
from pptx.util import Inches


def set_shape_color(shape, rgb_color):
    shape.fill.fore_color.rgb = rgb_color


@dataclass
class ShapeProperties:
    color: RGBColor
    # After text replacement a shape keeps the width of the placeholder key, which is usually
    # longer than the display value. width_inches overrides that; width_anchor_right decides
    # which edge stays put while it shrinks.
    width_inches: float | None = None
    width_anchor_right: bool = False


def apply_shape_properties(shape, props: ShapeProperties) -> None:
    set_shape_color(shape, props.color)
    if props.width_inches is not None:
        new_width = Inches(props.width_inches)
        if props.width_anchor_right:
            shape.left += shape.width - new_width
        shape.width = new_width

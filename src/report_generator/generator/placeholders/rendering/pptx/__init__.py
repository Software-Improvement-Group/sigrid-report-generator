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

"""The PowerPoint rendering API, split by concern.

`index` answers where the text is, `find` locates it, `write` changes it, `structure` removes
slides, shapes and rows, `shapes` sets a shape's appearance, and `colors` holds the palette.
"""

from . import index
from .colors import (
    FIVE_STAR_COLOR,
    FOUR_STAR_COLOR,
    NA_STAR_COLOR,
    ONE_STAR_COLOR,
    RATING_NEG_CHANGE_RANGE_COLORS,
    RATING_POS_CHANGE_RANGE_COLORS,
    SENTIMENT_COLORS,
    SIG_BLUE_COLOR,
    SIG_GREY_COLOR,
    THREE_STAR_COLOR,
    TWO_STAR_COLOR,
    VOLUME_NEG_CHANGE_RANGE_COLORS,
    VOLUME_POS_CHANGE_RANGE_COLORS,
    determine_rating_color,
    interpolate_color,
    sentiment_color,
    test_code_ratio_color,
)
from .find import (
    find_charts,
    find_shapes,
    find_shapes_with_text,
    find_tables,
    find_text_in_presentation,
    find_text_in_slide,
)
from .shapes import ShapeProperties, apply_shape_properties, set_shape_color
from .structure import (
    delete_slides_with_placeholder,
    remove_row_from_table,
    remove_rows_from_table,
    remove_shape,
)
from .write import (
    Hyperlink,
    replace_paragraph_with_text,
    update_many_paragraphs,
    update_paragraph,
    update_table,
)

__all__ = [
    "FIVE_STAR_COLOR",
    "FOUR_STAR_COLOR",
    "NA_STAR_COLOR",
    "ONE_STAR_COLOR",
    "RATING_NEG_CHANGE_RANGE_COLORS",
    "RATING_POS_CHANGE_RANGE_COLORS",
    "SENTIMENT_COLORS",
    "SIG_BLUE_COLOR",
    "SIG_GREY_COLOR",
    "THREE_STAR_COLOR",
    "TWO_STAR_COLOR",
    "VOLUME_NEG_CHANGE_RANGE_COLORS",
    "VOLUME_POS_CHANGE_RANGE_COLORS",
    "Hyperlink",
    "ShapeProperties",
    "apply_shape_properties",
    "delete_slides_with_placeholder",
    "determine_rating_color",
    "find_charts",
    "find_shapes",
    "find_shapes_with_text",
    "find_tables",
    "find_text_in_presentation",
    "find_text_in_slide",
    "index",
    "interpolate_color",
    "remove_row_from_table",
    "remove_rows_from_table",
    "remove_shape",
    "replace_paragraph_with_text",
    "sentiment_color",
    "set_shape_color",
    "test_code_ratio_color",
    "update_many_paragraphs",
    "update_paragraph",
    "update_table",
]

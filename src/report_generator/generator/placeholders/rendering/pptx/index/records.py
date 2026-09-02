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

# noinspection PyProtectedMember
from pptx.text.text import _Paragraph


@dataclass
class ParagraphRecord:
    """`text_owner` is the proxy whose text is searched, which is not always the paragraph: a table
    cell is matched on the whole cell text but yields its first paragraph. `top_level_shape` is
    recorded during the walk because it cannot be recovered afterwards -- the parent chain of a
    nested paragraph leads to the innermost shape, not to the slide-level one.
    """

    paragraph: _Paragraph
    text_owner: object
    text: str
    top_level_shape: object


@dataclass
class SlideIndex:
    slide: object
    paragraphs: list[ParagraphRecord]
    shape_names_including_nested: set[str]
    top_level_shapes: list


@dataclass
class PresentationIndex:
    """`paragraphs` is the slide indexes concatenated, so it is in document order. The maps
    are keyed on lxml elements rather than proxies, because proxies are recreated on every
    access and so cannot be compared by identity.
    """

    slides: list[SlideIndex]
    paragraphs: list[ParagraphRecord]
    slide_index_by_element: dict[object, SlideIndex]
    records_by_paragraph_element: dict[object, list[ParagraphRecord]]

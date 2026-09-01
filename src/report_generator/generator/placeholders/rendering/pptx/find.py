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

import logging

from pptx.presentation import Presentation

from . import index


def find_text_in_presentation(presentation, search_text):
    paragraphs = index.matching_paragraphs(
        index.for_presentation(presentation).paragraphs, search_text
    )
    logging.debug(f"Finds for {search_text}: {len(paragraphs)} paragraphs")
    return paragraphs


def find_text_in_slide(slide, search_text):
    return index.matching_paragraphs(index.for_slide(slide).paragraphs, search_text)


def _shapes_for_paragraphs(paragraphs):
    # Multiple matching paragraphs can share a shape, so de-duplicate while preserving order.
    shapes = []
    for paragraph in paragraphs:
        # noinspection PyProtectedMember
        shape = paragraph._parent._parent
        if shape not in shapes:
            shapes.append(shape)
    return shapes


def find_shapes_with_text(presentation, search_text):
    shapes = []
    for slide in presentation.slides:
        shapes += _shapes_for_paragraphs(find_text_in_slide(slide, search_text))
    logging.debug(f"Finds for {search_text}: {len(shapes)} shapes")
    return shapes


def _top_level_shapes_named(presentation: Presentation, key: str):
    return [
        shape
        for slide in index.for_presentation(presentation).slides
        for shape in slide.top_level_shapes
        if shape.name.strip() == key
    ]


def find_charts(presentation: Presentation, key: str):
    """Shape name is the supported way to locate a chart; its text is not searched."""
    charts = [
        shape.chart
        for shape in _top_level_shapes_named(presentation, key)
        if shape.has_chart
    ]
    logging.debug(f"Finds for {key}: {len(charts)}")
    return charts


def find_tables(presentation: Presentation, key: str):
    tables = [
        shape.table
        for shape in _top_level_shapes_named(presentation, key)
        if shape.has_table
    ]
    logging.debug(f"Finds for {key}: {len(tables)}")
    return tables


def _deduplicate_consecutive_shapes(shapes):
    """Every paragraph of a shape is indexed before the next shape's, so a shape that matches
    several times -- a group matching through more than one of its children, say -- always
    produces adjacent entries. Elements are compared because proxies are recreated per access.
    """
    unique = []
    for shape in shapes:
        if not unique or unique[-1].element is not shape.element:
            unique.append(shape)
    return unique


def find_shapes(presentation: Presentation, key: str):
    """Yields the top-level shape even when the text sits in a nested one, because callers
    use it for the shape's position and size on the slide.
    """
    shapes = _deduplicate_consecutive_shapes(
        record.top_level_shape
        for record in index.for_presentation(presentation).paragraphs
        if index.matches(record.text, key)
    )
    logging.debug(f"Finds for {key}: {len(shapes)}")
    return shapes

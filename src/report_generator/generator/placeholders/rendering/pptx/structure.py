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

"""Edits that change the document structure, and so must invalidate the cached index.

A detached shape's paragraphs still look writable, but the writes are dropped when the file is
saved. Skipping the invalidation turns a visible failure into a silently wrong report.
"""

import logging
from collections.abc import Iterable

from pptx.presentation import Presentation

# noinspection PyProtectedMember
from pptx.table import Table, _Row

from . import index
from .find import find_text_in_slide


def remove_shape(shape) -> None:
    index.invalidate(shape)
    element = shape.element
    element.getparent().remove(element)


def remove_row_from_table(table: Table, row: _Row):
    index.invalidate(table)
    # noinspection PyProtectedMember
    table._tbl.remove(row._tr)


def remove_rows_from_table(table: Table, row_numbers: Iterable[int]):
    for row_number in sorted(row_numbers, reverse=True):
        remove_row_from_table(table, table.rows[row_number])


def _slide_title(slide) -> str:
    title_shape = slide.shapes.title
    if title_shape is None or not title_shape.has_text_frame:
        return "<untitled>"
    return title_shape.text_frame.text.strip() or "<untitled>"


def _slide_contains_key(slide, key: str) -> bool:
    # Text placeholders match on paragraph text; chart and table placeholders match on shape
    # name. Both paths descend into groups, so a nested placeholder is still detected.
    if find_text_in_slide(slide, key):
        return True
    return key in index.for_slide(slide).shape_names_including_nested


def _slides_to_remove(presentation: Presentation, key: str):
    """presentation.slides iterates in <p:sldIdLst> order, so the i-th slide corresponds to
    the i-th <p:sldId>. Both are snapshotted so removing from the id list afterwards is safe.
    """
    return [
        (slide, sld_id)
        for slide, sld_id in zip(
            list(presentation.slides),
            list(presentation.slides.element),
            strict=True,
        )
        if _slide_contains_key(slide, key)
    ]


def delete_slides_with_placeholder(
    presentation: Presentation, key: str, reason: str | None = None
) -> None:
    """Called when a placeholder fails to resolve, so the report never shows an unresolved
    template token. Idempotent across repeated failures -- a slide already removed from the id
    list no longer appears in presentation.slides. `reason` is the message the Sigrid API
    returned with the failing request, such as a missing-license notice.
    """
    doomed = _slides_to_remove(presentation, key)
    detail = f" ({reason})" if reason else ""
    for slide, sld_id in doomed:
        presentation.slides.element.remove(sld_id)
        logging.info(
            f"Skipped slide '{_slide_title(slide)}' containing placeholder '{key}' "
            f"because it failed to resolve{detail}"
        )

    # An unlicensed report fails hundreds of placeholders without matching a single slide, and
    # rebuilding the index for each would undo the caching.
    if doomed:
        index.invalidate(presentation)

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
from dataclasses import dataclass

# noinspection PyProtectedMember
from pptx.table import Table

# noinspection PyProtectedMember
from pptx.text.text import _Paragraph, _Run

from ..common import (
    FontProperties,
    apply_font_properties,
    get_font_properties,
    merge_runs_with_same_formatting,
)
from . import index
from .structure import remove_rows_from_table


@dataclass
class Hyperlink:
    text: str
    url: str


def update_many_paragraphs(
    paragraphs, placeholder_id, replacement_text, font: FontProperties = None
):
    for paragraph in paragraphs:
        update_paragraph(paragraph, placeholder_id, replacement_text, font)


def _run_to_write_placeholder_into(
    paragraph: _Paragraph, placeholder_id
) -> _Run | None:
    pattern = index.word_bounded_pattern(placeholder_id)
    run = next((run for run in paragraph.runs or [] if pattern.search(run.text)), None)
    if run is None:
        logging.warning(
            f"Attempt to update placeholder '{placeholder_id}', but not found in paragraph: {paragraph.text}"
        )
    return run


def update_paragraph(
    paragraph: _Paragraph, placeholder_id, replacement_text, font: FontProperties = None
):
    merge_runs_with_same_formatting(paragraph)
    run = _run_to_write_placeholder_into(paragraph, placeholder_id)
    if run is None:
        return

    run.text = index.word_bounded_pattern(placeholder_id).sub(
        str(replacement_text), run.text
    )
    logging.debug(f'Replaced {placeholder_id} with "{replacement_text}": {run.text}')
    if font:
        apply_font_properties(run, font)
    index.note_text_changed(paragraph)


def _apply_hyperlink(run: _Run, hyperlink: Hyperlink) -> None:
    run.text = hyperlink.text
    run.hyperlink.address = hyperlink.url


def replace_paragraph_with_text(
    paragraph: _Paragraph,
    text: str | int | float | Hyperlink,
    font: FontProperties = None,
):
    paragraph.clear()
    run: _Run = paragraph.add_run()
    if isinstance(text, Hyperlink):
        _apply_hyperlink(run, text)
    else:
        run.text = "" if text is None else str(text)
    if font:
        apply_font_properties(run, font)

    index.note_text_changed(paragraph)


def _fill_row(row, values, column_fonts: dict) -> None:
    for col_idx, cell in enumerate(row.cells):
        if col_idx >= len(values):
            continue

        paragraph: _Paragraph = cell.text_frame.paragraphs[0]
        if paragraph.runs:
            column_fonts[col_idx] = get_font_properties(paragraph.runs[0])
        replace_paragraph_with_text(
            paragraph, values[col_idx], column_fonts.get(col_idx)
        )


def update_table(table: Table, value: list[list[str | int | float | Hyperlink]]):
    """Fill a table with values, dropping the rows the values do not reach.

    A column's font is taken from the first cell in it that has one, and applied to every later
    cell in that column.
    """
    column_fonts: dict = {}
    for row_idx, row in enumerate(table.rows):
        if row_idx >= len(value):
            # Breaking rather than continuing: the rows this iterator has left are the ones
            # just removed, and lxml does not promise anything about iterating past that.
            remove_rows_from_table(table, range(row_idx, len(table.rows)))
            break
        _fill_row(row, value[row_idx], column_fonts)

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
import re
from typing import Union


def find_text_in_document(document, search_text):
    paragraphs = []
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            if re.match(rf".*\b{search_text}\b.*", run.text):
                paragraphs.append(paragraph)

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if re.match(rf".*\b{search_text}\b.*", run.text):
                            paragraphs.append(paragraph)

    return paragraphs


def update_many_paragraphs(paragraphs, placeholder_id, replacement_text):
    for paragraph in paragraphs:
        update_paragraph(paragraph, placeholder_id, replacement_text)


def update_paragraph(paragraph, placeholder_id, replacement_text: Union[str, int, float]):
    replacement_text = str(replacement_text)

    try:
        run_with_placeholder = next(run for run in paragraph.runs if placeholder_id in run.text)
    except StopIteration:
        logging.warning(
            f"Attempt to update placeholder '{placeholder_id}', but not found in paragraph: {paragraph.text}")
        return

    logging.debug(f"Replacing: {placeholder_id} with \"{replacement_text}\". New text: {run_with_placeholder.text}")
    run_with_placeholder.text = run_with_placeholder.text.replace(placeholder_id, replacement_text)

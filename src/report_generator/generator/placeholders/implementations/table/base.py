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
from abc import ABC
from typing import Union

from report_generator.generator.placeholders import Placeholder
from report_generator.generator.placeholders.base import PlaceholderDocType
from report_generator.generator.report_utils.pptx import find_tables, update_table

TableMatrix = list[list[Union[str, int, float]]]


class TablePlaceholder(Placeholder, ABC):
    __doc_type__ = PlaceholderDocType.TABLE

    @classmethod
    def resolve_pptx(cls, presentation, key: str, value_cb):
        tables = find_tables(presentation, key)

        logging.debug(f"Finds for {key}: {len(tables)}")
        if len(tables) == 0:
            return

        value = value_cb()
        if value is None:
            raise ValueError(f"Value for placeholder '{key}' is None")

        for table in tables:
            update_table(table, value)

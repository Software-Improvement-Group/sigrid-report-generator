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

from report_generator.generator.domain import team_report_data
from report_generator.generator.placeholders.implementations.table.base import (
    TableMatrix,
    TablePlaceholder,
)
from report_generator.generator.placeholders.rendering.pptx import (
    delete_slides_with_placeholder,
)

_HEADER = ["Systeem", "Repo's"]
# Number of system rows in each table of the template; the report has a table per slide.
_ROWS_PER_SLIDE = 24


def _systems_page(page: int) -> TableMatrix:
    first = page * _ROWS_PER_SLIDE
    systems = team_report_data.systems_by_volume[first : first + _ROWS_PER_SLIDE]
    return [_HEADER] + [[system["displayName"], ""] for system in systems]


class TeamSystemsTable(TablePlaceholder):
    """Table of the team's systems, largest first, first 24. Headers are: Systeem, Repo's."""

    key = "TEAM_SYSTEMS_TABLE"

    @classmethod
    def value(cls) -> TableMatrix:
        return _systems_page(0)


class TeamSystemsTableContinued(TablePlaceholder):
    """Continuation of the team's systems table (systems 25 to 48). The slide with this table is dropped when the team has 24 systems or fewer."""

    key = "TEAM_SYSTEMS_TABLE_2"

    @classmethod
    def resolve_pptx(cls, presentation, key: str, value_cb):
        if len(value_cb()) <= 1:
            delete_slides_with_placeholder(
                presentation, key, reason="the team has no further systems"
            )
            return
        super().resolve_pptx(presentation, key, value_cb)

    @classmethod
    def value(cls) -> TableMatrix:
        return _systems_page(1)

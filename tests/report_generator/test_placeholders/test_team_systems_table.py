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

from pathlib import Path
from unittest.mock import PropertyMock

import pytest
from pptx import Presentation

from report_generator import presets
from report_generator.generator.placeholders.implementations.table import team_systems
from report_generator.generator.placeholders.implementations.table.team_systems import (
    TeamSystemsTable,
    TeamSystemsTableContinued,
)
from report_generator.generator.placeholders.rendering.pptx import find_tables

A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
FIRST_FILL = "CCDCEA"
SECOND_FILL = "E8EFF5"
ROWS_PER_SLIDE = 24


@pytest.fixture
def team_systems_data(mocker):
    def set_systems(count):
        systems = [
            {"system": f"s{i}", "displayName": f"Systeem {i}"} for i in range(count)
        ]
        mocker.patch.object(
            type(team_systems.team_report_data),
            "systems_by_volume",
            new_callable=PropertyMock,
            return_value=systems,
        )

    return set_systems


def _template():
    return Presentation(
        str(Path(presets.__file__).parent / "templates" / "simple-basic-data.pptx")
    )


def _fill_of_row(row):
    return row.tc_lst[0].find(f"{A_NS}tcPr").find(f"{A_NS}solidFill")[0].get("val")


class TestTableValues:
    def test_first_table_has_a_header_and_the_first_systems(self, team_systems_data):
        team_systems_data(30)
        value = TeamSystemsTable.value()
        assert value[0] == ["Systeem", "Repo's"]
        assert len(value) == 1 + ROWS_PER_SLIDE
        assert value[1] == ["Systeem 0", ""]
        assert value[-1] == ["Systeem 23", ""]

    def test_continuation_has_the_next_systems(self, team_systems_data):
        team_systems_data(30)
        value = TeamSystemsTableContinued.value()
        assert value[0] == ["Systeem", "Repo's"]
        assert [row[0] for row in value[1:]] == [f"Systeem {i}" for i in range(24, 30)]

    def test_a_small_team_has_an_empty_continuation(self, team_systems_data):
        team_systems_data(5)
        assert len(TeamSystemsTable.value()) == 6
        assert TeamSystemsTableContinued.value() == [["Systeem", "Repo's"]]


class TestTemplate:
    def test_template_tables_have_room_for_the_rows_per_slide(self):
        presentation = _template()
        for key in ("TEAM_SYSTEMS_TABLE", "TEAM_SYSTEMS_TABLE_2"):
            (table,) = find_tables(presentation, key)
            assert len(table.rows) == 1 + ROWS_PER_SLIDE

    def test_rows_alternate_between_the_two_fills_in_both_tables(self):
        presentation = _template()
        for key in ("TEAM_SYSTEMS_TABLE", "TEAM_SYSTEMS_TABLE_2"):
            (table,) = find_tables(presentation, key)
            fills = [_fill_of_row(row) for row in table._tbl.tr_lst[1:]]
            assert fills == [
                FIRST_FILL if i % 2 == 0 else SECOND_FILL for i in range(len(fills))
            ]


class TestReport:
    def _resolve(self, team_systems_data, count):
        team_systems_data(count)
        presentation = _template()
        for placeholder in (TeamSystemsTable, TeamSystemsTableContinued):
            placeholder.resolve_pptx(presentation, placeholder.key, placeholder.value)
        return presentation

    def _tables(self, presentation):
        return {
            shape.name: shape.table
            for slide in presentation.slides
            for shape in slide.shapes
            if shape.has_table and shape.name.startswith("TEAM_SYSTEMS_TABLE")
        }

    def test_many_systems_fill_both_slides(self, team_systems_data):
        presentation = self._resolve(team_systems_data, 38)
        tables = self._tables(presentation)
        assert len(tables["TEAM_SYSTEMS_TABLE"].rows) == 1 + 24
        assert len(tables["TEAM_SYSTEMS_TABLE_2"].rows) == 1 + 14
        assert len(presentation.slides) == 5

    def test_few_systems_drop_the_continuation_slide(self, team_systems_data):
        presentation = self._resolve(team_systems_data, 10)
        assert list(self._tables(presentation)) == ["TEAM_SYSTEMS_TABLE"]
        assert len(presentation.slides) == 4

    def test_exactly_one_slide_of_systems_drops_the_continuation_slide(
        self, team_systems_data
    ):
        presentation = self._resolve(team_systems_data, ROWS_PER_SLIDE)
        assert list(self._tables(presentation)) == ["TEAM_SYSTEMS_TABLE"]
        assert len(presentation.slides) == 4

    @pytest.mark.parametrize("count", [3, 24, 38])
    def test_colours_keep_alternating_whatever_the_number_of_systems(
        self, team_systems_data, count
    ):
        presentation = self._resolve(team_systems_data, count)
        for table in self._tables(presentation).values():
            fills = [_fill_of_row(row) for row in table._tbl.tr_lst[1:]]
            assert fills == [
                FIRST_FILL if i % 2 == 0 else SECOND_FILL for i in range(len(fills))
            ]

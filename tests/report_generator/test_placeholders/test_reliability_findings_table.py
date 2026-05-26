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

import pytest
from unittest.mock import PropertyMock

from report_generator.generator.context import sigrid_api
from report_generator.generator.domain import reliability_ratings_portfolio_data
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.table.reliability_findings import (
    ReliabilityFindingsTopSystemsTable,
)
from report_generator.generator.placeholders.rendering.pptx import Hyperlink


@pytest.fixture(autouse=True)
def set_customer(monkeypatch):
    monkeypatch.setattr(sigrid_api, "_customer", "test-customer")
    monkeypatch.setattr(formatters, "_USE_SIG_STERREN", False)


def _mock_top_systems(mocker, systems):
    mocker.patch.object(
        type(reliability_ratings_portfolio_data),
        "top_systems_by_findings_above_objective",
        new_callable=PropertyMock,
        return_value=systems,
    )


class TestReliabilityFindingsTopSystemsTable:
    def test_header_row(self, mocker):
        _mock_top_systems(mocker, [])
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[0] == [
            "System",
            "Objective set",
            "Findings above objective",
            "Rating",
            "Sigrid Link",
        ]

    def test_data_rows_are_in_order(self, mocker):
        systems = [
            {"systemName": "alpha", "displayName": "Alpha", "findings_above_objective": 10, "rating": 3.5},
            {"systemName": "beta", "displayName": "Beta", "findings_above_objective": 5, "rating": 2.0},
        ]
        _mock_top_systems(mocker, systems)
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[1][0] == "Alpha"
        assert result[2][0] == "Beta"

    def test_finding_count_in_row(self, mocker):
        systems = [
            {"systemName": "alpha", "displayName": "Alpha", "findings_above_objective": 10, "rating": 3.5},
        ]
        _mock_top_systems(mocker, systems)
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[1][2] == 10

    def test_star_rating_in_row(self, mocker):
        systems = [
            {
                "systemName": "alpha",
                "displayName": "Alpha",
                "findings_above_objective": 10,
                "rating": 3.5,
                "objective_target": None,
            },
        ]
        _mock_top_systems(mocker, systems)
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[1][3] == "3.5★"

    def test_link_url_format(self, mocker):
        systems = [
            {
                "systemName": "my-system",
                "displayName": "My System",
                "findings_above_objective": 3,
                "rating": 4.0,
                "objective_target": None,
            },
        ]
        _mock_top_systems(mocker, systems)
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[1][4] == Hyperlink(
            "link", "https://sigrid-says.com/test-customer/my-system/-/reliability"
        )

    def test_none_rating_shows_na(self, mocker):
        systems = [
            {
                "systemName": "alpha",
                "displayName": "Alpha",
                "findings_above_objective": 5,
                "rating": None,
                "objective_target": None,
            },
        ]
        _mock_top_systems(mocker, systems)
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[1][3] == "N/A"

    def test_objective_set_with_target(self, mocker):
        systems = [
            {
                "systemName": "alpha",
                "displayName": "Alpha",
                "findings_above_objective": 5,
                "rating": 3.0,
                "objective_target": "HIGH",
            },
        ]
        _mock_top_systems(mocker, systems)
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[1][1] == "≥ High"

    def test_objective_set_none_shows_na(self, mocker):
        systems = [
            {
                "systemName": "alpha",
                "displayName": "Alpha",
                "findings_above_objective": 5,
                "rating": 3.0,
                "objective_target": None,
            },
        ]
        _mock_top_systems(mocker, systems)
        result = ReliabilityFindingsTopSystemsTable.value()
        assert result[1][1] == "N/A"

    def test_empty_systems_returns_header_only(self, mocker):
        _mock_top_systems(mocker, [])
        result = ReliabilityFindingsTopSystemsTable.value()
        assert len(result) == 1

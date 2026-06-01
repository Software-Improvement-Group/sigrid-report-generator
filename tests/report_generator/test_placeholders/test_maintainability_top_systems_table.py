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

from unittest.mock import PropertyMock

import pytest

from report_generator.generator.context import config
from report_generator.generator.domain import maintainability_portfolio_data
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.table.maintainability_top_systems import (
    MaintainabilityTopSystemsTable,
)
from report_generator.generator.placeholders.rendering.pptx import Hyperlink


@pytest.fixture(autouse=True)
def set_customer(monkeypatch):
    monkeypatch.setattr(config, "_customer", "test-customer")
    monkeypatch.setattr(formatters, "_USE_SIG_STERREN", False)


def _mock_bottom_systems(mocker, systems):
    mocker.patch.object(
        type(maintainability_portfolio_data),
        "bottom_systems_by_maintainability_rating",
        new_callable=PropertyMock,
        return_value=systems,
    )


class TestMaintainabilityTopSystemsTable:
    def test_header_row(self, mocker):
        _mock_bottom_systems(mocker, [])
        result = MaintainabilityTopSystemsTable.value()
        assert result[0] == [
            "System",
            "Maintainability Rating",
            "Volume (in PY)",
            "Sigrid Link",
        ]

    def test_data_rows_are_in_order(self, mocker):
        systems = [
            {
                "systemName": "alpha",
                "displayName": "Alpha",
                "rating": 1.5,
                "volume_py": 2.0,
            },
            {
                "systemName": "beta",
                "displayName": "Beta",
                "rating": 2.0,
                "volume_py": 1.0,
            },
        ]
        _mock_bottom_systems(mocker, systems)
        result = MaintainabilityTopSystemsTable.value()
        assert result[1][0] == "Alpha"
        assert result[2][0] == "Beta"

    def test_display_name_used(self, mocker):
        systems = [
            {
                "systemName": "my-system",
                "displayName": "My System",
                "rating": 2.0,
                "volume_py": 3.0,
            },
        ]
        _mock_bottom_systems(mocker, systems)
        result = MaintainabilityTopSystemsTable.value()
        assert result[1][0] == "My System"

    def test_rating_format(self, mocker):
        systems = [
            {
                "systemName": "alpha",
                "displayName": "Alpha",
                "rating": 2.5,
                "volume_py": 1.0,
            },
        ]
        _mock_bottom_systems(mocker, systems)
        result = MaintainabilityTopSystemsTable.value()
        assert result[1][1] == "2.5★"

    def test_volume_in_row(self, mocker):
        systems = [
            {
                "systemName": "alpha",
                "displayName": "Alpha",
                "rating": 2.0,
                "volume_py": 4.2,
            },
        ]
        _mock_bottom_systems(mocker, systems)
        result = MaintainabilityTopSystemsTable.value()
        assert result[1][2] == 4.2

    def test_link_url_format(self, mocker):
        systems = [
            {
                "systemName": "my-system",
                "displayName": "My System",
                "rating": 2.0,
                "volume_py": 1.0,
            },
        ]
        _mock_bottom_systems(mocker, systems)
        result = MaintainabilityTopSystemsTable.value()
        assert result[1][3] == Hyperlink(
            "link", "https://sigrid-says.com/test-customer/my-system/-/maintainability"
        )

    def test_empty_systems_returns_header_only(self, mocker):
        _mock_bottom_systems(mocker, [])
        result = MaintainabilityTopSystemsTable.value()
        assert len(result) == 1

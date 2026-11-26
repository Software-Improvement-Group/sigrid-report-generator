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

from unittest.mock import MagicMock

import pytest

from report_generator.generator.placeholders.implementations import (
    placeholders as all_placeholders,
)
from report_generator.generator.placeholders.implementations.text import team_report

PLACEHOLDERS = {placeholder.key: placeholder for placeholder in all_placeholders}
MODULES = ["MAINTAINABILITY", "ARCHITECTURE", "OPEN_SOURCE_HEALTH", "SECURITY"]
COLUMNS = ["WAS", "IS", "DELTA", "MARKT", "DOEL"]


def _value(key):
    return PLACEHOLDERS[key].value()


@pytest.fixture
def data(mocker):
    """The team's domain data, with a period of 1 January to 11 November 2026."""
    data = mocker.patch.object(team_report, "team_report_data", MagicMock())
    data.period = ("2026-01-01", "2026-11-11")
    return data


class TestRegistration:
    @pytest.mark.parametrize(
        "key", [f"{module}_{column}" for module in MODULES for column in COLUMNS]
    )
    def test_every_cell_of_the_rating_table_is_a_placeholder(self, key):
        assert key in PLACEHOLDERS

    @pytest.mark.parametrize(
        "key",
        [
            "TEAM_NAME",
            "TEAM_REPORT_PERIOD",
            "TEAM_SYSTEMS_TABLE",
            "TEAM_SYSTEMS_TABLE_2",
        ],
    )
    def test_team_placeholders_are_registered(self, key):
        assert key in PLACEHOLDERS

    @pytest.mark.parametrize("key", [f"{m}_WAS" for m in MODULES])
    def test_placeholders_have_a_description(self, key):
        assert PLACEHOLDERS[key].__doc__


class TestTeamName:
    def test_is_the_first_team_of_the_filter(self, mocker):
        mocker.patch.object(team_report, "get_filter_values", return_value=["Platform"])
        assert _value("TEAM_NAME") == "Platform"

    def test_falls_back_to_team_without_filter(self, mocker):
        mocker.patch.object(team_report, "get_filter_values", return_value=None)
        assert _value("TEAM_NAME") == "Team"


class TestPeriod:
    def test_writes_both_dates_in_dutch(self, data):
        assert _value("TEAM_REPORT_PERIOD") == "1 januari 2026 - 11 november 2026"

    @pytest.mark.parametrize(
        "date, expected",
        [
            ("2026-03-05", "5 maart 2026"),
            ("2026-05-31", "31 mei 2026"),
            ("2026-12-01", "1 december 2026"),
        ],
    )
    def test_dutch_month_names(self, date, expected):
        assert team_report._dutch_date(date) == expected


class TestDeltaText:
    @pytest.mark.parametrize(
        "was, is_, expected",
        [
            (3.5, 3.5, "Gelijk"),
            (3.51, 3.59, "Gelijk"),  # both show as 3.5
            (3.5, 3.6, "Hoger"),
            (3.59, 3.6, "Hoger"),
            (3.5, 3.49, "Lager"),
            (4.7, 4.9, "Hoger"),
        ],
    )
    def test_compares_the_ratings_as_shown(self, was, is_, expected):
        assert team_report._delta_text(was, is_) == expected

    @pytest.mark.parametrize("was, is_", [(0, 3.5), (3.5, 0), (0, 0)])
    def test_is_empty_when_a_rating_is_missing(self, was, is_):
        assert team_report._delta_text(was, is_) == ""


class TestMarketText:
    @pytest.mark.parametrize(
        "rating, expected",
        [
            (1.0, "Onder"),
            (2.49, "Onder"),
            (2.5, "Op"),
            (3.0, "Op"),
            (3.4, "Op"),
            (3.49, "Op"),  # shows as 3.4
            (3.5, "Boven"),
            (4.9, "Boven"),
        ],
    )
    def test_compares_the_rating_as_shown_with_market_average(self, rating, expected):
        assert team_report._market_text(rating) == expected

    def test_is_empty_without_a_rating(self):
        assert team_report._market_text(0) == ""


class TestRatingTable:
    def test_was_and_is_use_the_start_and_end_of_the_period(self, data):
        data.maintainability_rating.side_effect = lambda date: {
            "2026-01-01": 3.59,
            "2026-11-11": 3.1,
        }[date]
        assert _value("MAINTAINABILITY_WAS") == "3.5"
        assert _value("MAINTAINABILITY_IS") == "3.1"

    def test_ratings_are_truncated_like_sigrid_does(self, data):
        data.security_rating.return_value = 4.7999
        assert _value("SECURITY_IS") == "4.7"

    def test_each_module_reads_its_own_rating(self, data):
        data.maintainability_rating.return_value = 1.1
        data.architecture_rating.return_value = 2.2
        data.security_rating.return_value = 3.3
        data.open_source_health_rating = 4.4
        assert [_value(f"{module}_IS") for module in MODULES] == [
            "1.1",
            "2.2",
            "4.4",
            "3.3",
        ]

    def test_a_missing_rating_leaves_the_cell_empty(self, data):
        data.architecture_rating.return_value = 0
        assert _value("ARCHITECTURE_WAS") == ""
        assert _value("ARCHITECTURE_IS") == ""

    def test_delta_and_market_follow_the_ratings(self, data):
        data.security_rating.side_effect = lambda date: {
            "2026-01-01": 4.7,
            "2026-11-11": 4.9,
        }[date]
        assert _value("SECURITY_DELTA") == "Hoger"
        assert _value("SECURITY_MARKT") == "Boven"

    @pytest.mark.parametrize(
        "met, expected", [(True, "Ja"), (False, "Nee"), (None, "")]
    )
    def test_objectives_are_ja_nee_or_empty(self, data, met, expected):
        data.objectives_met.return_value = met
        assert _value("ARCHITECTURE_DOEL") == expected

    @pytest.mark.parametrize(
        "module, feature",
        [
            ("MAINTAINABILITY", "MAINTAINABILITY"),
            ("ARCHITECTURE", "ARCHITECTURE_QUALITY"),
            ("OPEN_SOURCE_HEALTH", "OPEN_SOURCE_HEALTH"),
            ("SECURITY", "SECURITY"),
        ],
    )
    def test_objectives_are_asked_for_the_matching_feature(self, data, module, feature):
        data.objectives_met.return_value = True
        _value(f"{module}_DOEL")
        data.objectives_met.assert_called_once_with(feature)


class TestOpenSourceHealthHasNoHistory:
    def test_was_and_delta_are_empty_without_asking_for_a_rating(self, data):
        assert _value("OPEN_SOURCE_HEALTH_WAS") == ""
        assert _value("OPEN_SOURCE_HEALTH_DELTA") == ""

    def test_is_and_market_use_the_current_rating(self, data):
        data.open_source_health_rating = 4.5
        assert _value("OPEN_SOURCE_HEALTH_IS") == "4.5"
        assert _value("OPEN_SOURCE_HEALTH_MARKT") == "Boven"

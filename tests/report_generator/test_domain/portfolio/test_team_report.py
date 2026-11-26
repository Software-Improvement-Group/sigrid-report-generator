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

from report_generator.generator.domain.portfolio import team_report
from report_generator.generator.domain.portfolio.team_report import TeamReportData

PERIOD = ("2026-01-01", "2026-11-11")


def _system(name, rating, date, volume, history=()):
    return {
        "system": name,
        "maintainability": rating,
        "maintainabilityDate": date,
        "volumeInPersonMonths": volume,
        "allRatings": [
            {
                "maintainability": old_rating,
                "maintainabilityDate": old_date,
                "volumeInPersonMonths": volume,
            }
            for old_date, old_rating in history
        ],
    }


@pytest.fixture
def api(mocker):
    api = mocker.patch.object(team_report, "sigrid_api")
    api.get_period.return_value = PERIOD
    api.get_portfolio_maintainability.return_value = {"systems": []}
    api.get_portfolio_metadata.return_value = []
    return api


@pytest.fixture
def team_filter(mocker):
    return mocker.patch.object(
        team_report, "get_filter_values", return_value=["Platform"]
    )


def _with_team_systems(api, systems, metadata):
    api.get_portfolio_maintainability.return_value = {"systems": systems}
    api.get_portfolio_metadata.return_value = metadata


class TestTeamSystems:
    def test_keeps_only_systems_of_the_team(self, api, team_filter):
        _with_team_systems(
            api,
            [_system("a", 3.0, "2026-10-01", 10), _system("b", 4.0, "2026-10-01", 20)],
            [
                {"systemName": "a", "teamNames": ["Platform"]},
                {"systemName": "b", "teamNames": ["Other"]},
            ],
        )
        assert [s["system"] for s in TeamReportData().systems] == ["a"]

    def test_team_match_is_case_insensitive_and_includes_shared_systems(
        self, api, team_filter
    ):
        _with_team_systems(
            api,
            [_system("a", 3.0, "2026-10-01", 10)],
            [{"systemName": "a", "teamNames": ["Product", "PLATFORM"]}],
        )
        assert len(TeamReportData().systems) == 1

    def test_team_name_must_match_exactly(self, api, team_filter):
        _with_team_systems(
            api,
            [_system("a", 3.0, "2026-10-01", 10)],
            [{"systemName": "a", "teamNames": ["Platform Engineering"]}],
        )
        assert TeamReportData().systems == []

    def test_systems_missing_from_metadata_are_skipped(self, api, team_filter):
        _with_team_systems(api, [_system("a", 3.0, "2026-10-01", 10)], [])
        assert TeamReportData().systems == []

    def test_display_name_comes_from_metadata_with_system_name_as_fallback(
        self, api, team_filter
    ):
        _with_team_systems(
            api,
            [_system("a", 3.0, "2026-10-01", 10), _system("b", 3.0, "2026-10-01", 10)],
            [
                {"systemName": "a", "teamNames": ["Platform"], "displayName": "Alpha"},
                {"systemName": "b", "teamNames": ["Platform"]},
            ],
        )
        assert [s["displayName"] for s in TeamReportData().systems] == ["Alpha", "b"]

    def test_without_team_filter_all_systems_are_returned(self, api, mocker):
        mocker.patch.object(team_report, "get_filter_values", return_value=None)
        api.get_portfolio_maintainability.return_value = {
            "systems": [_system("a", 3.0, "2026-10-01", 10)]
        }
        assert [s["displayName"] for s in TeamReportData().systems] == ["a"]

    def test_source_data_is_not_modified(self, api, team_filter):
        source = _system("a", 3.0, "2026-10-01", 10)
        _with_team_systems(
            api, [source], [{"systemName": "a", "teamNames": ["Platform"]}]
        )
        systems = TeamReportData().systems
        assert systems[0]["displayName"] == "a"
        assert "displayName" not in source

    def test_systems_by_volume_puts_the_largest_first(self, api, team_filter):
        _with_team_systems(
            api,
            [
                _system("small", 3.0, "2026-10-01", 1),
                _system("large", 3.0, "2026-10-01", 50),
                _system("medium", 3.0, "2026-10-01", 10),
            ],
            [
                {"systemName": name, "teamNames": ["Platform"]}
                for name in ("small", "large", "medium")
            ],
        )
        assert [s["system"] for s in TeamReportData().systems_by_volume] == [
            "large",
            "medium",
            "small",
        ]


def _team_with_systems(mocker, systems):
    data = TeamReportData()
    data.__dict__["systems"] = systems
    return data


class TestMaintainabilityRating:
    def test_is_the_volume_weighted_average(self, api, mocker):
        data = _team_with_systems(
            mocker,
            [_system("a", 4.0, "2026-10-01", 10), _system("b", 3.0, "2026-10-01", 90)],
        )
        assert data.maintainability_rating("2026-11-11") == pytest.approx(3.1)

    def test_uses_the_latest_snapshot_on_or_before_the_date(self, api, mocker):
        # Ratings go up and down, so the latest snapshot is not the highest or lowest one.
        data = _team_with_systems(
            mocker,
            [
                _system(
                    "a",
                    3.0,
                    "2026-10-01",
                    10,
                    history=[("2026-01-01", 4.0), ("2026-06-01", 2.0)],
                )
            ],
        )
        assert data.maintainability_rating("2025-12-31") == 0
        assert data.maintainability_rating("2026-01-01") == pytest.approx(4.0)
        assert data.maintainability_rating("2026-05-31") == pytest.approx(4.0)
        assert data.maintainability_rating("2026-06-01") == pytest.approx(2.0)
        assert data.maintainability_rating("2026-11-11") == pytest.approx(3.0)

    def test_systems_without_a_snapshot_yet_are_left_out(self, api, mocker):
        data = _team_with_systems(
            mocker,
            [
                _system("old", 3.0, "2026-10-01", 10, history=[("2025-06-01", 2.0)]),
                _system("new", 5.0, "2026-10-01", 90),
            ],
        )
        assert data.maintainability_rating("2026-01-01") == pytest.approx(2.0)

    def test_no_rated_systems_gives_zero(self, api, mocker):
        assert _team_with_systems(mocker, []).maintainability_rating("2026-01-01") == 0


class TestListedRatings:
    def test_architecture_counts_only_team_systems_weighted_by_volume(
        self, api, mocker
    ):
        data = _team_with_systems(
            mocker,
            [_system("a", 0, "2026-10-01", 10), _system("b", 0, "2026-10-01", 90)],
        )
        api.get_portfolio_architecture_findings.return_value = [
            {"system": "a", "ratings": {"architecture": 4.0}},
            {"system": "b", "ratings": {"architecture": 3.0}},
            {"system": "outsider", "ratings": {"architecture": 1.0}},
        ]
        assert data.architecture_rating("2026-11-11") == pytest.approx(3.1)
        api.get_portfolio_architecture_findings.assert_called_once_with(
            end_date="2026-11-11"
        )

    def test_architecture_skips_systems_without_a_rating(self, api, mocker):
        data = _team_with_systems(
            mocker,
            [_system("a", 0, "2026-10-01", 10), _system("b", 0, "2026-10-01", 90)],
        )
        api.get_portfolio_architecture_findings.return_value = [
            {"system": "a", "ratings": {"architecture": 4.0}},
            {"system": "b", "ratings": {}},
        ]
        assert data.architecture_rating("2026-11-11") == pytest.approx(4.0)

    def test_security_counts_only_team_systems_weighted_by_volume(self, api, mocker):
        data = _team_with_systems(
            mocker,
            [_system("a", 0, "2026-10-01", 30), _system("b", 0, "2026-10-01", 10)],
        )
        api.get_portfolio_security_ratings.return_value = [
            {"systemName": "a", "rating": 5.0},
            {"systemName": "b", "rating": 3.0},
            {"systemName": "outsider", "rating": 1.0},
        ]
        assert data.security_rating("2026-01-01") == pytest.approx(4.5)
        api.get_portfolio_security_ratings.assert_called_once_with(
            end_date="2026-01-01"
        )

    @pytest.mark.parametrize("response", [None, {}, "error"])
    def test_an_unexpected_response_gives_zero(self, api, mocker, response):
        data = _team_with_systems(mocker, [_system("a", 0, "2026-10-01", 10)])
        api.get_portfolio_security_ratings.return_value = response
        api.get_portfolio_architecture_findings.return_value = response
        assert data.security_rating("2026-01-01") == 0
        assert data.architecture_rating("2026-01-01") == 0

    def test_open_source_health_comes_from_the_osh_portfolio(self, mocker):
        mocker.patch.object(
            type(team_report.osh_portfolio_data),
            "weighted_average_rating",
            new_callable=PropertyMock,
            return_value=4.4,
        )
        assert TeamReportData().open_source_health_rating == 4.4


def _evaluation(*systems):
    return {
        "systems": [
            {
                "systemName": name,
                "objectives": [
                    {"feature": feature, "targetMetAtEnd": outcome}
                    for feature, outcome in objectives
                ],
            }
            for name, objectives in systems
        ]
    }


class TestObjectivesMet:
    def _data(self, api, mocker, evaluation):
        api.get_objectives_evaluation.return_value = evaluation
        return _team_with_systems(
            mocker,
            [_system("a", 0, "2026-10-01", 10), _system("b", 0, "2026-10-01", 10)],
        )

    def test_true_when_every_team_objective_is_met(self, api, mocker):
        data = self._data(
            api,
            mocker,
            _evaluation(
                ("a", [("SECURITY", "MET")]),
                ("b", [("SECURITY", "MET")]),
            ),
        )
        assert data.objectives_met("SECURITY") is True

    @pytest.mark.parametrize("outcome", ["NOT_MET", "UNMET"])
    def test_false_when_one_objective_is_not_met(self, api, mocker, outcome):
        data = self._data(
            api,
            mocker,
            _evaluation(
                ("a", [("SECURITY", "MET")]),
                ("b", [("SECURITY", outcome)]),
            ),
        )
        assert data.objectives_met("SECURITY") is False

    def test_unknown_outcomes_are_ignored(self, api, mocker):
        data = self._data(
            api,
            mocker,
            _evaluation(
                ("a", [("SECURITY", "MET")]),
                ("b", [("SECURITY", "UNKNOWN")]),
            ),
        )
        assert data.objectives_met("SECURITY") is True

    def test_none_when_no_outcome_is_known(self, api, mocker):
        data = self._data(api, mocker, _evaluation(("a", [("SECURITY", "UNKNOWN")])))
        assert data.objectives_met("SECURITY") is None

    def test_none_when_the_team_has_no_objective_of_that_feature(self, api, mocker):
        data = self._data(api, mocker, _evaluation(("a", [("MAINTAINABILITY", "MET")])))
        assert data.objectives_met("SECURITY") is None

    def test_systems_of_other_teams_are_ignored(self, api, mocker):
        data = self._data(
            api,
            mocker,
            _evaluation(
                ("a", [("SECURITY", "MET")]),
                ("outsider", [("SECURITY", "NOT_MET")]),
            ),
        )
        assert data.objectives_met("SECURITY") is True

    def test_the_evaluation_covers_the_reporting_period(self, api, mocker):
        data = self._data(api, mocker, _evaluation())
        data.objectives_met("SECURITY")
        period = api.get_objectives_evaluation.call_args.args[0]
        assert (
            period.start.strftime("%Y-%m-%d"),
            period.end.strftime("%Y-%m-%d"),
        ) == PERIOD

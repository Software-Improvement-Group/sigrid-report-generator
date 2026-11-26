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

from functools import cached_property

from report_generator.generator.context import sigrid_api
from report_generator.generator.context.portfolio_filters import get_filter_values
from report_generator.generator.domain.portfolio.osh_portfolio import osh_portfolio_data
from report_generator.generator.domain.portfolio.shared.utils import (
    calculate_weighted_average_rating,
)
from report_generator.generator.utils.time_series import Period

_KNOWN_OBJECTIVE_OUTCOMES = ("MET", "NOT_MET", "UNMET")


def _belongs_to_team(metadata: dict, team_filter: list[str]) -> bool:
    team_names = {name.lower() for name in metadata.get("teamNames", [])}
    return any(team.lower() in team_names for team in team_filter)


def _snapshot_on_date(system: dict, date: str) -> dict | None:
    """The system's latest rating snapshot on or before date (YYYY-MM-DD), if any."""
    candidates = [
        snapshot
        for snapshot in [*system.get("allRatings", []), system]
        if snapshot.get("maintainabilityDate")
        and snapshot["maintainabilityDate"] <= date
    ]
    return max(candidates, key=lambda s: s["maintainabilityDate"], default=None)


class TeamReportData:
    """The systems of one team, and their ratings at the start and end of the period.

    All averages are weighted by the system's volume in person months, like Sigrid does.
    """

    @property
    def period(self) -> tuple[str, str]:
        return sigrid_api.get_period()

    @cached_property
    def systems(self) -> list[dict]:
        """The team's systems, each with a displayName. Without a team filter: all systems."""
        portfolio = sigrid_api.get_portfolio_maintainability()
        systems = portfolio.get("systems", []) if isinstance(portfolio, dict) else []
        team_filter = get_filter_values("team")
        if not team_filter:
            return [self._with_display_name(system, {}) for system in systems]

        metadata_by_name = {
            metadata["systemName"]: metadata
            for metadata in sigrid_api.get_portfolio_metadata()
        }
        return [
            self._with_display_name(system, metadata_by_name[system.get("system")])
            for system in systems
            if system.get("system") in metadata_by_name
            and _belongs_to_team(metadata_by_name[system["system"]], team_filter)
        ]

    @staticmethod
    def _with_display_name(system: dict, metadata: dict) -> dict:
        name = system.get("system", "")
        return {**system, "displayName": metadata.get("displayName") or name}

    @cached_property
    def systems_by_volume(self) -> list[dict]:
        """The team's systems, largest first."""
        return sorted(
            self.systems,
            key=lambda system: system.get("volumeInPersonMonths", 0),
            reverse=True,
        )

    def maintainability_rating(self, date: str) -> float:
        """Average maintainability of the team's systems on date; 0 when none is rated."""

        def rating_and_volume(system):
            snapshot = _snapshot_on_date(system, date)
            if snapshot is None:
                return None, 0
            return snapshot.get("maintainability"), snapshot.get(
                "volumeInPersonMonths", 0
            )

        return calculate_weighted_average_rating(self.systems, rating_and_volume)

    def architecture_rating(self, date: str) -> float:
        """Average architecture quality of the team's systems on date; 0 when none is rated."""
        ratings = sigrid_api.get_portfolio_architecture_findings(end_date=date)
        return self._average_of_listed_ratings(
            ratings, "system", lambda item: item.get("ratings", {}).get("architecture")
        )

    def security_rating(self, date: str) -> float:
        """Average security rating of the team's systems on date; 0 when none is rated."""
        ratings = sigrid_api.get_portfolio_security_ratings(end_date=date)
        return self._average_of_listed_ratings(
            ratings, "systemName", lambda item: item.get("rating")
        )

    @property
    def open_source_health_rating(self) -> float:
        """Average open source health of the team's systems. The API has only the current state."""
        return osh_portfolio_data.weighted_average_rating

    def _average_of_listed_ratings(self, ratings, name_key: str, rating_of) -> float:
        if not isinstance(ratings, list):
            return 0.0
        volumes = {
            system.get("system"): system.get("volumeInPersonMonths", 0)
            for system in self.systems
        }

        def rating_and_volume(item):
            name = item.get(name_key)
            rating = rating_of(item)
            if name not in volumes or rating is None:
                return None, 0
            return rating, volumes[name]

        return calculate_weighted_average_rating(ratings, rating_and_volume)

    def objectives_met(self, feature: str) -> bool | None:
        """Whether all of the team's objectives for this feature are met at the end of the
        period. Objectives with an unknown status are ignored; None when none is known.
        """
        start, end = self.period
        evaluation = sigrid_api.get_objectives_evaluation(Period(start, end))
        team_names = {system.get("system") for system in self.systems}
        systems = evaluation.get("systems", []) if isinstance(evaluation, dict) else []
        outcomes = [
            objective.get("targetMetAtEnd")
            for system in systems
            if system.get("systemName") in team_names
            for objective in system.get("objectives", [])
            if objective.get("feature") == feature
        ]
        known = [
            outcome for outcome in outcomes if outcome in _KNOWN_OBJECTIVE_OUTCOMES
        ]
        if not known:
            return None
        return all(outcome == "MET" for outcome in known)


team_report_data = TeamReportData()

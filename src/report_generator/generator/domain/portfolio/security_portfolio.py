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

from report_generator.generator.context import config, sigrid_api
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared import utils
from report_generator.generator.domain.portfolio.shared.findings_portfolio_base import (
    FindingsRatingsPortfolioBase,
)


class SecurityRatingsPortfolioData(FindingsRatingsPortfolioBase):
    _objective_type = "SECURITY_MAX_SEVERITY"
    _portfolio_ratings_api_method = "get_portfolio_security_ratings"
    _findings_api_method = "get_security_findings"

    @property
    def security_findings(self):
        return self._raw_findings


security_ratings_portfolio_data = SecurityRatingsPortfolioData()


class SecurityRatingsChangePortfolioData:
    """Per-system change in security rating between the start and end of the reporting period.

    The security ``model-ratings`` endpoint is point-in-time, so the delta is obtained by
    requesting the ratings at both period boundaries (via the ``endDate`` parameter) and
    subtracting.
    """

    @property
    def customer(self) -> str:
        return config.get_customer()

    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def _start_ratings(self):
        return sigrid_api.get_portfolio_security_ratings(
            end_date=sigrid_api.get_period()[0]
        )

    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def _end_ratings(self):
        return sigrid_api.get_portfolio_security_ratings(
            end_date=sigrid_api.get_period()[1]
        )

    @staticmethod
    def _delta(start_rating, end_rating) -> float | None:
        if start_rating is None or end_rating is None:
            return None
        return end_rating - start_rating

    @cached_property
    def differences(self) -> dict[str, float | None]:
        start = {s["systemName"]: s.get("rating") for s in self._start_ratings}
        end = {s["systemName"]: s.get("rating") for s in self._end_ratings}
        return {
            name: self._delta(start.get(name), end_rating)
            for name, end_rating in end.items()
        }

    def get_difference(self, system_name: str) -> float | None:
        return self.differences.get(system_name)

    @cached_property
    def average_delta(self) -> float:
        """Portfolio-wide change in the volume-weighted average security rating over the period.

        Computed as the end-of-period volume-weighted average minus the start-of-period average,
        mirroring ``MaintainabilityPortfolioStats.average_delta`` (a delta of averages, not an
        average of per-system deltas). Returns 0.0 when no system contributes at either boundary.
        """
        return self.end_weighted_average - self.start_weighted_average

    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()

    def get_display_name(self, system_name: str) -> str:
        md = utils.get_system_metadata(self.metadata, system_name)
        if md is None:
            return system_name
        return md.get("displayName") or system_name

    @cached_property
    def _valid_differences(self) -> dict[str, float]:
        return {
            name: delta for name, delta in self.differences.items() if delta is not None
        }

    @cached_property
    def _change_counts(self) -> dict[str, int]:
        counts = {"increased": 0, "stable": 0, "decreased": 0}
        for delta in self._valid_differences.values():
            if delta > 0:
                counts["increased"] += 1
            elif delta < 0:
                counts["decreased"] += 1
            else:
                counts["stable"] += 1
        return counts

    @cached_property
    def change_distribution_percentages(self) -> dict[str, int]:
        """Percentage of systems whose security rating increased, stayed stable, or decreased."""
        counts = self._change_counts
        total = sum(counts.values())
        if total == 0:
            return counts
        return {key: round(100 * value / total) for key, value in counts.items()}

    def _biggest_mover(self, selector, keep) -> tuple[str, float] | None:
        candidates = {
            name: delta
            for name, delta in self._valid_differences.items()
            if keep(delta)
        }
        if not candidates:
            return None
        system = selector(candidates, key=candidates.get)
        return self.get_display_name(system), round(candidates[system], 1)

    @cached_property
    def biggest_increase(self) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest security rating increase."""
        return self._biggest_mover(max, lambda delta: delta > 0)

    @cached_property
    def biggest_decrease(self) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest security rating decrease."""
        return self._biggest_mover(min, lambda delta: delta < 0)

    @staticmethod
    def _rating_and_volume(system) -> tuple[float | None, float]:
        return utils.get_rating_and_volume_from_system(
            system, lambda s: s.get("rating"), "systemName"
        )

    @cached_property
    def start_weighted_average(self) -> float:
        """Volume-weighted average security rating at the start of the reporting period."""
        return utils.calculate_weighted_average_rating(
            self._start_ratings, self._rating_and_volume
        )

    @cached_property
    def end_weighted_average(self) -> float:
        """Volume-weighted average security rating at the end of the reporting period."""
        return utils.calculate_weighted_average_rating(
            self._end_ratings, self._rating_and_volume
        )


security_ratings_change_portfolio_data = SecurityRatingsChangePortfolioData()

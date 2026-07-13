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

    @staticmethod
    def _delta_and_volume(system) -> tuple[float | None, float]:
        return utils.get_rating_and_volume_from_system(
            system, lambda s: s.get("delta"), "systemName"
        )

    @cached_property
    def average_delta(self) -> float:
        """Portfolio-wide, volume-weighted average change in security rating over the period.

        Each system's rating change is weighted by its volume in person-months, mirroring the
        volume-weighted portfolio average rating. Systems that lack a rating at either period
        boundary, or whose volume is unavailable, do not contribute. Returns 0.0 when no system
        does.
        """
        changed_systems = [
            {"systemName": name, "delta": delta}
            for name, delta in self.differences.items()
            if delta is not None
        ]
        return utils.calculate_weighted_average_rating(
            changed_systems, self._delta_and_volume
        )


security_ratings_change_portfolio_data = SecurityRatingsChangePortfolioData()

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
from functools import cached_property

from report_generator.generator.context import sigrid_api
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared import utils
from report_generator.generator.domain.portfolio.shared.rated_mixin import (
    RatedPortfolioMixin,
)
from report_generator.generator.domain.shared.findings_severity import (
    count_findings_above_objective,
)
from report_generator.generator.utils.time_series import Period


def _build_objective_index(
    objectives_systems: list, objective_type: str
) -> dict[str, dict]:
    return {
        system["systemName"]: next(
            (obj for obj in system["objectives"] if obj["type"] == objective_type),
            None,
        )
        for system in objectives_systems
    }


class FindingsRatingsPortfolioBase(RatedPortfolioMixin):
    _objective_type: str = ""
    _portfolio_ratings_api_method: str = ""
    _findings_api_method: str = ""

    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()

    def get_display_name(self, system_name: str) -> str:
        md = utils.get_system_metadata(self.metadata, system_name)
        if md is None:
            return system_name
        return md.get("displayName") or system_name

    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def data(self):
        return sorted(
            getattr(sigrid_api, self._portfolio_ratings_api_method)(),
            key=lambda s: s["systemName"],
        )

    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]

    def get_system(self, system):
        return utils.get_system_helper(system, self.data, "systemName")

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data, "systemName")

    def _rated_systems(self):
        return self.data

    def _extract_rating(self, system):
        return system.get("rating")

    def _get_rating_and_volume(self, system):
        return utils.get_rating_and_volume_from_system(
            system, lambda s: s.get("rating"), "systemName"
        )

    @cached_property
    def _raw_findings(self):
        result = []
        for system_name in self.system_names:
            try:
                findings = getattr(sigrid_api, self._findings_api_method)(system_name)
            except Exception:
                logging.warning(
                    f"Could not retrieve findings for system '{system_name}'",
                    exc_info=True,
                )
                findings = []
            result.append({"systemName": system_name, "findings": findings})
        return result

    @cached_property
    def _objective_index(self) -> dict[str, dict | None]:
        period = Period(*sigrid_api.get_period())
        objectives_systems = sigrid_api.get_objectives_evaluation(period)["systems"]
        return _build_objective_index(objectives_systems, self._objective_type)

    @cached_property
    def findings_above_objective(self):
        return [
            {
                "systemName": entry["systemName"],
                "findings_above_objective": count_findings_above_objective(
                    entry["findings"],
                    self._objective_index.get(entry["systemName"]),
                ),
            }
            for entry in self._raw_findings
        ]

    @cached_property
    def top_systems_by_findings_above_objective(self) -> list[dict]:
        ratings_index = {s["systemName"]: s.get("rating") for s in self.data}
        ranked = sorted(
            self.findings_above_objective,
            key=lambda e: e["findings_above_objective"],
            reverse=True,
        )
        return [
            {
                "systemName": entry["systemName"],
                "displayName": self.get_display_name(entry["systemName"]),
                "findings_above_objective": entry["findings_above_objective"],
                "rating": ratings_index.get(entry["systemName"]),
                "objective_target": (
                    self._objective_index.get(entry["systemName"]) or {}
                ).get("target"),
            }
            for entry in ranked
        ]

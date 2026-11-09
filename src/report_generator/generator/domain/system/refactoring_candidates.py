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
from functools import lru_cache

from report_generator.generator.context import sigrid_api
from report_generator.generator.domain.system.maintainability import (
    maintainability_data,
)
from report_generator.generator.utils.constants import MaintMetric


def _get_technology_name_at_index(tech_index: int) -> str | None:
    name = maintainability_data.sorted_tech_get_key(tech_index - 1, "name", None)
    return None if name in (None, "others") else name


class RefactoringCandidatesData:
    @staticmethod
    def _get_api_data(metric: MaintMetric):
        return sigrid_api.get_maintainability_refactoring_candidates(
            system_property=metric, count=100
        )

    @lru_cache  # noqa: B019
    def get_candidates(self, metric: MaintMetric):
        return self._get_api_data(metric).get("refactoringCandidates", [])

    def get_candidates_for_technology(self, metric: MaintMetric, tech_index: int):
        """Candidates of the technology at rank `tech_index` in the system's technology
        ranking. Raises when there are none, so slides built on it are skipped."""
        name = _get_technology_name_at_index(tech_index)
        candidates = (
            [c for c in self.get_candidates(metric) if c.get("technology") == name]
            if name is not None
            else []
        )
        if not candidates:
            reason = f"No {metric} refactoring candidates for technology {tech_index}"
            raise sigrid_api.SigridAPIRequestFailedError(
                "get_maintainability_refactoring_candidates",
                message=reason,
                api_message=reason,
            )
        return candidates


refactoring_candidates_data = RefactoringCandidatesData()

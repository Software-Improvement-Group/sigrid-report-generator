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

from dataclasses import dataclass
from functools import cached_property

from report_generator.generator import sigrid_api


@dataclass
class ModernizationCandidate:
    display_name: str
    business_criticality: str
    volume_in_py: float
    maintainability_rating: float
    architecture_rating: float
    technical_debt_in_py: float
    scenario: str
    estimated_change_speed: float
    estimated_effort_py: float
    priority: float


class ModernizationData:
    MAX_SYSTEMS = 100
    MIN_DEV_SPEED_IMPROVEMENT = 5.0
    MIN_EFFORT = 0.25

    @cached_property
    def possible_candidates(self):
        return list(self.fetch_possible_candidates())

    def fetch_possible_candidates(self):
        portfolio_metadata = {metadata["systemName"]: metadata for metadata in sigrid_api.get_portfolio_metadata()}
        portfolio_maintainability = sigrid_api.get_portfolio_maintainability()

        for system in portfolio_maintainability["systems"]:
            metadata = portfolio_metadata[system["system"]]
            if metadata["active"] and not metadata["isDevelopmentOnly"]:
                yield (system, metadata)

    @cached_property
    def modernization_candidates(self):
        systems = self.possible_candidates.copy()
        systems.sort(key=lambda e: -e[0]["volumeInPersonMonths"])
        systems = systems[0:self.MAX_SYSTEMS]

        candidates = [self.to_modernization_candidate(system, metadata) for system, metadata in systems]
        candidates = [candidate for candidate in candidates if self.is_viable_candidate(candidate)]
        candidates.sort(key=lambda candidate: -candidate.priority)
        return candidates

    def to_modernization_candidate(self, system, metadata):
        return ModernizationCandidate(
            display_name=metadata.get("displayName") or metadata["systemName"],
            business_criticality=metadata.get("businessCriticality") or "unknown",
            volume_in_py=system["volumeInPersonMonths"] / 12.0,
            maintainability_rating=system["maintainability"],
            architecture_rating=0.0,
            technical_debt_in_py=0.0,
            scenario="Keep as-is",
            estimated_change_speed=0.0,
            estimated_effort_py=0.0,
            priority=0.0
        )

    def is_viable_candidate(self, candidate: ModernizationCandidate):
        #TODO
        return True
        return candidate.estimated_change_speed >= self.MIN_DEV_SPEED_IMPROVEMENT and \
            candidate.estimated_effort_py >= self.MIN_EFFORT


modernization_data = ModernizationData()

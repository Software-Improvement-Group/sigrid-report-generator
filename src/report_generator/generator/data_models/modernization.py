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
from enum import Enum
from functools import cached_property
from typing import Optional

from report_generator.generator import sigrid_api


@dataclass
class CandidateSystem:
    metadata: dict
    maintainability_data: dict


class Scenario(Enum):
    KEEP_AS_IS = "KEEP_AS_IS"
    RENOVATE = "RENOVATE"
    REBUILD = "REBUILD"
    REPLACE = "REPLACE"


@dataclass
class ModernizationCandidate:
    display_name: str
    business_criticality: str
    volume_in_py: float
    activity_in_py: float
    maintainability_rating: float
    architecture_rating: float
    technical_debt_in_py: float
    scenario: Scenario
    estimated_change_speed: float
    estimated_effort_py: float
    priority: float


class ModernizationData:
    MAX_SYSTEMS = 100
    MIN_DEV_SPEED_IMPROVEMENT = 5.0
    MIN_EFFORT = 0.25

    BUSINESS_CRITICALITY_FACTOR = {
        "CRITICAL" : 2.0,
        "HIGH" : 1.5,
        "LOW" : 0.0
    }

    PREDETERMINED_SCENARIOS = {
        "INITIAL" : Scenario.KEEP_AS_IS,
        "EOL" : Scenario.REBUILD,
        "EVOLUTION" : Scenario.RENOVATE,
        "DECOMMISSIONED" : Scenario.REPLACE
    }

    @cached_property
    def possible_candidates(self) -> list[CandidateSystem]:
        return list(self.fetch_possible_candidates())

    def fetch_possible_candidates(self):
        portfolio_metadata = {metadata["systemName"]: metadata for metadata in sigrid_api.get_portfolio_metadata()}
        portfolio_maintainability = sigrid_api.get_portfolio_maintainability()

        for system in portfolio_maintainability["systems"]:
            metadata = portfolio_metadata[system["system"]]
            if metadata["active"] and not metadata["isDevelopmentOnly"] and system.get("maintainability"):
                yield CandidateSystem(metadata, system)

    @cached_property
    def modernization_candidates(self) -> list[ModernizationCandidate]:
        systems = self.possible_candidates.copy()
        systems.sort(key=lambda e: -e.maintainability_data["volumeInPersonMonths"])
        systems = systems[0:self.MAX_SYSTEMS]

        candidates = [self.to_modernization_candidate(system.maintainability_data, system.metadata) for system in systems]
        candidates = [candidate for candidate in candidates if self.is_viable_candidate(candidate)]
        candidates.sort(key=lambda candidate: -candidate.priority)
        return candidates

    def to_modernization_candidate(self, system, metadata) -> Optional[ModernizationCandidate]:
        volume_in_py = system["volumeInPersonMonths"] / 12.0
        architecture_graph = sigrid_api.get_architecture_graph_uncached(system["system"])

        if architecture_graph is None or system.get("maintainability") is None:
            return None

        architecture_metrics = architecture_graph["systemElements"][0]["measurementValues"]
        scenario = self.determine_scenario(metadata)
        change_speed = self.get_change_speed(scenario, architecture_metrics)
        renovation_effort = self.get_renovation_effort(scenario, architecture_metrics, volume_in_py)

        return ModernizationCandidate(
            display_name=metadata.get("displayName") or metadata["systemName"],
            business_criticality=metadata.get("businessCriticality") or "unknown",
            volume_in_py=volume_in_py,
            activity_in_py=self.get_activity(volume_in_py, architecture_graph),
            maintainability_rating=system["maintainability"],
            architecture_rating=architecture_metrics["ARCHITECTURE_RATING"],
            technical_debt_in_py=architecture_metrics.get("TECHNICAL_DEBT", 0.0),
            scenario=scenario,
            estimated_change_speed=change_speed,
            estimated_effort_py=renovation_effort,
            priority=self.calculate_priority(metadata, volume_in_py, change_speed)
        )

    def get_activity(self, volume_in_py, architecture_graph):
        churn = architecture_graph["systemElements"][0]["measurementTimeSeries"].get("YEARLY_CHURN_PERCENTAGE")
        if churn is None:
            return None
        return (churn["averageValue"] / 100.0 * 52) * volume_in_py

    def determine_scenario(self, metadata):
        lifecycle = metadata.get("lifecyclePhase")
        return self.PREDETERMINED_SCENARIOS.get(lifecycle, Scenario.RENOVATE)

    def get_change_speed(self, scenario, architecture_metrics):
        if scenario in (Scenario.KEEP_AS_IS, Scenario.REPLACE):
            return 0.0
        return architecture_metrics.get("POTENTIAL_CHANGE_SPEED", 0.0)

    def get_renovation_effort(self, scenario, architecture_metrics, volume_in_py):
        if scenario in (Scenario.KEEP_AS_IS, Scenario.REPLACE):
            return 0.0
        elif scenario == Scenario.REBUILD:
            return volume_in_py
        else:
            return architecture_metrics.get("RENOVATION_EFFORT", 0.0)

    def calculate_priority(self, metadata, volume_in_py, change_speed):
        business_criticality_factor = self.BUSINESS_CRITICALITY_FACTOR.get(metadata.get("businessCriticality"), 1.0)
        return (change_speed * volume_in_py) * business_criticality_factor

    def is_viable_candidate(self, candidate: ModernizationCandidate):
        if candidate is None:
            return False

        return candidate.estimated_change_speed >= self.MIN_DEV_SPEED_IMPROVEMENT and \
            candidate.estimated_effort_py >= self.MIN_EFFORT

    @cached_property
    def single_system_candidate(self):
        maintainability = sigrid_api.get_maintainability_ratings()
        metadata = sigrid_api.get_system_metadata()
        return self.to_modernization_candidate(maintainability, metadata)


modernization_data = ModernizationData()

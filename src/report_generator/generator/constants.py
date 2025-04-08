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

from enum import Enum
from typing import List


class MetricEnum(Enum):
    def __str__(self):
        return self.value

    @classmethod
    def values(cls) -> List[str]:
        return [metric.value for metric in cls]

    def to_json_name(self):
        metric_name = self.value
        metric = metric_name.replace("_", " ").title().replace(" ", "")
        return metric[0].lower() + metric[1:]


class MaintMetric(MetricEnum):
    VOLUME = "VOLUME"
    DUPLICATION = "DUPLICATION"
    UNIT_SIZE = "UNIT_SIZE"
    UNIT_COMPLEXITY = "UNIT_COMPLEXITY"
    UNIT_INTERFACING = "UNIT_INTERFACING"
    MODULE_COUPLING = "MODULE_COUPLING"
    COMPONENT_INDEPENDENCE = "COMPONENT_INDEPENDENCE"
    COMPONENT_ENTANGLEMENT = "COMPONENT_ENTANGLEMENT"


class ArchMetric(MetricEnum):
    CODE_BREAKDOWN = "CODE_BREAKDOWN"
    COMPONENT_COUPLING = "COMPONENT_COUPLING"
    COMPONENT_COHESION = "COMPONENT_COHESION"
    CODE_REUSE = "CODE_REUSE"
    COMMUNICATION_CENTRALIZATION = "COMMUNICATION_CENTRALIZATION"
    DATA_COUPLING = "DATA_COUPLING"
    TECHNOLOGY_PREVALENCE = "TECHNOLOGY_PREVALENCE"
    BOUNDED_EVOLUTION = "BOUNDED_EVOLUTION"
    KNOWLEDGE_DISTRIBUTION = "KNOWLEDGE_DISTRIBUTION"
    COMPONENT_FRESHNESS = "COMPONENT_FRESHNESS"


class ArchSubcharacteristic(MetricEnum):
    KNOWLEDGE = "KNOWLEDGE"
    COMMUNICATION = "COMMUNICATION"
    DATA_ACCESS = "DATA_ACCESS"
    STRUCTURE = "STRUCTURE"
    EVOLUTION = "EVOLUTION"
    TECHNOLOGY_STACK = "TECHNOLOGY_STACK"


class OSHMetric(MetricEnum):
    SYSTEM = "SYSTEM"
    VULNERABILITY = "VULNERABILITY"
    LICENSES = "LICENSES"
    FRESHNESS = "FRESHNESS"
    MANAGEMENT = "MANAGEMENT"
    ACTIVITY = "ACTIVITY"

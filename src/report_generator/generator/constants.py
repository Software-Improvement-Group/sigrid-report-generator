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

MAINT_METRICS = ["VOLUME", "DUPLICATION", "UNIT_SIZE", "UNIT_COMPLEXITY", "UNIT_INTERFACING", "MODULE_COUPLING",
                 "COMPONENT_INDEPENDENCE", "COMPONENT_ENTANGLEMENT"]
ARCH_METRICS = ["CODE_BREAKDOWN", "COMPONENT_COUPLING", "COMPONENT_COHESION", "CODE_REUSE",
                "COMMUNICATION_CENTRALIZATION", "DATA_COUPLING", "TECHNOLOGY_PREVALENCE", "BOUNDED_EVOLUTION",
                "KNOWLEDGE_DISTRIBUTION", "COMPONENT_FRESHNESS"]
ARCH_SUBCHARACTERISTICS = ["KNOWLEDGE", "COMMUNICATION", "DATA_ACCESS", "STRUCTURE", "EVOLUTION", "TECHNOLOGY_STACK"]
OSH_METRICS = ["SYSTEM", "VULNERABILITY", "LICENSES", "FRESHNESS", "MANAGEMENT", "ACTIVITY"]

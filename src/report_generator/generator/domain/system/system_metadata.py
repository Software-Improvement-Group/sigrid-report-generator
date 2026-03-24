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
from typing import Callable, ClassVar

from report_generator.generator.context import sigrid_api

from .maintainability import maintainability_data


class SystemMetadata:
    _attributes: ClassVar[dict[str, str]] = {
        "display_name": "displayName",
        "external_display_name": "externalDisplayName",
        "division_name": "divisionName",
        "supplier_names": "supplierNames",
        "team_names": "teamNames",
        "in_production_since": "inProductionSince",
        "business_criticality": "businessCriticality",
        "lifecycle_phase": "lifecyclePhase",
        "target_industry": "targetIndustry",
        "deployment_type": "deploymentType",
        "application_type": "applicationType",
        "software_distribution_strategy": "softwareDistributionStrategy",
        "is_development_only": "isDevelopmentOnly",
        "remark": "remark",
        "external_id": "externalID",
        "active": "active",
    }

    _fallbacks: ClassVar[dict[str, Callable[[], str]]] = {
        "display_name": lambda: maintainability_data.system_name
    }

    @cached_property
    def data(self):
        return sigrid_api.get_system_metadata()

    def __getattr__(self, name):
        if name not in self._attributes:
            raise AttributeError(name)

        value = self.data[self._attributes[name]]
        if value is None and name in self._fallbacks:
            return self._fallbacks[name]()

        return value


system_metadata = SystemMetadata()

"""
Example API response:
{
    "divisionName": "Backend",
    "displayName": "Hadoop",
    "supplierNames": [
        "Open Source Community",
        "Apache"
    ],
    "teamNames": [
        "architecture"
    ],
    "lifecyclePhase": "EVOLUTION",
    "inProductionSince": 2006,
    "businessCriticality": "CRITICAL",
    "targetIndustry": "ICD9530",
    "deploymentType": "INTERNAL",
    "applicationType": "RESOURCE_MANAGEMENT",
    "softwareDistributionStrategy": "NETWORK_SERVICE",
    "remark": null,
    "externalID": null,
    "externalDisplayName": null,
    "scopeFileInRepository": true,
    "mainTechnology": "java",
    "technologyCategory": "MODERN_GENERAL_PURPOSE",
    "active": true,
    "isDevelopmentOnly": false
}
"""

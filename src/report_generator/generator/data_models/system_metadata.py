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

from report_generator.generator import sigrid_api


class SystemMetadata:
    _attributes = {
        'display_name'                  : 'displayName',
        'external_display_name'         : 'externalDisplayName',
        'division_name'                 : 'divisionName',
        'supplier_names'                : 'supplierNames',
        'team_names'                    : 'teamNames',
        'in_production_since'           : 'inProductionSince',
        'business_criticality'          : 'businessCriticality',
        'lifecycle_phase'               : 'lifecyclePhase',
        'target_industry'               : 'targetIndustry',
        'deployment_type'               : 'deploymentType',
        'application_type'              : 'applicationType',
        'software_distribution_strategy': 'softwareDistributionStrategy',
        'is_development_only'           : 'isDevelopmentOnly',
        'remark'                        : 'remark',
        'external_id'                   : 'externalID'
    }

    @cached_property
    def data(self):
        return sigrid_api.get_system_metadata()

    def __getattr__(self, name):
        if name in self._attributes:
            return self.data[self._attributes[name]]
        raise AttributeError(name)


system_metadata = SystemMetadata()

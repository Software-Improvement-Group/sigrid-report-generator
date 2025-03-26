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

from datetime import datetime
from functools import cached_property

from report_generator.generator import sigrid_api


class ArchitectureData:
    @cached_property
    def data(self):
        return sigrid_api.get_architecture_findings()

    @cached_property
    def date(self):
        return datetime.strptime(self.data["analysisDate"], '%Y-%m-%d')

    @cached_property
    def ratings(self):
        return self.data['ratings']

    @cached_property
    def system_properties(self):
        return self.ratings['systemProperties']

    @cached_property
    def subcharacteristics(self):
        return self.ratings['subcharacteristics']

    def get_score_for_prop_or_subchar(self, metric_or_subchar):
        return self.system_properties[metric_or_subchar] if metric_or_subchar in self.system_properties else \
            self.subcharacteristics[metric_or_subchar]


architecture_data = ArchitectureData()

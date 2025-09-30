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
from .security_dashboard_findings_portfolio import _filter_systems_based_on_metadata

class SecurityDashboardResolutionTimesPortfolioData:
    @cached_property
    def data(self):
        raw_data = sigrid_api.get_portfolio_security_resolution_time_findings()
        return _filter_systems_based_on_metadata(raw_data)
    
    @cached_property
    def system_names(self):
        return [x['system'] for x in self.data['systems']]
    
    def _find_system(self, system):
        for s in self.data['systems']:
            if s['system'] == system:
                return s
        return None
    
security_dashboard_resolution_times_portfolio_data = SecurityDashboardResolutionTimesPortfolioData()
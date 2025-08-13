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

class SecurityRatingsPortfolioData:
    @cached_property
    def data(self):
        return sigrid_api.get_portfolio_security_ratings()
    
    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()

    @cached_property
    def period(self):
        return (None, sigrid_api.get_period()[1])
    
    @cached_property
    def system_names(self):
        return [x['systemName'] for x in self.data]
    
    @staticmethod
    def _find_entry_in_data(data, system):
        for s in data:
            if s['systemName'] == system:
                return s
        return None
    
    def _find_system(self, system):
        return SecurityRatingsPortfolioData._find_entry_in_data(self.data, system)
    
    def find_system_metadata(self, system):
        return SecurityRatingsPortfolioData._find_entry_in_data(self.metadata, system)
    
    def start_snapshot(self, system):
        return None

    def end_snapshot(self, system):
        return self._find_system(system)

security_ratings_portfolio_data = SecurityRatingsPortfolioData()
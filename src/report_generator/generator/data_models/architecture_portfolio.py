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
from .base import BasePortfolioModel

class ArchitecturePortfolioData(BasePortfolioModel):
    @cached_property
    def data(self):
        return sigrid_api.get_portfolio_architecture_findings()

    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]
    
    @cached_property
    def system_names(self):
        return BasePortfolioModel._system_names_helper(self.data, 'system')

    def _find_system(self, system):
        return BasePortfolioModel._find_system_helper(system, self.data, 'system')

architecture_portfolio_data = ArchitecturePortfolioData()
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

from abc import ABC, abstractmethod
from functools import cached_property

from report_generator.generator import sigrid_api

class AbstractPortfolioModel(ABC):
    @cached_property
    @abstractmethod
    def data(self):
        pass

    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()
    
    @cached_property
    @abstractmethod
    def system_names(self):
        pass

    @staticmethod
    def _system_names_helper(data, tag):
        return [x[tag] for x in data]
    
    @cached_property
    def period(self):
        return sigrid_api.get_period()

    @staticmethod
    def _get_system_helper(system, data, tag):
        for s in data:
            if s[tag] == system:
                return s
        return None
    
    @abstractmethod
    def _get_system(self, system):
        pass

    def get_system_metadata(self, system):
        for s in self.metadata:
            if s['systemName'] == system:
                return s
        return None
    
    def start_snapshot(self, system):
        return None

    def end_snapshot(self, system):
        return self._get_system(system)
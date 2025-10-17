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
from abc import ABC, abstractmethod
import logging

from report_generator.generator import sigrid_api
from .base import BasePortfolioModel
from .maintainability_portfolio import maintainability_portfolio_data

class _AbstractMaintainabilityDeltaQualityPortfolioData(BasePortfolioModel, ABC):
    @cached_property
    def data(self):
        result = {}
        type = self.get_type()
        for system in maintainability_portfolio_data.system_names:
            try:
                temp = sigrid_api.get_maintainability_delta_quality(system, type)
            except sigrid_api.SigridAPIRequestFailed as e:
                temp = None
            except Exception as e:
                logging.error("Unexpected error in get_maintainability_delta_quality.")
                raise e
            result[system] = temp
        return result
    
    @abstractmethod
    def get_type(self):
        pass

    def _find_system(self, system):
        return self.data.get(system)
    
    @cached_property
    def system_names(self):
        return list(self.data.keys())

class MaintainabilityDeltaQualityNewCodePortfolioData(_AbstractMaintainabilityDeltaQualityPortfolioData):
    def get_type(self):
        return "NEW_CODE"

class MaintainabilityDeltaQualityChangedCodePortfolioData(_AbstractMaintainabilityDeltaQualityPortfolioData):
    def get_type(self):
        return "CHANGED_CODE"

class MaintainabilityDeltaQualityNewAndChangedCodePortfolioData(_AbstractMaintainabilityDeltaQualityPortfolioData):
    def get_type(self):
        return "NEW_AND_CHANGED_CODE"
    
maintainability_delta_quality_new_code = MaintainabilityDeltaQualityNewCodePortfolioData()
maintainability_delta_quality_changed_code = MaintainabilityDeltaQualityChangedCodePortfolioData()
maintainability_delta_quality_new_and_changed_code = MaintainabilityDeltaQualityNewAndChangedCodePortfolioData()

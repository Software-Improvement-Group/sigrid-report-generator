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
from report_generator.generator.data_models.portfolio.base import AbstractPortfolioModel

from report_generator.generator.data_models.portfolio.portfolio_arguments import filter_data_on_portfolio_arguments

#To import system volume
from report_generator.generator.data_models.portfolio.maintainability_portfolio import maintainability_portfolio_data

class ArchitecturePortfolioData(AbstractPortfolioModel):
    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="system")
    def data(self):
        return sigrid_api.get_portfolio_architecture_findings()

    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]
    
    @cached_property
    def system_names(self):
        return AbstractPortfolioModel._system_names_helper(self.data, 'system')

    def get_system(self, system):
        return AbstractPortfolioModel._get_system_helper(system, self.data, 'system')
    
    @cached_property
    def get_rating_distribution_percentages(self):
        """Calculate percentage of systems in each rating category."""
        counts = {'above_market': 0, 'market_average': 0, 'below_market': 0}
        total = 0
        
        for system in self.data:
            if 'ratings' not in system or 'architecture' not in system['ratings']:
                continue
                
            rating = system['ratings']['architecture']
            category = self._categorize_rating(rating)
            counts[category] += 1
            total += 1
        
        return self._calculate_percentages(counts, total)
    
    def _extract_architecture_rating(self, system):
        """Extract architecture rating from a system."""
        if 'ratings' not in system or 'architecture' not in system['ratings']:
            return None
        return system['ratings']['architecture']
    
    def _get_volume_from_maintainability(self, system_name):
        """Get volume from maintainability portfolio for a given system."""
        try:
            end_snapshot = maintainability_portfolio_data.end_snapshot(system_name)
            return end_snapshot.get('volumeInPersonMonths', 0) if end_snapshot else 0
        except:
            return 0
    
    def _get_rating_and_volume(self, system):
        """Extract rating and volume for a system."""
        rating = self._extract_architecture_rating(system)
        system_name = system.get('system')
        
        if rating is None or system_name is None:
            return None, 0
        
        volume = self._get_volume_from_maintainability(system_name)
        return rating, volume
    
    @cached_property
    def weighted_average_rating(self):
        """Calculate volume-weighted average architecture rating across all systems."""
        total_weighted_rating = 0
        total_volume = 0
        
        for system in self.data:
            rating, volume = self._get_rating_and_volume(system)
            
            if rating is None or volume == 0:
                continue
            
            total_weighted_rating += rating * volume
            total_volume += volume
        
        if total_volume > 0:
            return self._round_star_rating(total_weighted_rating / total_volume)
        return 0.0

architecture_portfolio_data = ArchitecturePortfolioData()
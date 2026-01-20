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
    def get_system(self, system):
        pass

    def get_system_metadata(self, system):
        for s in self.metadata:
            if s['systemName'] == system:
                return s
        return None

    def end_snapshot(self, system):
        return self.get_system(system)
    
    @staticmethod
    def _categorize_rating(rating):
        """Categorize a rating into market segments."""
        if rating >= 3.5:
            return 'above_market'
        elif rating >= 2.5:
            return 'market_average'
        else:
            return 'below_market'
    
    @staticmethod
    def _calculate_percentages(counts, total):
        """Calculate percentages from counts."""
        if total == 0:
            return {'above_market': 0, 'market_average': 0, 'below_market': 0}
        
        return {
            'above_market': round(100 * counts['above_market'] / total),
            'market_average': round(100 * counts['market_average'] / total),
            'below_market': round(100 * counts['below_market'] / total)
        }
    
    @staticmethod
    def _round_star_rating(rating):
        """Round rating to one decimal place."""
        return int(rating * 10) / 10
    
    def _is_month_in_period(self, month):
        """Check if a month falls within the reporting period.
        
        Compares year-month to handle cases where the period is within a single month.
        For example, if period is 2025-01-15 to 2025-01-31, month 2025-01-01 should match.
        """
        if not month:
            return False
        period_start, period_end = self.period
        
        # Extract year-month (YYYY-MM) for comparison
        month_ym = month[:7]  # e.g., "2025-01-01" -> "2025-01"
        period_start_ym = period_start[:7]
        period_end_ym = period_end[:7]
        
        # Month is included if its year-month falls within the period's year-month range
        return period_start_ym <= month_ym <= period_end_ym
    
    def _get_volume_from_maintainability(self, system_name):
        """Get volume from maintainability portfolio for a given system."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import maintainability_portfolio_data
        
        try:
            end_snapshot = maintainability_portfolio_data.end_snapshot(system_name)
            return end_snapshot.get('volumeInPersonMonths', 0) if end_snapshot else 0
        except Exception:
            return 0
    
    def _get_rating_and_volume_from_system(self, system, rating_extractor, system_name_key='systemName'):
        """
        Extract rating and volume for a system.
        
        Args:
            system: System dictionary
            rating_extractor: Function that takes system and returns rating value
            system_name_key: Key to use for extracting system name (default 'systemName')
        
        Returns:
            tuple: (rating, volume) where rating may be None and volume is 0 if invalid
        """
        rating = rating_extractor(system)
        system_name = system.get(system_name_key)
        
        if rating is None or system_name is None:
            return None, 0
        
        volume = self._get_volume_from_maintainability(system_name)
        return rating, volume
    
    def _calculate_weighted_average_rating(self, data_source, get_rating_and_volume_func):
        """
        Calculate volume-weighted average rating across all items in a data source.
        
        Args:
            data_source: Iterable of systems/items to process
            get_rating_and_volume_func: Function that takes an item and returns (rating, volume) tuple
        
        Returns:
            float: Weighted average rating rounded to one decimal place, or 0.0 if no valid data
        """
        total_weighted_rating = 0
        total_volume = 0
        
        for item in data_source:
            rating, volume = get_rating_and_volume_func(item)
            
            if rating is None or volume == 0:
                continue
            
            total_weighted_rating += rating * volume
            total_volume += volume
        
        if total_volume > 0:
            return self._round_star_rating(total_weighted_rating / total_volume)
        return 0.0
    
    def _get_rating_distribution_percentages(self, data_source, rating_extractor):
        """
        Calculate percentage of items in each rating category (above_market, market_average, below_market).
        
        Args:
            data_source: Iterable of systems/items to process
            rating_extractor: Function that takes an item and returns its rating (or None if unavailable)
        
        Returns:
            dict: Percentages for 'above_market', 'market_average', and 'below_market' categories
        """
        counts = {'above_market': 0, 'market_average': 0, 'below_market': 0}
        total = 0
        
        for item in data_source:
            rating = rating_extractor(item)
            if rating is None:
                continue
                
            category = self._categorize_rating(rating)
            counts[category] += 1
            total += 1
        
        return self._calculate_percentages(counts, total)

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

from report_generator.generator.context import sigrid_api
from report_generator.generator.context.portfolio_filters import filter_data_on_portfolio_arguments
from report_generator.generator.domain.portfolio.base import AbstractPortfolioModel
from report_generator.generator.domain.portfolio.shared import utils


class SecurityDashboardResolutionTimesPortfolioData(AbstractPortfolioModel):
    @cached_property
    @filter_data_on_portfolio_arguments(data_tag="systems", system_tag="system")
    def data(self):
        return sigrid_api.get_portfolio_security_resolution_time_findings()
    
    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data['systems'], 'system')
    
    def get_system(self, system):
        return utils.get_system_helper(system, self.data['systems'], 'system')
    
    @cached_property
    def period(self):
        return sigrid_api.get_period()
    
    def _initialize_resolution_stats(self):
        """Initialize resolution statistics structure for all severity levels."""
        return {
            'CRITICAL': {'no_risk': 0, 'low_risk': 0, 'medium_risk': 0, 'high_risk': 0},
            'HIGH': {'no_risk': 0, 'low_risk': 0, 'medium_risk': 0, 'high_risk': 0},
            'MEDIUM': {'no_risk': 0, 'low_risk': 0, 'medium_risk': 0, 'high_risk': 0},
            'LOW': {'no_risk': 0, 'low_risk': 0, 'medium_risk': 0, 'high_risk': 0}
        }
    
    def _accumulate_resolution_counts(self, stats):
        """Accumulate resolution time counts for all severity levels within the period."""
        for system in self.data.get('systems', []):
            for month_data in system.get('resolutionTimes', []):
                if utils.is_month_in_period(month_data.get('month'), self.period):
                    severities = month_data.get('severities', {})
                    
                    for severity_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                        severity_data = severities.get(severity_level, {})
                        stats[severity_level]['no_risk'] += severity_data.get('noRisk', 0)
                        stats[severity_level]['low_risk'] += severity_data.get('lowRisk', 0)
                        stats[severity_level]['medium_risk'] += severity_data.get('mediumRisk', 0)
                        stats[severity_level]['high_risk'] += severity_data.get('highRisk', 0)
    
    def _calculate_most_common_times(self, stats):
        """Calculate which time bucket has the most findings for each severity level."""
        for severity_level in stats:
            counts = stats[severity_level]
            severity_legend = self.legend.get(severity_level, {})
            most_days, most_findings = self._find_most_common_resolution_time(counts, severity_legend)
            stats[severity_level]['most_days'] = most_days
            stats[severity_level]['most_findings'] = most_findings
    
    def _find_most_common_resolution_time(self, counts, severity_legend):
        """Determine which time bucket has the most findings for a specific severity level.
        
        Uses the legend to determine the appropriate labels for each risk category.
        """
        # Use legend text directly as labels from API response
        no_risk_label = severity_legend.get('noRisk', '')
        low_risk_label = severity_legend.get('lowRisk', '')
        medium_risk_label = severity_legend.get('mediumRisk', '')
        high_risk_label = severity_legend.get('highRisk', '')
        
        buckets = {
            no_risk_label: counts['no_risk'],
            low_risk_label: counts['low_risk'],
            medium_risk_label: counts['medium_risk'],
            high_risk_label: counts['high_risk']
        }
        
        most_label = no_risk_label
        most_findings = counts['no_risk']
        
        for label, count in buckets.items():
            if count > most_findings:
                most_label = label
                most_findings = count
        
        return most_label, most_findings
    
    @cached_property
    def _all_resolution_statistics(self):
        """
        Calculate resolution time statistics for all severity levels in a single loop for efficiency.
        
        Returns:
            dict: Statistics for each severity level (CRITICAL, HIGH, MEDIUM, LOW).
        """
        stats = self._initialize_resolution_stats()
        self._accumulate_resolution_counts(stats)
        self._calculate_most_common_times(stats)
        return stats
    
    @cached_property
    def critical_resolution_statistics(self):
        """
        Calculate resolution time statistics for critical security findings.
        
        Returns:
            dict: Statistics including counts per risk category and most common resolution time.
        """
        return self._all_resolution_statistics['CRITICAL']
    
    @cached_property
    def high_resolution_statistics(self):
        """
        Calculate resolution time statistics for high severity security findings.
        
        Returns:
            dict: Statistics including counts per risk category and most common resolution time.
        """
        return self._all_resolution_statistics['HIGH']
    
    @cached_property
    def medium_resolution_statistics(self):
        """
        Calculate resolution time statistics for medium severity security findings.
        
        Returns:
            dict: Statistics including counts per risk category and most common resolution time.
        """
        return self._all_resolution_statistics['MEDIUM']
    
    @cached_property
    def low_resolution_statistics(self):
        """
        Calculate resolution time statistics for low severity security findings.
        
        Returns:
            dict: Statistics including counts per risk category and most common resolution time.
        """
        return self._all_resolution_statistics['LOW']
    
    @cached_property
    def legend(self):
        """Cache the legend data from API"""
        return self.data.get('legend', {})
    
    def get_legend_labels(self, severity):
        """
        Get legend labels from API for a specific severity level.
        
        Args:
            severity: Severity level ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
        
        Returns:
            dict: Labels for each risk category (noRisk, lowRisk, mediumRisk, highRisk)
        """
        severity_legend = self.legend.get(severity, {})
        
        return {
            'noRisk': severity_legend.get('noRisk', 'No Risk'),
            'lowRisk': severity_legend.get('lowRisk', 'Low Risk'),
            'mediumRisk': severity_legend.get('mediumRisk', 'Medium Risk'),
            'highRisk': severity_legend.get('highRisk', 'High Risk')
        }
    
    @cached_property
    def unique_months(self):
        """Extract unique month labels from resolution times data"""
        from datetime import datetime
        
        columns = []
        for system in self.data['systems']:
            for entry in system.get('resolutionTimes', []):
                month = datetime.strptime(entry['month'], "%Y-%m-%d").strftime("%b")
                if month not in columns:
                    columns.append(month)
        return columns
    
    def _update_times_for_entry(self, times, entry, severity, columns):
        """Update times arrays for a single resolution time entry"""
        from datetime import datetime
        
        month = datetime.strptime(entry['month'], "%Y-%m-%d").strftime("%b")
        month_idx = columns.index(month)
        
        severities = entry.get('severities', {}).get(severity, {})
        times['noRisk'][month_idx] += severities.get('noRisk', 0)
        times['lowRisk'][month_idx] += severities.get('lowRisk', 0)
        times['mediumRisk'][month_idx] += severities.get('mediumRisk', 0)
        times['highRisk'][month_idx] += severities.get('highRisk', 0)
    
    def _aggregate_resolution_times_for_severity(self, severity, columns):
        """Aggregate resolution times data for a specific severity across all systems"""
        times = {
            'noRisk': [0] * len(columns),
            'lowRisk': [0] * len(columns),
            'mediumRisk': [0] * len(columns),
            'highRisk': [0] * len(columns)
        }
        
        for system in self.data['systems']:
            for entry in system.get('resolutionTimes', []):
                self._update_times_for_entry(times, entry, severity, columns)
        
        return times
    
    def chart_resolution_times_by_severity(self, severity):
        """
        Get aggregated resolution times data by severity level for chart display.
        
        Args:
            severity: Severity level ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
        
        Returns:
            dict: Contains 'columns' (month labels) and arrays for each risk level
        """
        columns = self.unique_months
        times = self._aggregate_resolution_times_for_severity(severity, columns)
        times['columns'] = columns
        return times

security_dashboard_resolution_times_portfolio_data = SecurityDashboardResolutionTimesPortfolioData()
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
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared import utils


class SecurityDashboardFindingsPortfolioData:
    @cached_property
    @filter_data_on_portfolio_arguments(data_tag="systems", system_tag="system")
    def data(self):
        return sigrid_api.get_portfolio_security_dashboard_findings()

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data["systems"], "system")

    def get_system(self, system):
        return utils.get_system_helper(system, self.data["systems"], "system")

    def _initialize_severity_stats(self):
        """Initialize statistics structure for all severity levels."""
        return {
            "CRITICAL": {"resolved": 0, "added": 0},
            "HIGH": {"resolved": 0, "added": 0},
            "MEDIUM": {"resolved": 0, "added": 0},
            "LOW": {"resolved": 0, "added": 0},
        }

    def _accumulate_severity_counts(self, stats):
        """Accumulate resolved and added counts for all severity levels within the period."""
        for system in self.data.get("systems", []):
            for month_data in system.get("findingRatio", []):
                if utils.is_month_in_period(month_data.get("month"), sigrid_api.get_period()):
                    severities = month_data.get("severities", {})

                    for severity_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                        severity_data = severities.get(severity_level, {})
                        stats[severity_level]["resolved"] += severity_data.get(
                            "resolved", 0
                        )
                        stats[severity_level]["added"] += severity_data.get("new", 0)

    def _calculate_net_changes(self, stats):
        """Calculate net change for each severity level."""
        for severity_level in stats:
            net_change = (
                stats[severity_level]["added"] - stats[severity_level]["resolved"]
            )
            stats[severity_level]["net_change"] = net_change

    def _get_earliest_month(self):
        """Get the earliest month from the actual API data.

        Returns:
            str: The earliest month date (always first of the month), or period start if no data.
        """
        earliest_month = None

        for system in self.data.get("systems", []):
            for month_data in system.get("findingRatio", []):
                month = month_data.get("month")
                if month and (earliest_month is None or month < earliest_month):
                    earliest_month = month

        return earliest_month if earliest_month else sigrid_api.get_period()[0]

    @cached_property
    def _all_findings_statistics(self):
        """
        Calculate statistics for all severity levels in a single loop for efficiency.

        Returns:
            dict: Statistics for each severity level (CRITICAL, HIGH, MEDIUM, LOW).
        """
        stats = self._initialize_severity_stats()
        self._accumulate_severity_counts(stats)
        self._calculate_net_changes(stats)
        return stats

    @cached_property
    def critical_findings_statistics(self):
        """
        Calculate statistics for critical security findings across the portfolio.

        Returns:
            dict: Statistics including total resolved, new, and net change in critical findings.
        """
        return self._all_findings_statistics["CRITICAL"]

    @cached_property
    def high_findings_statistics(self):
        """
        Calculate statistics for high severity security findings across the portfolio.

        Returns:
            dict: Statistics including total resolved, new, and net change in high severity findings.
        """
        return self._all_findings_statistics["HIGH"]

    @cached_property
    def medium_findings_statistics(self):
        """
        Calculate statistics for medium severity security findings across the portfolio.

        Returns:
            dict: Statistics including total resolved, new, and net change in medium severity findings.
        """
        return self._all_findings_statistics["MEDIUM"]

    @cached_property
    def low_findings_statistics(self):
        """
        Calculate statistics for low severity security findings across the portfolio.

        Returns:
            dict: Statistics including total resolved, new, and net change in low severity findings.
        """
        return self._all_findings_statistics["LOW"]

    @cached_property
    def unique_months(self):
        """Extract unique month labels from findings data"""
        from datetime import datetime

        columns = []
        for system in self.data["systems"]:
            for ratio in system.get("findingRatio", []):
                month = datetime.strptime(ratio["month"], "%Y-%m-%d").strftime("%b")
                if month not in columns:
                    columns.append(month)
        return columns

    def _aggregate_findings_for_severity(self, severity, columns):
        """Aggregate findings data for a specific severity across all systems"""
        from datetime import datetime

        findings = {
            "new": [0] * len(columns),
            "existing": [0] * len(columns),
            "resolved": [0] * len(columns),
        }

        for system in self.data["systems"]:
            for ratio in system.get("findingRatio", []):
                month = datetime.strptime(ratio["month"], "%Y-%m-%d").strftime("%b")
                month_idx = columns.index(month)

                severities = ratio.get("severities", {}).get(severity, {})
                findings["new"][month_idx] += severities.get("new", 0)
                findings["existing"][month_idx] += severities.get("existing", 0)
                findings["resolved"][month_idx] += severities.get("resolved", 0)

        return findings

    def chart_findings_by_severity(self, severity):
        """
        Get aggregated findings data by severity level for chart display.

        Args:
            severity: Severity level ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')

        Returns:
            dict: Contains 'columns' (month labels), 'new', 'existing', and 'resolved' arrays
        """
        columns = self.unique_months
        findings = self._aggregate_findings_for_severity(severity, columns)
        findings["columns"] = columns
        return findings


security_dashboard_findings_portfolio_data = SecurityDashboardFindingsPortfolioData()

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

from unittest.mock import patch

import pytest

from report_generator.generator.context.portfolio_filters import reset_context
from report_generator.generator.domain.portfolio.security_dashboard_findings_portfolio import (
    SecurityDashboardFindingsPortfolioData,
    security_dashboard_findings_portfolio_data,
)
from report_generator.generator.domain.portfolio.security_dashboard_resolution_times_portfolio import (
    SecurityDashboardResolutionTimesPortfolioData,
    security_dashboard_resolution_times_portfolio_data,
)
from report_generator.generator.domain.portfolio.security_portfolio import (
    SecurityRatingsPortfolioData,
    security_ratings_change_portfolio_data,
    security_ratings_portfolio_data,
)
from report_generator.generator.domain.shared.findings_severity import (
    FALLBACK_SEVERITY_THRESHOLD,
    count_findings_above_objective,
    count_findings_above_severity,
)


class TestSecurityCriticalFindingsStatistics:
    """Test the critical findings statistics for security dashboard."""

    def test_critical_findings_statistics_with_resolved_and_added(self, mocker):
        """Test statistics calculation with both resolved and added critical findings."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 5, "existing": 10, "new": 2},
                                "HIGH": {"resolved": 3, "existing": 8, "new": 1},
                            },
                        },
                        {
                            "month": "2025-02-01",
                            "severities": {
                                "CRITICAL": {"resolved": 3, "existing": 9, "new": 1},
                                "HIGH": {"resolved": 2, "existing": 7, "new": 0},
                            },
                        },
                    ],
                },
                {
                    "system": "system2",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 2, "existing": 5, "new": 4},
                                "HIGH": {"resolved": 1, "existing": 3, "new": 2},
                            },
                        }
                    ],
                },
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_findings_statistics

        # Total resolved: 5 + 3 + 2 = 10
        assert stats["resolved"] == 10
        # Total added: 2 + 1 + 4 = 7
        assert stats["added"] == 7
        # Net change: 7 - 10 = -3 (decrease of 3)
        assert stats["net_change"] == -3

    def test_critical_findings_statistics_with_only_additions(self, mocker):
        """Test statistics when only new critical findings are added."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 0, "existing": 5, "new": 8},
                                "HIGH": {"resolved": 1, "existing": 3, "new": 2},
                            },
                        }
                    ],
                },
                {
                    "system": "system2",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 0, "existing": 2, "new": 5},
                                "HIGH": {"resolved": 0, "existing": 1, "new": 1},
                            },
                        }
                    ],
                },
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_findings_statistics

        assert stats["resolved"] == 0
        assert stats["added"] == 13  # 8 + 5
        assert stats["net_change"] == 13  # All new findings

    def test_critical_findings_statistics_with_only_resolutions(self, mocker):
        """Test statistics when only critical findings are resolved."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 10, "existing": 0, "new": 0},
                                "HIGH": {"resolved": 5, "existing": 2, "new": 0},
                            },
                        }
                    ],
                },
                {
                    "system": "system2",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 7, "existing": 0, "new": 0}
                            },
                        }
                    ],
                },
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_findings_statistics

        assert stats["resolved"] == 17  # 10 + 7
        assert stats["added"] == 0
        assert stats["net_change"] == -17  # All resolved, net decrease

    def test_critical_findings_statistics_ignores_other_severities(self, mocker):
        """Test that only CRITICAL severity findings are counted, not HIGH, MEDIUM, or LOW."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 3, "existing": 5, "new": 2},
                                "HIGH": {"resolved": 10, "existing": 8, "new": 15},
                                "MEDIUM": {"resolved": 20, "existing": 10, "new": 25},
                                "LOW": {"resolved": 5, "existing": 3, "new": 8},
                            },
                        }
                    ],
                }
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_findings_statistics

        # Only CRITICAL findings should be counted
        assert stats["resolved"] == 3
        assert stats["added"] == 2
        assert stats["net_change"] == -1

    def test_critical_findings_statistics_with_empty_data(self, mocker):
        """Test statistics with no systems or findings."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {"systems": []}

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_findings_statistics

        assert stats["resolved"] == 0
        assert stats["added"] == 0
        assert stats["net_change"] == 0

    def test_critical_findings_statistics_with_missing_critical_severity(self, mocker):
        """Test statistics when CRITICAL severity data is missing from some months."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "HIGH": {"resolved": 5, "existing": 3, "new": 2}
                                # CRITICAL is missing
                            },
                        },
                        {
                            "month": "2025-02-01",
                            "severities": {
                                "CRITICAL": {"resolved": 4, "existing": 2, "new": 3},
                                "HIGH": {"resolved": 1, "existing": 1, "new": 1},
                            },
                        },
                    ],
                }
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_findings_statistics

        # Only the second month's CRITICAL data should be counted
        assert stats["resolved"] == 4
        assert stats["added"] == 3
        assert stats["net_change"] == -1


class TestSecurityHighMediumLowFindingsStatistics:
    """Test the high, medium, and low severity findings statistics."""

    def test_high_findings_statistics(self, mocker):
        """Test high severity findings statistics calculation."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "HIGH": {"resolved": 10, "existing": 5, "new": 3},
                                "MEDIUM": {"resolved": 2, "existing": 1, "new": 1},
                            },
                        },
                        {
                            "month": "2025-02-01",
                            "severities": {
                                "HIGH": {"resolved": 5, "existing": 3, "new": 7},
                                "MEDIUM": {"resolved": 1, "existing": 0, "new": 0},
                            },
                        },
                    ],
                },
                {
                    "system": "system2",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "HIGH": {"resolved": 8, "existing": 4, "new": 2}
                            },
                        }
                    ],
                },
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.high_findings_statistics

        # Total resolved: 10 + 5 + 8 = 23
        assert stats["resolved"] == 23
        # Total added: 3 + 7 + 2 = 12
        assert stats["added"] == 12
        # Net change: 12 - 23 = -11 (decrease)
        assert stats["net_change"] == -11

    def test_medium_findings_statistics(self, mocker):
        """Test medium severity findings statistics calculation."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "MEDIUM": {"resolved": 3, "existing": 8, "new": 5},
                                "LOW": {"resolved": 1, "existing": 2, "new": 0},
                            },
                        },
                        {
                            "month": "2025-02-01",
                            "severities": {
                                "MEDIUM": {"resolved": 2, "existing": 11, "new": 4}
                            },
                        },
                    ],
                },
                {
                    "system": "system2",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "MEDIUM": {"resolved": 1, "existing": 5, "new": 6}
                            },
                        }
                    ],
                },
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.medium_findings_statistics

        # Total resolved: 3 + 2 + 1 = 6
        assert stats["resolved"] == 6
        # Total added: 5 + 4 + 6 = 15
        assert stats["added"] == 15
        # Net change: 15 - 6 = 9 (increase)
        assert stats["net_change"] == 9

    def test_low_findings_statistics(self, mocker):
        """Test low severity findings statistics calculation."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "LOW": {"resolved": 20, "existing": 15, "new": 10}
                            },
                        },
                        {
                            "month": "2025-02-01",
                            "severities": {
                                "LOW": {"resolved": 15, "existing": 10, "new": 5}
                            },
                        },
                    ],
                },
                {
                    "system": "system2",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "LOW": {"resolved": 12, "existing": 8, "new": 3}
                            },
                        }
                    ],
                },
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.low_findings_statistics

        # Total resolved: 20 + 15 + 12 = 47
        assert stats["resolved"] == 47
        # Total added: 10 + 5 + 3 = 18
        assert stats["added"] == 18
        # Net change: 18 - 47 = -29 (decrease)
        assert stats["net_change"] == -29

    def test_all_severities_calculated_efficiently(self, mocker):
        """Test that all severity statistics are calculated from the same cached data."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 1, "existing": 0, "new": 2},
                                "HIGH": {"resolved": 3, "existing": 1, "new": 4},
                                "MEDIUM": {"resolved": 5, "existing": 2, "new": 6},
                                "LOW": {"resolved": 7, "existing": 3, "new": 8},
                            },
                        }
                    ],
                }
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        # Access all statistics
        critical = portfolio.critical_findings_statistics
        high = portfolio.high_findings_statistics
        medium = portfolio.medium_findings_statistics
        low = portfolio.low_findings_statistics

        # Verify each severity has correct values
        assert critical == {"resolved": 1, "added": 2, "net_change": 1}
        assert high == {"resolved": 3, "added": 4, "net_change": 1}
        assert medium == {"resolved": 5, "added": 6, "net_change": 1}
        assert low == {"resolved": 7, "added": 8, "net_change": 1}

        # Verify that _all_findings_statistics is the same object (cached)
        assert portfolio._all_findings_statistics["CRITICAL"] is critical
        assert portfolio._all_findings_statistics["HIGH"] is high
        assert portfolio._all_findings_statistics["MEDIUM"] is medium
        assert portfolio._all_findings_statistics["LOW"] is low

    def test_missing_severity_data_returns_zero(self, mocker):
        """Test that missing severity data returns zero values instead of errors."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {"resolved": 5, "existing": 2, "new": 3}
                                # HIGH, MEDIUM, LOW are missing
                            },
                        }
                    ],
                }
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        # Missing severities should return all zeros
        assert portfolio.high_findings_statistics == {
            "resolved": 0,
            "added": 0,
            "net_change": 0,
        }
        assert portfolio.medium_findings_statistics == {
            "resolved": 0,
            "added": 0,
            "net_change": 0,
        }
        assert portfolio.low_findings_statistics == {
            "resolved": 0,
            "added": 0,
            "net_change": 0,
        }

        # CRITICAL should still have data
        assert portfolio.critical_findings_statistics == {
            "resolved": 5,
            "added": 3,
            "net_change": -2,
        }

    def test_empty_systems_returns_zero(self, mocker):
        """Test that empty systems list returns zero values."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {"systems": []}

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        # All severities should return zeros
        assert portfolio.critical_findings_statistics == {
            "resolved": 0,
            "added": 0,
            "net_change": 0,
        }
        assert portfolio.high_findings_statistics == {
            "resolved": 0,
            "added": 0,
            "net_change": 0,
        }
        assert portfolio.medium_findings_statistics == {
            "resolved": 0,
            "added": 0,
            "net_change": 0,
        }
        assert portfolio.low_findings_statistics == {
            "resolved": 0,
            "added": 0,
            "net_change": 0,
        }

    def test_findings_filtered_by_period(self, mocker):
        """Test that only findings within the specified period are counted."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2024-12-01",  # Before period
                            "severities": {
                                "CRITICAL": {
                                    "resolved": 100,
                                    "existing": 50,
                                    "new": 100,
                                }
                            },
                        },
                        {
                            "month": "2025-01-01",  # Start of period
                            "severities": {
                                "CRITICAL": {"resolved": 5, "existing": 10, "new": 3}
                            },
                        },
                        {
                            "month": "2025-06-01",  # Middle of period
                            "severities": {
                                "CRITICAL": {"resolved": 2, "existing": 11, "new": 1}
                            },
                        },
                        {
                            "month": "2025-12-31",  # End of period
                            "severities": {
                                "CRITICAL": {"resolved": 3, "existing": 9, "new": 2}
                            },
                        },
                        {
                            "month": "2026-01-01",  # After period
                            "severities": {
                                "CRITICAL": {
                                    "resolved": 200,
                                    "existing": 100,
                                    "new": 200,
                                }
                            },
                        },
                    ],
                }
            ]
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_findings_statistics

        # Only data from 2025-01-01 to 2025-12-31 should be counted
        # Resolved: 5 + 2 + 3 = 10 (excluding 100 from before and 200 from after)
        assert stats["resolved"] == 10
        # Added: 3 + 1 + 2 = 6 (excluding 100 from before and 200 from after)
        assert stats["added"] == 6
        # Net change: 6 - 10 = -4
        assert stats["net_change"] == -4

    def test_findings_with_single_month_period(self, mocker):
        """Test that findings are counted when period is within a single month (e.g., 2025-01-15 to 2025-01-31)."""

        portfolio = SecurityDashboardFindingsPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "findingRatio": [
                        {
                            "month": "2024-12-01",  # Different month, should be excluded
                            "severities": {
                                "CRITICAL": {
                                    "resolved": 100,
                                    "existing": 50,
                                    "new": 100,
                                }
                            },
                        },
                        {
                            "month": "2025-01-01",  # Same month as period, should be included
                            "severities": {
                                "CRITICAL": {"resolved": 5, "existing": 10, "new": 3},
                                "HIGH": {"resolved": 10, "existing": 5, "new": 8},
                            },
                        },
                        {
                            "month": "2025-02-01",  # Different month, should be excluded
                            "severities": {
                                "CRITICAL": {
                                    "resolved": 200,
                                    "existing": 100,
                                    "new": 200,
                                }
                            },
                        },
                    ],
                }
            ]
        }

        # Period is within January 2025
        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-15", "2025-01-31"),
        )

        stats = portfolio.critical_findings_statistics
        high_stats = portfolio.high_findings_statistics

        # Should include data from 2025-01-01 (same year-month as period)
        assert stats["resolved"] == 5
        assert stats["added"] == 3
        assert stats["net_change"] == -2

        assert high_stats["resolved"] == 10
        assert high_stats["added"] == 8
        assert high_stats["net_change"] == -2


class TestSecurityCriticalResolutionTimes:
    """Test the critical findings resolution time statistics."""

    def test_critical_resolution_statistics_basic(self, mocker):
        """Test basic resolution time statistics calculation."""

        portfolio = SecurityDashboardResolutionTimesPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "resolutionTimes": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 10,  # Within 7 days
                                    "lowRisk": 5,  # 8-14 days
                                    "mediumRisk": 3,  # 15-30 days
                                    "highRisk": 2,  # 30+ days
                                }
                            },
                        },
                        {
                            "month": "2025-02-01",
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 8,
                                    "lowRisk": 4,
                                    "mediumRisk": 2,
                                    "highRisk": 1,
                                }
                            },
                        },
                    ],
                },
                {
                    "system": "system2",
                    "resolutionTimes": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 12,
                                    "lowRisk": 3,
                                    "mediumRisk": 1,
                                    "highRisk": 0,
                                }
                            },
                        }
                    ],
                },
            ],
            "legend": {
                "CRITICAL": {
                    "noRisk": "at most 7 days",
                    "lowRisk": "between 7 and 14 days",
                    "mediumRisk": "between 14 and 30 days",
                    "highRisk": "at least 30 days",
                }
            },
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_resolution_statistics

        # Total counts across all systems and months
        assert stats["no_risk"] == 30  # 10 + 8 + 12
        assert stats["low_risk"] == 12  # 5 + 4 + 3
        assert stats["medium_risk"] == 6  # 3 + 2 + 1
        assert stats["high_risk"] == 3  # 2 + 1 + 0

        # Most common bucket should be noRisk with 30 findings
        assert stats["most_days"] == "at most 7 days"
        assert stats["most_findings"] == 30

    def test_critical_resolution_statistics_most_is_high_risk(self, mocker):
        """Test when most findings are in the high risk category."""

        portfolio = SecurityDashboardResolutionTimesPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "resolutionTimes": [
                        {
                            "month": "2025-01-01",
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 2,
                                    "lowRisk": 3,
                                    "mediumRisk": 5,
                                    "highRisk": 50,  # Most in high risk
                                }
                            },
                        }
                    ],
                }
            ],
            "legend": {
                "CRITICAL": {
                    "noRisk": "at most 7 days",
                    "lowRisk": "between 7 and 14 days",
                    "mediumRisk": "between 14 and 30 days",
                    "highRisk": "at least 30 days",
                }
            },
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_resolution_statistics

        assert stats["high_risk"] == 50
        assert stats["most_days"] == "at least 30 days"
        assert stats["most_findings"] == 50

    def test_critical_resolution_statistics_filtered_by_period(self, mocker):
        """Test that resolution times are filtered by the reporting period."""

        portfolio = SecurityDashboardResolutionTimesPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "resolutionTimes": [
                        {
                            "month": "2024-12-01",  # Before period
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 100,
                                    "lowRisk": 100,
                                    "mediumRisk": 100,
                                    "highRisk": 100,
                                }
                            },
                        },
                        {
                            "month": "2025-01-01",  # Within period
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 5,
                                    "lowRisk": 3,
                                    "mediumRisk": 2,
                                    "highRisk": 1,
                                }
                            },
                        },
                        {
                            "month": "2026-01-01",  # After period
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 200,
                                    "lowRisk": 200,
                                    "mediumRisk": 200,
                                    "highRisk": 200,
                                }
                            },
                        },
                    ],
                }
            ],
            "legend": {
                "CRITICAL": {
                    "noRisk": "at most 7 days",
                    "lowRisk": "between 7 and 14 days",
                    "mediumRisk": "between 14 and 30 days",
                    "highRisk": "at least 30 days",
                }
            },
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_resolution_statistics

        # Should only include data from 2025-01-01
        assert stats["no_risk"] == 5
        assert stats["low_risk"] == 3
        assert stats["medium_risk"] == 2
        assert stats["high_risk"] == 1

    def test_critical_resolution_statistics_empty_data(self, mocker):
        """Test with empty systems data."""

        portfolio = SecurityDashboardResolutionTimesPortfolioData()

        mock_data = {
            "systems": [],
            "legend": {
                "CRITICAL": {
                    "noRisk": "at most 7 days",
                    "lowRisk": "between 7 and 14 days",
                    "mediumRisk": "between 14 and 30 days",
                    "highRisk": "at least 30 days",
                }
            },
        }

        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-01", "2025-12-31"),
        )

        stats = portfolio.critical_resolution_statistics

        assert stats["no_risk"] == 0
        assert stats["low_risk"] == 0
        assert stats["medium_risk"] == 0
        assert stats["high_risk"] == 0
        assert stats["most_days"] == "at most 7 days"  # From legend
        assert stats["most_findings"] == 0

    def test_critical_resolution_statistics_with_single_month_period(self, mocker):
        """Test resolution times with period within a single month."""

        portfolio = SecurityDashboardResolutionTimesPortfolioData()

        mock_data = {
            "systems": [
                {
                    "system": "system1",
                    "resolutionTimes": [
                        {
                            "month": "2024-12-01",  # Different month
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 100,
                                    "lowRisk": 100,
                                    "mediumRisk": 100,
                                    "highRisk": 100,
                                }
                            },
                        },
                        {
                            "month": "2025-01-01",  # Same month as period
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 15,
                                    "lowRisk": 8,
                                    "mediumRisk": 5,
                                    "highRisk": 3,
                                }
                            },
                        },
                        {
                            "month": "2025-02-01",  # Different month
                            "severities": {
                                "CRITICAL": {
                                    "noRisk": 200,
                                    "lowRisk": 200,
                                    "mediumRisk": 200,
                                    "highRisk": 200,
                                }
                            },
                        },
                    ],
                }
            ],
            "legend": {
                "CRITICAL": {
                    "noRisk": "at most 7 days",
                    "lowRisk": "between 7 and 14 days",
                    "mediumRisk": "between 14 and 30 days",
                    "highRisk": "at least 30 days",
                }
            },
        }

        # Period is within January 2025
        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )
        mocker.patch(
            "report_generator.generator.context.sigrid_api.get_period",
            return_value=("2025-01-15", "2025-01-31"),
        )

        stats = portfolio.critical_resolution_statistics

        # Should include data from 2025-01-01 (same year-month)
        assert stats["no_risk"] == 15
        assert stats["low_risk"] == 8
        assert stats["medium_risk"] == 5
        assert stats["high_risk"] == 3
        assert stats["most_days"] == "at most 7 days"
        assert stats["most_findings"] == 15


class TestSecurityPortfolioData:
    """Test cases for SecurityRatingsPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = [
            "data",
            "metadata",
            "period",
            "system_names",
            "_raw_findings",
            "_objective_index",
            "findings_above_objective",
            "top_systems_by_findings_above_objective",
        ]
        for attr in cache_attrs:
            security_ratings_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.shared.findings_portfolio_base.sigrid_api"
    )
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = [
            {"systemName": "system1", "securityRating": 4.5},
            {"systemName": "system2", "securityRating": 3.8},
        ]
        mock_sigrid_api.get_portfolio_security_ratings.return_value = mock_data

        security_ratings_portfolio_data.__dict__.pop("data", None)

        system = security_ratings_portfolio_data.get_system("system1")

        assert system is not None
        assert system["systemName"] == "system1"
        assert abs(system["securityRating"] - 4.5) < 0.01

    @patch(
        "report_generator.generator.domain.portfolio.shared.findings_portfolio_base.sigrid_api"
    )
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = [
            {"systemName": "system1", "securityRating": 4.5},
            {"systemName": "system2", "securityRating": 3.8},
            {"systemName": "system3", "securityRating": 4.2},
        ]
        mock_sigrid_api.get_portfolio_security_ratings.return_value = mock_data

        for attr in ["data", "system_names"]:
            security_ratings_portfolio_data.__dict__.pop(attr, None)

        names = security_ratings_portfolio_data.system_names

        assert len(names) == 3
        assert "system1" in names
        assert "system2" in names
        assert "system3" in names


class TestSecurityRatingsChangePortfolioData:
    """Test cases for SecurityRatingsChangePortfolioData (per-system rating delta)."""

    def teardown_method(self):
        reset_context()
        for attr in [
            "_start_ratings",
            "_end_ratings",
            "differences",
            "average_delta",
            "metadata",
            "_valid_differences",
            "_change_counts",
            "change_distribution_percentages",
            "biggest_increase",
            "biggest_decrease",
            "start_weighted_average",
            "end_weighted_average",
        ]:
            security_ratings_change_portfolio_data.__dict__.pop(attr, None)

    @staticmethod
    def _ratings_by_end_date(mapping):
        """Return a side_effect that serves ratings keyed by the requested end_date."""

        def side_effect(end_date=None):
            return mapping[end_date]

        return side_effect

    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_differences_computes_signed_deltas(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [
                        {"systemName": "up", "rating": 2.0},
                        {"systemName": "down", "rating": 4.0},
                        {"systemName": "flat", "rating": 3.0},
                    ],
                    "2025-12-31": [
                        {"systemName": "up", "rating": 3.5},
                        {"systemName": "down", "rating": 2.5},
                        {"systemName": "flat", "rating": 3.0},
                    ],
                }
            )
        )

        differences = security_ratings_change_portfolio_data.differences

        assert differences["up"] == pytest.approx(1.5)
        assert differences["down"] == pytest.approx(-1.5)
        assert differences["flat"] == pytest.approx(0.0)

    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_difference_is_none_when_system_absent_at_start(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [{"systemName": "existing", "rating": 2.0}],
                    "2025-12-31": [
                        {"systemName": "existing", "rating": 2.5},
                        {"systemName": "new", "rating": 4.0},
                    ],
                }
            )
        )

        assert security_ratings_change_portfolio_data.get_difference(
            "existing"
        ) == pytest.approx(0.5)
        assert security_ratings_change_portfolio_data.get_difference("new") is None

    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_get_difference_returns_none_for_unknown_system(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [{"systemName": "known", "rating": 2.0}],
                    "2025-12-31": [{"systemName": "known", "rating": 3.0}],
                }
            )
        )

        assert security_ratings_change_portfolio_data.get_difference("missing") is None

    @staticmethod
    def _volumes(mapping):
        """Return a portfolio-maintainability payload with the given per-system volumes."""
        return {
            "systems": [
                {"system": name, "volumeInPersonMonths": volume}
                for name, volume in mapping.items()
            ]
        }

    @patch("report_generator.generator.domain.portfolio.shared.utils.sigrid_api")
    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_average_delta_is_volume_weighted_mean_of_changes(
        self, mock_sigrid_api, mock_utils_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [
                        {"systemName": "up", "rating": 2.0},
                        {"systemName": "down", "rating": 4.0},
                    ],
                    "2025-12-31": [
                        {"systemName": "up", "rating": 3.0},
                        {"systemName": "down", "rating": 3.5},
                    ],
                }
            )
        )
        mock_utils_api.get_portfolio_maintainability.return_value = self._volumes(
            {"up": 3.0, "down": 1.0}
        )

        # (+1.0 * 3 + -0.5 * 1) / (3 + 1) = 2.5 / 4 = 0.625
        assert security_ratings_change_portfolio_data.average_delta == pytest.approx(
            0.625
        )

    @patch("report_generator.generator.domain.portfolio.shared.utils.sigrid_api")
    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_average_delta_excludes_systems_without_a_pair(
        self, mock_sigrid_api, mock_utils_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [{"systemName": "existing", "rating": 2.0}],
                    "2025-12-31": [
                        {"systemName": "existing", "rating": 3.0},
                        {"systemName": "new", "rating": 4.0},
                    ],
                }
            )
        )
        mock_utils_api.get_portfolio_maintainability.return_value = self._volumes(
            {"existing": 5.0, "new": 2.0}
        )

        # only "existing" has a start and end rating: delta = +1.0
        assert security_ratings_change_portfolio_data.average_delta == pytest.approx(
            1.0
        )

    @patch("report_generator.generator.domain.portfolio.shared.utils.sigrid_api")
    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_average_delta_excludes_systems_without_a_volume(
        self, mock_sigrid_api, mock_utils_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [
                        {"systemName": "known", "rating": 2.0},
                        {"systemName": "unsized", "rating": 4.0},
                    ],
                    "2025-12-31": [
                        {"systemName": "known", "rating": 3.0},
                        {"systemName": "unsized", "rating": 2.0},
                    ],
                }
            )
        )
        # "unsized" has a rating change but no volume entry, so it is skipped.
        mock_utils_api.get_portfolio_maintainability.return_value = self._volumes(
            {"known": 4.0}
        )

        assert security_ratings_change_portfolio_data.average_delta == pytest.approx(
            1.0
        )

    @patch("report_generator.generator.domain.portfolio.shared.utils.sigrid_api")
    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_average_delta_defaults_to_zero_without_comparable_systems(
        self, mock_sigrid_api, mock_utils_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [],
                    "2025-12-31": [{"systemName": "new", "rating": 4.0}],
                }
            )
        )
        mock_utils_api.get_portfolio_maintainability.return_value = self._volumes(
            {"new": 2.0}
        )

        assert security_ratings_change_portfolio_data.average_delta == 0.0

    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_change_distribution_percentages_counts_each_direction(
        self, mock_sigrid_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [
                        {"systemName": "up", "rating": 2.0},
                        {"systemName": "down", "rating": 4.0},
                        {"systemName": "flat", "rating": 3.0},
                    ],
                    "2025-12-31": [
                        {"systemName": "up", "rating": 3.5},
                        {"systemName": "down", "rating": 2.5},
                        {"systemName": "flat", "rating": 3.0},
                        # "new" has no start rating -> None delta -> not counted
                        {"systemName": "new", "rating": 4.0},
                    ],
                }
            )
        )

        distribution = (
            security_ratings_change_portfolio_data.change_distribution_percentages
        )

        # 3 comparable systems: 1 up, 1 down, 1 stable -> 33% each
        assert distribution == {"increased": 33, "stable": 33, "decreased": 33}

    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_change_distribution_percentages_all_zero_without_valid_deltas(
        self, mock_sigrid_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [],
                    "2025-12-31": [{"systemName": "new", "rating": 4.0}],
                }
            )
        )

        assert (
            security_ratings_change_portfolio_data.change_distribution_percentages
            == {
                "increased": 0,
                "stable": 0,
                "decreased": 0,
            }
        )

    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_biggest_increase_and_decrease_resolve_display_names(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [
                        {"systemName": "up", "rating": 2.0},
                        {"systemName": "small-up", "rating": 3.0},
                        {"systemName": "down", "rating": 4.0},
                    ],
                    "2025-12-31": [
                        {"systemName": "up", "rating": 3.5},  # +1.5 (biggest increase)
                        {"systemName": "small-up", "rating": 3.2},  # +0.2
                        {
                            "systemName": "down",
                            "rating": 2.0,
                        },  # -2.0 (biggest decrease)
                    ],
                }
            )
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "up", "displayName": "Up System"},
            {"systemName": "down", "displayName": "Down System"},
        ]

        assert security_ratings_change_portfolio_data.biggest_increase == (
            "Up System",
            1.5,
        )
        assert security_ratings_change_portfolio_data.biggest_decrease == (
            "Down System",
            -2.0,
        )

    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_biggest_increase_is_none_without_a_positive_mover(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [
                        {"systemName": "down", "rating": 4.0},
                        {"systemName": "flat", "rating": 3.0},
                    ],
                    "2025-12-31": [
                        {"systemName": "down", "rating": 2.0},
                        {"systemName": "flat", "rating": 3.0},
                    ],
                }
            )
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "down", "displayName": "Down System"},
        ]

        assert security_ratings_change_portfolio_data.biggest_increase is None
        assert security_ratings_change_portfolio_data.biggest_decrease == (
            "Down System",
            -2.0,
        )

    @patch("report_generator.generator.domain.portfolio.shared.utils.sigrid_api")
    @patch("report_generator.generator.domain.portfolio.security_portfolio.sigrid_api")
    def test_start_and_end_weighted_averages_are_volume_weighted(
        self, mock_sigrid_api, mock_utils_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_security_ratings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": [
                        {"systemName": "up", "rating": 2.0},
                        {"systemName": "down", "rating": 4.0},
                    ],
                    "2025-12-31": [
                        {"systemName": "up", "rating": 3.0},
                        {"systemName": "down", "rating": 3.5},
                    ],
                }
            )
        )
        mock_utils_api.get_portfolio_maintainability.return_value = self._volumes(
            {"up": 3.0, "down": 1.0}
        )

        # start: (2*3 + 4*1) / 4 = 2.5 ; end: (3*3 + 3.5*1) / 4 = 3.125
        assert (
            security_ratings_change_portfolio_data.start_weighted_average
            == pytest.approx(2.5)
        )
        assert (
            security_ratings_change_portfolio_data.end_weighted_average
            == pytest.approx(3.125)
        )


class TestSecurityDashboardFindingsPortfolioData:
    """Test cases for SecurityDashboardFindingsPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = ["data", "metadata", "system_names"]
        for attr in cache_attrs:
            security_dashboard_findings_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.security_dashboard_findings_portfolio.sigrid_api"
    )
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = {
            "systems": [
                {"system": "system1", "findings": [{"severity": "HIGH"}]},
                {"system": "system2", "findings": [{"severity": "LOW"}]},
            ]
        }
        mock_sigrid_api.get_portfolio_security_dashboard_findings.return_value = (
            mock_data
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "system1"},
            {"systemName": "system2"},
        ]

        security_dashboard_findings_portfolio_data.__dict__.pop("data", None)

        system = security_dashboard_findings_portfolio_data.get_system("system1")

        assert system is not None
        assert system["system"] == "system1"
        assert len(system["findings"]) == 1

    @patch(
        "report_generator.generator.domain.portfolio.security_dashboard_findings_portfolio.sigrid_api"
    )
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = {
            "systems": [
                {"system": "system1", "findings": []},
                {"system": "system2", "findings": []},
                {"system": "system3", "findings": []},
            ]
        }
        mock_sigrid_api.get_portfolio_security_dashboard_findings.return_value = (
            mock_data
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "system1"},
            {"systemName": "system2"},
            {"systemName": "system3"},
        ]

        for attr in ["data", "system_names"]:
            security_dashboard_findings_portfolio_data.__dict__.pop(attr, None)

        names = security_dashboard_findings_portfolio_data.system_names

        assert len(names) == 3
        assert "system1" in names
        assert "system2" in names
        assert "system3" in names

    @patch(
        "report_generator.generator.domain.portfolio.security_dashboard_findings_portfolio.sigrid_api"
    )
    def test_excluded_systems_are_filtered_from_data(self, mock_sigrid_api):
        """Test that systems absent from metadata are excluded from data."""
        mock_data = {
            "systems": [
                {"system": "active_system", "findingRatio": []},
                {"system": "excluded_system", "findingRatio": []},
            ]
        }
        mock_sigrid_api.get_portfolio_security_dashboard_findings.return_value = (
            mock_data
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "active_system"},
        ]

        security_dashboard_findings_portfolio_data.__dict__.pop("data", None)

        data = security_dashboard_findings_portfolio_data.data

        system_names = [s["system"] for s in data["systems"]]
        assert system_names == ["active_system"]
        assert "excluded_system" not in system_names


class TestSecurityDashboardResolutionTimesPortfolioData:
    """Test cases for SecurityDashboardResolutionTimesPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = ["data", "metadata", "system_names"]
        for attr in cache_attrs:
            security_dashboard_resolution_times_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.security_dashboard_resolution_times_portfolio.sigrid_api"
    )
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = {
            "systems": [
                {"system": "system1", "avgResolutionTime": 15.5},
                {"system": "system2", "avgResolutionTime": 20.3},
            ]
        }
        mock_sigrid_api.get_portfolio_security_resolution_time_findings.return_value = (
            mock_data
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "system1"},
            {"systemName": "system2"},
        ]

        security_dashboard_resolution_times_portfolio_data.__dict__.pop("data", None)

        system = security_dashboard_resolution_times_portfolio_data.get_system(
            "system1"
        )

        assert system is not None
        assert system["system"] == "system1"
        assert abs(system["avgResolutionTime"] - 15.5) < 0.01

    @patch(
        "report_generator.generator.domain.portfolio.security_dashboard_resolution_times_portfolio.sigrid_api"
    )
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = {
            "systems": [
                {"system": "system1", "avgResolutionTime": 15.5},
                {"system": "system2", "avgResolutionTime": 20.3},
                {"system": "system3", "avgResolutionTime": 10.0},
            ]
        }
        mock_sigrid_api.get_portfolio_security_resolution_time_findings.return_value = (
            mock_data
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "system1"},
            {"systemName": "system2"},
            {"systemName": "system3"},
        ]

        for attr in ["data", "system_names"]:
            security_dashboard_resolution_times_portfolio_data.__dict__.pop(attr, None)

        names = security_dashboard_resolution_times_portfolio_data.system_names

        assert len(names) == 3
        assert "system1" in names
        assert "system2" in names
        assert "system3" in names

    @patch(
        "report_generator.generator.domain.portfolio.security_dashboard_resolution_times_portfolio.sigrid_api"
    )
    def test_excluded_systems_are_filtered_from_data(self, mock_sigrid_api):
        """Test that systems absent from metadata are excluded from data."""
        mock_data = {
            "systems": [
                {"system": "active_system", "resolutionTimes": []},
                {"system": "excluded_system", "resolutionTimes": []},
            ]
        }
        mock_sigrid_api.get_portfolio_security_resolution_time_findings.return_value = (
            mock_data
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "active_system"},
        ]

        security_dashboard_resolution_times_portfolio_data.__dict__.pop("data", None)

        data = security_dashboard_resolution_times_portfolio_data.data

        system_names = [s["system"] for s in data["systems"]]
        assert system_names == ["active_system"]
        assert "excluded_system" not in system_names


class TestCountFindingsAboveSeverity:
    """Unit tests for count_findings_above_severity helper."""

    def test_counts_findings_strictly_above_target(self):
        findings = [
            {"severity": "LOW"},
            {"severity": "MEDIUM"},
            {"severity": "HIGH"},
            {"severity": "CRITICAL"},
        ]
        assert count_findings_above_severity(findings, "MEDIUM") == 2

    def test_target_at_highest_returns_zero(self):
        findings = [{"severity": "HIGH"}, {"severity": "CRITICAL"}]
        assert count_findings_above_severity(findings, "CRITICAL") == 0

    def test_target_at_lowest_counts_all_above(self):
        findings = [
            {"severity": "LOW"},
            {"severity": "MEDIUM"},
            {"severity": "HIGH"},
        ]
        assert count_findings_above_severity(findings, "INFORMATION") == 3

    def test_unknown_target_severity_returns_zero(self):
        findings = [{"severity": "HIGH"}]
        assert count_findings_above_severity(findings, "UNKNOWN") == 0

    def test_unknown_finding_severity_is_skipped(self):
        findings = [{"severity": "UNKNOWN"}, {"severity": "CRITICAL"}]
        assert count_findings_above_severity(findings, "HIGH") == 1

    def test_empty_findings_returns_zero(self):
        assert count_findings_above_severity([], "MEDIUM") == 0


class TestCountFindingsAboveObjective:
    """Unit tests for count_findings_above_objective helper."""

    def test_no_objective_counts_high_and_critical(self):
        findings = [
            {"severity": "LOW"},
            {"severity": "MEDIUM"},
            {"severity": "HIGH"},
            {"severity": "CRITICAL"},
        ]
        assert count_findings_above_objective(
            findings, None
        ) == count_findings_above_severity(findings, FALLBACK_SEVERITY_THRESHOLD)

    def test_objective_met_returns_zero(self):
        findings = [{"severity": "CRITICAL"}]
        objective = {"targetMetAtEnd": "MET", "target": "HIGH"}
        assert count_findings_above_objective(findings, objective) == 0

    def test_objective_not_met_delegates_to_count_helper(self):
        findings = [
            {"severity": "LOW"},
            {"severity": "HIGH"},
            {"severity": "CRITICAL"},
        ]
        objective = {"targetMetAtEnd": "NOT_MET", "target": "LOW"}
        assert count_findings_above_objective(findings, objective) == 2


class TestFindingsAboveObjective:
    """Integration-style tests for SecurityRatingsPortfolioData.findings_above_objective."""

    def _make_instance(self, ratings_data):
        instance = SecurityRatingsPortfolioData()
        instance.__dict__["data"] = ratings_data
        instance.__dict__["system_names"] = [s["systemName"] for s in ratings_data]
        return instance

    @patch(
        "report_generator.generator.domain.portfolio.shared.findings_portfolio_base.sigrid_api"
    )
    def test_objective_met_returns_zero(self, mock_api):
        instance = self._make_instance([{"systemName": "sys1", "rating": 4.0}])
        instance.__dict__["_raw_findings"] = [
            {"systemName": "sys1", "findings": [{"severity": "CRITICAL"}]}
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "systemName": "sys1",
                    "objectives": [
                        {
                            "type": "SECURITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "MET",
                        }
                    ],
                }
            ]
        }

        result = instance.findings_above_objective
        assert result == [{"systemName": "sys1", "findings_above_objective": 0}]

    @patch(
        "report_generator.generator.domain.portfolio.shared.findings_portfolio_base.sigrid_api"
    )
    def test_no_objective_uses_fallback(self, mock_api):
        instance = self._make_instance([{"systemName": "sys1", "rating": 3.0}])
        instance.__dict__["_raw_findings"] = [
            {
                "systemName": "sys1",
                "findings": [
                    {"severity": "LOW"},
                    {"severity": "HIGH"},
                    {"severity": "CRITICAL"},
                ],
            }
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {"systems": []}

        result = instance.findings_above_objective
        assert result == [{"systemName": "sys1", "findings_above_objective": 2}]

    @patch(
        "report_generator.generator.domain.portfolio.shared.findings_portfolio_base.sigrid_api"
    )
    def test_objective_not_met_counts_above_target(self, mock_api):
        instance = self._make_instance([{"systemName": "sys1", "rating": 2.5}])
        instance.__dict__["_raw_findings"] = [
            {
                "systemName": "sys1",
                "findings": [
                    {"severity": "LOW"},
                    {"severity": "HIGH"},
                    {"severity": "CRITICAL"},
                ],
            }
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "systemName": "sys1",
                    "objectives": [
                        {
                            "type": "SECURITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "NOT_MET",
                        }
                    ],
                }
            ]
        }

        result = instance.findings_above_objective
        assert result == [{"systemName": "sys1", "findings_above_objective": 1}]

    @patch(
        "report_generator.generator.domain.portfolio.shared.findings_portfolio_base.sigrid_api"
    )
    def test_multiple_systems_mixed_objectives(self, mock_api):
        instance = self._make_instance(
            [
                {"systemName": "sys1", "rating": 4.0},
                {"systemName": "sys2", "rating": 3.0},
                {"systemName": "sys3", "rating": 2.0},
            ]
        )
        instance.__dict__["_raw_findings"] = [
            {"systemName": "sys1", "findings": [{"severity": "CRITICAL"}]},
            {
                "systemName": "sys2",
                "findings": [{"severity": "HIGH"}, {"severity": "CRITICAL"}],
            },
            {
                "systemName": "sys3",
                "findings": [{"severity": "LOW"}, {"severity": "HIGH"}],
            },
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "systemName": "sys1",
                    "objectives": [
                        {
                            "type": "SECURITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "MET",
                        }
                    ],
                },
                {
                    "systemName": "sys2",
                    "objectives": [
                        {
                            "type": "SECURITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "NOT_MET",
                        }
                    ],
                },
                {
                    "systemName": "sys3",
                    "objectives": [],
                },
            ]
        }

        result = instance.findings_above_objective
        assert result == [
            {"systemName": "sys1", "findings_above_objective": 0},
            {"systemName": "sys2", "findings_above_objective": 1},
            {"systemName": "sys3", "findings_above_objective": 1},
        ]

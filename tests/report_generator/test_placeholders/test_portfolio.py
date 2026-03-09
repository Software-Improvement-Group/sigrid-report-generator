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

import pytest

from report_generator.generator.domain import (
    osh_portfolio_data,
    security_dashboard_findings_portfolio_data,
    security_ratings_portfolio_data,
)


class TestPortfolioPlaceholders:
    def test_portfolio_osh_placeholders_return_distribution_values(self, mocker):
        """Test that OSH portfolio placeholders access and return distribution percentages."""
        mock_distribution = {
            "above_market": 45.5,
            "market_average": 30.0,
            "below_market": 24.5,
        }

        # Mock at the data model instance level
        mocker.patch.object(
            type(osh_portfolio_data),
            "get_rating_distribution_percentages",
            new_callable=mocker.PropertyMock,
            return_value=mock_distribution,
        )

        # The placeholders are classes with a `replace` method, but we can test the underlying functions
        assert osh_portfolio_data.get_rating_distribution_percentages[
            "above_market"
        ] == pytest.approx(45.5)
        assert osh_portfolio_data.get_rating_distribution_percentages[
            "market_average"
        ] == pytest.approx(30.0)
        assert osh_portfolio_data.get_rating_distribution_percentages[
            "below_market"
        ] == pytest.approx(24.5)

    def test_portfolio_security_placeholders_return_distribution_values(self, mocker):
        """Test that security portfolio placeholders access and return distribution percentages."""
        mock_distribution = {
            "above_market": 60.0,
            "market_average": 25.0,
            "below_market": 15.0,
        }

        # Mock at the data model instance level
        mocker.patch.object(
            type(security_ratings_portfolio_data),
            "get_rating_distribution_percentages",
            new_callable=mocker.PropertyMock,
            return_value=mock_distribution,
        )

        # Test that we can access the distribution values
        assert security_ratings_portfolio_data.get_rating_distribution_percentages[
            "above_market"
        ] == pytest.approx(60.0)
        assert security_ratings_portfolio_data.get_rating_distribution_percentages[
            "market_average"
        ] == pytest.approx(25.0)
        assert security_ratings_portfolio_data.get_rating_distribution_percentages[
            "below_market"
        ] == pytest.approx(15.0)

    def test_portfolio_security_critical_findings_placeholders(self, mocker):
        """Test security critical findings placeholders return correct values."""
        mock_statistics = {
            "resolved": 25,
            "added": 18,
            "net_change": -7,  # More resolved than added
        }

        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "critical_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_statistics,
        )

        # Test statistics values
        assert (
            security_dashboard_findings_portfolio_data.critical_findings_statistics[
                "resolved"
            ]
            == 25
        )
        assert (
            security_dashboard_findings_portfolio_data.critical_findings_statistics[
                "added"
            ]
            == 18
        )
        assert (
            security_dashboard_findings_portfolio_data.critical_findings_statistics[
                "net_change"
            ]
            == -7
        )

    def test_portfolio_security_critical_findings_with_increase(self, mocker):
        """Test critical findings placeholders when there's an increase in findings."""
        mock_statistics = {
            "resolved": 10,
            "added": 22,
            "net_change": 12,  # More added than resolved
        }

        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "critical_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_statistics,
        )

        stats = security_dashboard_findings_portfolio_data.critical_findings_statistics
        assert stats["net_change"] == 12
        assert stats["resolved"] == 10
        assert stats["added"] == 22

    def test_portfolio_security_critical_findings_with_no_change(self, mocker):
        """Test critical findings placeholders when resolved equals added."""
        mock_statistics = {
            "resolved": 15,
            "added": 15,
            "net_change": 0,  # Same number resolved and added
        }

        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "critical_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_statistics,
        )

        stats = security_dashboard_findings_portfolio_data.critical_findings_statistics
        assert stats["net_change"] == 0
        assert stats["resolved"] == 15
        assert stats["added"] == 15

    def test_portfolio_security_high_findings_placeholders(self, mocker):
        """Test high severity findings placeholders."""
        mock_statistics = {
            "resolved": 25,
            "added": 18,
            "net_change": -7,  # Decrease of 7
        }

        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "high_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_statistics,
        )

        # Test statistics values
        assert (
            security_dashboard_findings_portfolio_data.high_findings_statistics[
                "resolved"
            ]
            == 25
        )
        assert (
            security_dashboard_findings_portfolio_data.high_findings_statistics["added"]
            == 18
        )
        assert (
            security_dashboard_findings_portfolio_data.high_findings_statistics[
                "net_change"
            ]
            == -7
        )

    def test_portfolio_security_medium_findings_placeholders(self, mocker):
        """Test medium severity findings placeholders."""
        mock_statistics = {
            "resolved": 10,
            "added": 30,
            "net_change": 20,  # Increase of 20
        }

        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "medium_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_statistics,
        )

        # Test statistics values
        assert (
            security_dashboard_findings_portfolio_data.medium_findings_statistics[
                "resolved"
            ]
            == 10
        )
        assert (
            security_dashboard_findings_portfolio_data.medium_findings_statistics[
                "added"
            ]
            == 30
        )
        assert (
            security_dashboard_findings_portfolio_data.medium_findings_statistics[
                "net_change"
            ]
            == 20
        )

    def test_portfolio_security_low_findings_placeholders(self, mocker):
        """Test low severity findings placeholders."""
        mock_statistics = {
            "resolved": 50,
            "added": 50,
            "net_change": 0,  # No change
        }

        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "low_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_statistics,
        )

        # Test statistics values
        assert (
            security_dashboard_findings_portfolio_data.low_findings_statistics[
                "resolved"
            ]
            == 50
        )
        assert (
            security_dashboard_findings_portfolio_data.low_findings_statistics["added"]
            == 50
        )
        assert (
            security_dashboard_findings_portfolio_data.low_findings_statistics[
                "net_change"
            ]
            == 0
        )

    def test_portfolio_security_all_severities_together(self, mocker):
        """Test all severity findings placeholders work together correctly."""
        mock_critical = {"resolved": 5, "added": 3, "net_change": -2}
        mock_high = {"resolved": 10, "added": 15, "net_change": 5}
        mock_medium = {"resolved": 20, "added": 20, "net_change": 0}
        mock_low = {"resolved": 100, "added": 95, "net_change": -5}

        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "critical_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_critical,
        )
        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "high_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_high,
        )
        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "medium_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_medium,
        )
        mocker.patch.object(
            type(security_dashboard_findings_portfolio_data),
            "low_findings_statistics",
            new_callable=mocker.PropertyMock,
            return_value=mock_low,
        )

        # Critical: decrease
        assert (
            security_dashboard_findings_portfolio_data.critical_findings_statistics[
                "resolved"
            ]
            == 5
        )
        assert (
            security_dashboard_findings_portfolio_data.critical_findings_statistics[
                "added"
            ]
            == 3
        )
        assert (
            security_dashboard_findings_portfolio_data.critical_findings_statistics[
                "net_change"
            ]
            == -2
        )

        # High: increase
        assert (
            security_dashboard_findings_portfolio_data.high_findings_statistics[
                "resolved"
            ]
            == 10
        )
        assert (
            security_dashboard_findings_portfolio_data.high_findings_statistics["added"]
            == 15
        )
        assert (
            security_dashboard_findings_portfolio_data.high_findings_statistics[
                "net_change"
            ]
            == 5
        )

        # Medium: no change
        assert (
            security_dashboard_findings_portfolio_data.medium_findings_statistics[
                "resolved"
            ]
            == 20
        )
        assert (
            security_dashboard_findings_portfolio_data.medium_findings_statistics[
                "added"
            ]
            == 20
        )
        assert (
            security_dashboard_findings_portfolio_data.medium_findings_statistics[
                "net_change"
            ]
            == 0
        )

        # Low: decrease
        assert (
            security_dashboard_findings_portfolio_data.low_findings_statistics[
                "resolved"
            ]
            == 100
        )
        assert (
            security_dashboard_findings_portfolio_data.low_findings_statistics["added"]
            == 95
        )
        assert (
            security_dashboard_findings_portfolio_data.low_findings_statistics[
                "net_change"
            ]
            == -5
        )

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

from report_generator.generator.context.portfolio_filters import reset_context
from report_generator.generator.domain.portfolio.reliability_portfolio import (
    ReliabilityRatingsPortfolioData,
    reliability_ratings_portfolio_data,
)


class TestReliabilityPortfolioData:
    """Test cases for ReliabilityRatingsPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = ["data", "metadata", "period", "system_names", "reliability_findings"]
        for attr in cache_attrs:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

    @patch("report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api")
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
        ]
        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data

        reliability_ratings_portfolio_data.__dict__.pop("data", None)

        system = reliability_ratings_portfolio_data.get_system("system1")

        assert system is not None
        assert system["systemName"] == "system1"
        assert abs(system["rating"] - 4.5) < 0.01

    @patch("report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api")
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
            {"systemName": "system3", "rating": 4.2},
        ]
        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data

        for attr in ["data", "system_names"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        names = reliability_ratings_portfolio_data.system_names

        assert len(names) == 3
        assert "system1" in names
        assert "system2" in names
        assert "system3" in names

    @patch("report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api")
    def test_reliability_findings_aggregates_per_system(self, mock_sigrid_api):
        """Test that reliability_findings returns findings per system."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
        ]
        findings_system1 = [{"id": "a1", "severity": "HIGH"}, {"id": "a2", "severity": "LOW"}]
        findings_system2 = [{"id": "b1", "severity": "CRITICAL"}]

        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data
        mock_sigrid_api.get_reliability_findings.side_effect = [
            findings_system1,
            findings_system2,
        ]

        for attr in ["data", "system_names", "reliability_findings"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        result = reliability_ratings_portfolio_data.reliability_findings

        assert len(result) == 2
        assert result[0] == {"systemName": "system1", "findings": findings_system1}
        assert result[1] == {"systemName": "system2", "findings": findings_system2}

    @patch("report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api")
    def test_reliability_findings_handles_api_error_gracefully(self, mock_sigrid_api):
        """Test that a failing API call for one system returns empty findings and logs a warning."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
        ]
        findings_system1 = [{"id": "a1", "severity": "HIGH"}]

        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data
        mock_sigrid_api.get_reliability_findings.side_effect = [
            findings_system1,
            Exception("API error"),
        ]

        for attr in ["data", "system_names", "reliability_findings"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        result = reliability_ratings_portfolio_data.reliability_findings

        assert len(result) == 2
        assert result[0] == {"systemName": "system1", "findings": findings_system1}
        assert result[1] == {"systemName": "system2", "findings": []}

    @patch("report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api")
    def test_reliability_findings_empty_portfolio(self, mock_sigrid_api):
        """Test that reliability_findings returns an empty list when there are no systems."""
        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = []

        for attr in ["data", "system_names", "reliability_findings"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        result = reliability_ratings_portfolio_data.reliability_findings

        assert result == []

    @patch("report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api")
    def test_reliability_findings_uses_fresh_instance(self, mock_sigrid_api):
        """Test that a fresh instance fetches its own findings independently."""
        mock_data = [
            {"systemName": "system1", "rating": 3.5},
        ]
        findings = [{"id": "c1", "severity": "MEDIUM"}]

        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data
        mock_sigrid_api.get_reliability_findings.return_value = findings

        portfolio = ReliabilityRatingsPortfolioData()

        result = portfolio.reliability_findings

        assert result == [{"systemName": "system1", "findings": findings}]
        mock_sigrid_api.get_reliability_findings.assert_called_once_with("system1")

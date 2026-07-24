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
from report_generator.generator.domain.portfolio.architecture_portfolio import (
    architecture_portfolio_data,
)


class TestArchitecturePortfolioData:
    """Test cases for ArchitecturePortfolioData model."""

    def setup_method(self):
        """Reset portfolio context before each test."""
        reset_context()

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = ["data", "metadata", "period", "system_names"]
        for attr in cache_attrs:
            architecture_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = [
            {"system": "system1", "architectureQuality": 4.5},
            {"system": "system2", "architectureQuality": 3.8},
        ]
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = mock_data

        architecture_portfolio_data.__dict__.pop("data", None)

        system = architecture_portfolio_data.get_system("system1")

        assert system is not None
        assert system["system"] == "system1"
        assert abs(system["architectureQuality"] - 4.5) < 0.01

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = [
            {"system": "system1", "architectureQuality": 4.5},
            {"system": "system2", "architectureQuality": 3.8},
            {"system": "system3", "architectureQuality": 4.2},
        ]
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = mock_data

        for attr in ["data", "system_names"]:
            architecture_portfolio_data.__dict__.pop(attr, None)

        names = architecture_portfolio_data.system_names

        assert len(names) == 3
        assert "system1" in names
        assert "system2" in names
        assert "system3" in names


def _arch_ratings(mapping):
    """Build an architecture-quality payload with the given per-system ratings."""
    return [
        {"system": name, "ratings": {"architecture": rating}}
        for name, rating in mapping.items()
    ]


class TestArchitecturePortfolioDataChange:
    """Test cases for the per-system rating delta on ArchitecturePortfolioData."""

    def teardown_method(self):
        reset_context()
        for attr in [
            "data",
            "_start_ratings",
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
            architecture_portfolio_data.__dict__.pop(attr, None)

    @staticmethod
    def _ratings_by_end_date(mapping):
        """Return a side_effect that serves ratings keyed by the requested end_date."""

        def side_effect(end_date=None):
            return mapping[end_date]

        return side_effect

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_differences_computes_signed_deltas(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings({"up": 2.0, "down": 4.0, "flat": 3.0}),
                    "2025-12-31": _arch_ratings({"up": 3.5, "down": 2.5, "flat": 3.0}),
                }
            )
        )

        differences = architecture_portfolio_data.differences

        assert differences["up"] == pytest.approx(1.5)
        assert differences["down"] == pytest.approx(-1.5)
        assert differences["flat"] == pytest.approx(0.0)

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_difference_is_none_when_system_absent_at_start(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings({"existing": 2.0}),
                    "2025-12-31": _arch_ratings({"existing": 2.5, "new": 4.0}),
                }
            )
        )

        assert architecture_portfolio_data.get_difference("existing") == pytest.approx(
            0.5
        )
        assert architecture_portfolio_data.get_difference("new") is None

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_get_difference_returns_none_for_unknown_system(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings({"known": 2.0}),
                    "2025-12-31": _arch_ratings({"known": 3.0}),
                }
            )
        )

        assert architecture_portfolio_data.get_difference("missing") is None

    @patch("report_generator.generator.domain.portfolio.shared.utils.sigrid_api")
    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_average_delta_is_difference_of_volume_weighted_averages(
        self, mock_sigrid_api, mock_utils_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings({"up": 2.0, "down": 4.0}),
                    "2025-12-31": _arch_ratings({"up": 3.0, "down": 3.5}),
                }
            )
        )
        mock_utils_api.get_portfolio_maintainability.return_value = {
            "systems": [
                {"system": "up", "volumeInPersonMonths": 1.0},
                {"system": "down", "volumeInPersonMonths": 3.0},
            ]
        }

        # start avg = (2*1 + 4*3)/4 = 3.5 ; end avg = (3*1 + 3.5*3)/4 = 3.375
        assert architecture_portfolio_data.average_delta == pytest.approx(-0.125)

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_change_distribution_percentages(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings(
                        {"up": 2.0, "down": 4.0, "flat": 3.0, "flat2": 3.0}
                    ),
                    "2025-12-31": _arch_ratings(
                        {"up": 3.0, "down": 2.0, "flat": 3.0, "flat2": 3.0}
                    ),
                }
            )
        )

        assert architecture_portfolio_data.change_distribution_percentages == {
            "increased": 25,
            "stable": 50,
            "decreased": 25,
        }

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_biggest_increase_and_decrease_resolve_display_names(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            self._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings(
                        {"up": 2.0, "small-up": 3.0, "down": 4.0}
                    ),
                    "2025-12-31": _arch_ratings(
                        {"up": 3.5, "small-up": 3.2, "down": 2.0}
                    ),
                }
            )
        )
        mock_sigrid_api.get_portfolio_metadata.return_value = [
            {"systemName": "up", "displayName": "Up System"},
            {"systemName": "down", "displayName": "Down System"},
        ]

        assert architecture_portfolio_data.biggest_increase == (
            "Up System",
            1.5,
        )
        assert architecture_portfolio_data.biggest_decrease == (
            "Down System",
            -2.0,
        )

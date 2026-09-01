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

from report_generator.generator.context.portfolio_metadata import reset_context
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


def _arch_ratings_with_properties(mapping):
    """Build an architecture-quality payload with per-system property ratings."""
    return [
        {"system": name, "ratings": {"systemProperties": properties}}
        for name, properties in mapping.items()
    ]


class TestArchitecturePortfolioDataPropertyRatings:
    """Test cases for per-metric (systemProperties) ratings and deltas."""

    def teardown_method(self):
        reset_context()
        for attr in ["data", "_start_ratings", "metadata"]:
            architecture_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_get_property_rating_returns_metric_value(self, mock_sigrid_api):
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = (
            _arch_ratings_with_properties({"system1": {"componentCoupling": 5.08685}})
        )

        rating = architecture_portfolio_data.get_property_rating(
            "system1", "componentCoupling"
        )

        assert rating == pytest.approx(5.08685)

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_get_property_rating_returns_none_for_unknown_system(self, mock_sigrid_api):
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = (
            _arch_ratings_with_properties({"system1": {"componentCoupling": 5.0}})
        )

        assert (
            architecture_portfolio_data.get_property_rating(
                "missing", "componentCoupling"
            )
            is None
        )

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_get_property_difference_computes_signed_delta(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            TestArchitecturePortfolioDataChange._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings_with_properties(
                        {"system1": {"componentCoupling": 2.0}}
                    ),
                    "2025-12-31": _arch_ratings_with_properties(
                        {"system1": {"componentCoupling": 3.5}}
                    ),
                }
            )
        )

        difference = architecture_portfolio_data.get_property_difference(
            "system1", "componentCoupling"
        )

        assert difference == pytest.approx(1.5)

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_get_property_difference_is_none_when_system_absent_at_start(
        self, mock_sigrid_api
    ):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            TestArchitecturePortfolioDataChange._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings_with_properties({}),
                    "2025-12-31": _arch_ratings_with_properties(
                        {"system1": {"componentCoupling": 3.5}}
                    ),
                }
            )
        )

        difference = architecture_portfolio_data.get_property_difference(
            "system1", "componentCoupling"
        )

        assert difference is None


class TestArchitecturePortfolioDataMetricParams:
    """Test cases for the per-metric (systemProperties) change/rating helpers."""

    def teardown_method(self):
        reset_context()
        for attr in ["data", "_start_ratings", "metadata"]:
            architecture_portfolio_data.__dict__.pop(attr, None)
        architecture_portfolio_data.change_distribution_percentages_for_metric.cache_clear()
        architecture_portfolio_data.biggest_increase_for_metric.cache_clear()
        architecture_portfolio_data.biggest_decrease_for_metric.cache_clear()

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_change_distribution_percentages_for_metric(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            TestArchitecturePortfolioDataChange._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings_with_properties(
                        {
                            "up": {"componentCoupling": 2.0},
                            "down": {"componentCoupling": 4.0},
                            "flat": {"componentCoupling": 3.0},
                        }
                    ),
                    "2025-12-31": _arch_ratings_with_properties(
                        {
                            "up": {"componentCoupling": 3.0},
                            "down": {"componentCoupling": 2.0},
                            "flat": {"componentCoupling": 3.0},
                        }
                    ),
                }
            )
        )

        result = architecture_portfolio_data.change_distribution_percentages_for_metric(
            "componentCoupling"
        )

        assert result == {"increased": 33, "stable": 33, "decreased": 33}

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_biggest_increase_and_decrease_for_metric(self, mock_sigrid_api):
        mock_sigrid_api.get_period.return_value = ("2025-01-01", "2025-12-31")
        mock_sigrid_api.get_portfolio_metadata.return_value = []
        mock_sigrid_api.get_portfolio_architecture_findings.side_effect = (
            TestArchitecturePortfolioDataChange._ratings_by_end_date(
                {
                    "2025-01-01": _arch_ratings_with_properties(
                        {
                            "up": {"componentCoupling": 2.0},
                            "down": {"componentCoupling": 4.0},
                        }
                    ),
                    "2025-12-31": _arch_ratings_with_properties(
                        {
                            "up": {"componentCoupling": 3.5},
                            "down": {"componentCoupling": 2.0},
                        }
                    ),
                }
            )
        )

        assert architecture_portfolio_data.biggest_increase_for_metric(
            "componentCoupling"
        ) == ("up", 1.5)
        assert architecture_portfolio_data.biggest_decrease_for_metric(
            "componentCoupling"
        ) == ("down", -2.0)

    @patch("report_generator.generator.domain.portfolio.shared.utils.sigrid_api")
    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_weighted_average_rating_for_metric(self, mock_sigrid_api, mock_utils_api):
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = (
            _arch_ratings_with_properties(
                {
                    "a": {"componentCoupling": 2.0},
                    "b": {"componentCoupling": 4.0},
                }
            )
        )
        mock_utils_api.get_portfolio_maintainability.return_value = {
            "systems": [
                {"system": "a", "volumeInPersonMonths": 1.0},
                {"system": "b", "volumeInPersonMonths": 3.0},
            ]
        }

        rating = architecture_portfolio_data.weighted_average_rating_for_metric(
            "componentCoupling"
        )

        assert rating == pytest.approx((2.0 * 1 + 4.0 * 3) / 4)

    @patch(
        "report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api"
    )
    def test_rating_distribution_percentages_for_metric(self, mock_sigrid_api):
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = (
            _arch_ratings_with_properties(
                {
                    "high": {"componentCoupling": 4.0},
                    "mid": {"componentCoupling": 3.0},
                    "low": {"componentCoupling": 1.0},
                }
            )
        )

        distribution = (
            architecture_portfolio_data.rating_distribution_percentages_for_metric(
                "componentCoupling"
            )
        )

        assert distribution == {
            "above_market": 33,
            "market_average": 33,
            "below_market": 33,
        }

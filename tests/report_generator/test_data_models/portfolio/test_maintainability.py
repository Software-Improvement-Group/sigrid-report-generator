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

from report_generator.generator.context import portfolio_filters
from report_generator.generator.domain import maintainability_portfolio_data

# noinspection PyProtectedMember
from report_generator.generator.domain.portfolio.maintainability_delta_quality_portfolio import (
    _AbstractMaintainabilityDeltaQualityPortfolioData,
)
from report_generator.generator.domain.portfolio.maintainability_portfolio.data import (
    is_system_active,
    parse_date,
)
from report_generator.generator.domain.portfolio.maintainability_portfolio.statistics import (
    MaintainabilityPortfolioStats,
    _finalize_change_statistics,
    _initialize_statistics,
    _update_star_statistics,
    _weighted_avg,
)


class TestMaintainabilityStatistics:
    """Test the statistics cached property for maintainability portfolio."""

    def test_statistics_with_changes(self, mocker):
        """Test statistics calculation with systems that have increased, decreased, and stayed stable."""
        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3", "system4"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        # Mock period
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        # System 1: Improved from 2.5 (3 stars) to 3.5 (4 stars) - diff = 1.0
        # System 2: Declined from 4.5 (5 stars) to 3.5 (4 stars) - diff = -1.0
        # System 3: Stable at 3.5 (4 stars) - diff = 0.0
        # System 4: Improved from 3.0 (3 stars) to 3.8 (4 stars) - diff = 0.8

        def mock_start_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 2.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 4.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 200,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 150,
                },
                "system4": {
                    "maintainability": 3.0,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 50,
                },
            }
            return snapshots[system_name]

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 200,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 150,
                },
                "system4": {
                    "maintainability": 3.8,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 50,
                },
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Verify star distribution (all systems are 4 stars at end)
        assert stats["maintainability"]["1-star"] == 0
        assert stats["maintainability"]["2-star"] == 0
        assert stats["maintainability"]["3-star"] == 0
        assert (
            stats["maintainability"]["4-star"] == 4
        )  # All systems end at 3.5-3.8 which is 4 stars
        assert stats["maintainability"]["5-star"] == 0
        assert stats["maintainability"]["number-of-systems"] == 4

        # Verify change counts (system4 improved from 3 stars to 4 stars)
        assert (
            stats["maintainability-change"]["systems-increased"] == 2
        )  # system1 (2→4), system4 (3→4)
        assert (
            stats["maintainability-change"]["systems-decreased"] == 1
        )  # system2 (4→4 but rating decreased)
        assert (
            stats["maintainability-change"]["systems-stable"] == 1
        )  # system3 (4→4 and stable rating)

        # Verify biggest changes
        assert "system1" in stats["maintainability-change"]["biggest-increase"]
        assert stats["maintainability-change"]["biggest-increase"][
            "system1"
        ] == pytest.approx(1.0)
        assert "system2" in stats["maintainability-change"]["biggest-decrease"]
        assert stats["maintainability-change"]["biggest-decrease"][
            "system2"
        ] == pytest.approx(-1.0)

        # Verify averages exist
        assert "start-average" in stats["maintainability"]
        assert "end-average" in stats["maintainability"]

    def test_statistics_all_stable(self, mocker):
        """Test statistics when all systems remain stable."""
        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        def mock_start_snapshot(system_name):
            return {
                "maintainability": 3.5,
                "maintainabilityDate": "2024-02-01",
                "volumeInPersonMonths": 100,
            }

        def mock_end_snapshot(system_name):
            return {
                "maintainability": 3.5,
                "maintainabilityDate": "2024-12-31",
                "volumeInPersonMonths": 100,
            }

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        assert stats["maintainability-change"]["systems-increased"] == 0
        assert stats["maintainability-change"]["systems-decreased"] == 0
        assert stats["maintainability-change"]["systems-stable"] == 2
        assert stats["maintainability-change"]["biggest-increase"] == {}
        assert stats["maintainability-change"]["biggest-decrease"] == {}

    def test_statistics_excludes_inactive_systems(self, mocker):
        """Test that inactive and development-only systems are excluded from statistics."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["active_system", "inactive_system", "dev_only_system"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            if system_name == "inactive_system":
                return {"active": False, "isDevelopmentOnly": False}
            elif system_name == "dev_only_system":
                return {"active": True, "isDevelopmentOnly": True}
            else:
                return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        def mock_start_snapshot(system_name):
            return {
                "maintainability": 3.0,
                "maintainabilityDate": "2024-02-01",
                "volumeInPersonMonths": 100,
            }

        def mock_end_snapshot(system_name):
            return {
                "maintainability": 4.0,
                "maintainabilityDate": "2024-12-31",
                "volumeInPersonMonths": 100,
            }

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Only active_system should be counted
        assert stats["maintainability"]["number-of-systems"] == 1
        assert stats["maintainability-change"]["systems-increased"] == 1

    def test_statistics_no_change_when_dates_same(self, mocker):
        """Test that systems with same start and end date count as stable (diff=0)."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        def mock_start_snapshot(system_name):
            return {
                "maintainability": 3.0,
                "maintainabilityDate": "2024-12-31",  # Same as end date
                "volumeInPersonMonths": 100,
            }

        def mock_end_snapshot(system_name):
            return {
                "maintainability": 4.0,
                "maintainabilityDate": "2024-12-31",
                "volumeInPersonMonths": 100,
            }

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # System should be counted in star statistics, and when dates are same, diff=0 counts as stable
        assert stats["maintainability"]["number-of-systems"] == 1
        assert stats["maintainability-change"]["systems-increased"] == 0
        assert stats["maintainability-change"]["systems-decreased"] == 0
        assert stats["maintainability-change"]["systems-stable"] == 1

    def test_statistics_volume_change_tracking(self, mocker):
        """Test that volume changes are tracked correctly in statistics."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        # System 1: volume increased from 100 to 150 (+50)
        # System 2: volume decreased from 200 to 180 (-20)
        # System 3: volume increased from 50 to 90 (+40)
        # Total start: 350, Total end: 420, biggest change: system1 (+50)

        def mock_start_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 200,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 50,
                },
            }
            return snapshots[system_name]

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 150,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 180,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 90,
                },
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Verify volume totals
        assert stats["volume-change"]["total-start"] == 350
        assert stats["volume-change"]["total-end"] == 420

        # Verify biggest change tracking
        assert stats["volume-change"]["biggest-change-system"] == "system1"
        assert stats["volume-change"]["biggest-change-amount"] == 50

    def test_statistics_volume_decrease(self, mocker):
        """Test that volume decreases are tracked correctly."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        # System 1: volume decreased from 100 to 80 (-20)
        # System 2: volume decreased from 200 to 50 (-150) - biggest change

        def mock_start_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 200,
                },
            }
            return snapshots[system_name]

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 80,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "volumeInPersonMonths": 50,
                },
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Verify volume totals
        assert stats["volume-change"]["total-start"] == 300
        assert stats["volume-change"]["total-end"] == 130

        # Verify biggest change tracking (should track the largest absolute change)
        assert stats["volume-change"]["biggest-change-system"] == "system2"
        assert stats["volume-change"]["biggest-change-amount"] == -150

    def test_statistics_volume_no_change(self, mocker):
        """Test volume tracking when there are no volume changes."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        def mock_start_snapshot(system_name):
            return {
                "maintainability": 3.5,
                "maintainabilityDate": "2024-02-01",
                "volumeInPersonMonths": 100,
            }

        def mock_end_snapshot(system_name):
            return {
                "maintainability": 3.5,
                "maintainabilityDate": "2024-12-31",
                "volumeInPersonMonths": 100,
            }

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Verify volume totals are equal
        assert stats["volume-change"]["total-start"] == 100
        assert stats["volume-change"]["total-end"] == 100

        # When all changes are 0, there's no "biggest" change - it remains None
        assert stats["volume-change"]["biggest-change-system"] is None
        assert stats["volume-change"]["biggest-change-amount"] == 0

    def test_statistics_with_none_ratings(self, mocker):
        """Test statistics when some systems have None ratings."""

        class TestDeltaQualityPortfolio(
            _AbstractMaintainabilityDeltaQualityPortfolioData
        ):
            def get_type(self):
                return "NEW_CODE"

        portfolio = TestDeltaQualityPortfolio()

        mock_system_names = ["system1", "system2", "system3"]
        mock_data = {
            "system1": {"filesRatingAtEnd": 4.0, "systemRatingAtEnd": 3.5},
            "system2": {
                "filesRatingAtEnd": None,  # No new code
                "systemRatingAtEnd": 3.0,
            },
            "system3": {"filesRatingAtEnd": 3.0, "systemRatingAtEnd": 3.0},
        }

        mocker.patch.object(
            type(portfolio),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )

        stats = portfolio.statistics

        # Should only count system1 and system3: (4.0 + 3.0) / 2 = 3.5
        assert stats["avg_stars"] == pytest.approx(3.5)
        assert stats["count"] == 2

        # Extremes should only be from systems with ratings
        assert stats["lowest_system"][0] == "system3"
        assert stats["lowest_system"][1] == pytest.approx(3.0)
        assert stats["highest_system"][0] == "system1"
        assert stats["highest_system"][1] == pytest.approx(4.0)

    def test_statistics_with_no_systems(self, mocker):
        """Test statistics when there are no systems."""

        class TestDeltaQualityPortfolio(
            _AbstractMaintainabilityDeltaQualityPortfolioData
        ):
            def get_type(self):
                return "NEW_CODE"

        portfolio = TestDeltaQualityPortfolio()

        mocker.patch.object(
            type(portfolio),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=[],
        )
        mocker.patch.object(
            type(portfolio), "data", new_callable=mocker.PropertyMock, return_value={}
        )

        stats = portfolio.statistics

        assert stats["avg_stars"] == 0
        assert stats["count"] == 0
        assert stats["lowest_system"] is None
        assert stats["highest_system"] is None

    def test_statistics_with_all_none_ratings(self, mocker):
        """Test statistics when all systems have None ratings."""

        class TestDeltaQualityPortfolio(
            _AbstractMaintainabilityDeltaQualityPortfolioData
        ):
            def get_type(self):
                return "NEW_CODE"

        portfolio = TestDeltaQualityPortfolio()

        mock_system_names = ["system1", "system2"]
        mock_data = {
            "system1": {"filesRatingAtEnd": None, "systemRatingAtEnd": 3.0},
            "system2": {"filesRatingAtEnd": None, "systemRatingAtEnd": 3.5},
        }

        mocker.patch.object(
            type(portfolio),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )

        stats = portfolio.statistics

        assert stats["avg_stars"] == 0
        assert stats["count"] == 0
        assert stats["lowest_system"] is None
        assert stats["highest_system"] is None

    def test_statistics_single_system(self, mocker):
        """Test statistics with a single system."""

        class TestDeltaQualityPortfolio(
            _AbstractMaintainabilityDeltaQualityPortfolioData
        ):
            def get_type(self):
                return "CHANGED_CODE"

        portfolio = TestDeltaQualityPortfolio()

        mock_system_names = ["only_system"]
        mock_data = {"only_system": {"filesRatingAtEnd": 3.7, "systemRatingAtEnd": 3.5}}

        mocker.patch.object(
            type(portfolio),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mocker.patch.object(
            type(portfolio),
            "data",
            new_callable=mocker.PropertyMock,
            return_value=mock_data,
        )

        stats = portfolio.statistics

        assert stats["avg_stars"] == pytest.approx(3.7)
        assert stats["count"] == 1
        assert stats["lowest_system"][0] == "only_system"
        assert stats["lowest_system"][1] == pytest.approx(3.7)
        assert stats["highest_system"][0] == "only_system"
        assert stats["highest_system"][1] == pytest.approx(3.7)

    def test_update_extremes(self, mocker):
        """Test the _update_extremes method updates lowest and highest correctly."""

        class TestDeltaQualityPortfolio(
            _AbstractMaintainabilityDeltaQualityPortfolioData
        ):
            def get_type(self):
                return "NEW_CODE"

        portfolio = TestDeltaQualityPortfolio()

        lowest = (None, float("inf"))
        highest = (None, float("-inf"))

        # First update
        lowest, highest = portfolio._update_extremes(3.5, "system1", lowest, highest)
        assert lowest == ("system1", 3.5)
        assert highest == ("system1", 3.5)

        # Update with higher rating
        lowest, highest = portfolio._update_extremes(4.2, "system2", lowest, highest)
        assert lowest == ("system1", 3.5)
        assert highest == ("system2", 4.2)

        # Update with lower rating
        lowest, highest = portfolio._update_extremes(2.1, "system3", lowest, highest)
        assert lowest == ("system3", 2.1)
        assert highest == ("system2", 4.2)

        # Update with middle rating (shouldn't change extremes)
        lowest, highest = portfolio._update_extremes(3.0, "system4", lowest, highest)
        assert lowest == ("system3", 2.1)
        assert highest == ("system2", 4.2)


class TestTestCodeRatioDistribution:
    """Test the test_code_ratio_distribution_percentages method."""

    def test_test_code_ratio_distribution_mixed(self, mocker):
        """Test distribution with systems in all three categories."""
        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3", "system4", "system5"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "testCodeRatio": 0.3,
                },  # low (< 50%)
                "system2": {
                    "maintainability": 3.5,
                    "testCodeRatio": 0.6,
                },  # medium (50-100%)
                "system3": {
                    "maintainability": 3.5,
                    "testCodeRatio": 1.2,
                },  # high (≥ 100%)
                "system4": {
                    "maintainability": 3.5,
                    "testCodeRatio": 0.8,
                },  # medium (50-100%)
                "system5": {
                    "maintainability": 3.5,
                    "testCodeRatio": 0.4,
                },  # low (< 50%)
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        distribution = stats_obj.test_code_ratio_distribution_percentages

        # 2 out of 5 = 40% low, 2 out of 5 = 40% medium, 1 out of 5 = 20% high
        assert distribution["low"] == 40
        assert distribution["medium"] == 40
        assert distribution["high"] == 20

    def test_test_code_ratio_distribution_all_low(self, mocker):
        """Test distribution when all systems have low test code ratio."""
        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {"maintainability": 3.5, "testCodeRatio": 0.1},
                "system2": {"maintainability": 3.5, "testCodeRatio": 0.25},
                "system3": {"maintainability": 3.5, "testCodeRatio": 0.49},
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        distribution = stats_obj.test_code_ratio_distribution_percentages

        assert distribution["low"] == 100
        assert distribution["medium"] == 0
        assert distribution["high"] == 0

    def test_test_code_ratio_distribution_with_none_values(self, mocker):
        """Test distribution when some systems have None test code ratio."""
        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3", "system4"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {"maintainability": 3.5, "testCodeRatio": 0.3},  # low
                "system2": {
                    "maintainability": 3.5,
                    "testCodeRatio": None,
                },  # should be excluded
                "system3": {"maintainability": 3.5, "testCodeRatio": 1.0},  # high
                "system4": {"maintainability": 3.5},  # missing key, should be excluded
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        distribution = stats_obj.test_code_ratio_distribution_percentages

        # Only 2 systems counted: 1 low, 1 high = 50% each
        assert distribution["low"] == 50
        assert distribution["medium"] == 0
        assert distribution["high"] == 50

    def test_test_code_ratio_distribution_excludes_inactive_systems(self, mocker):
        """Test that inactive and development-only systems are excluded."""
        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["active_system", "inactive_system", "dev_only_system"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            if system_name == "inactive_system":
                return {"active": False, "isDevelopmentOnly": False}
            elif system_name == "dev_only_system":
                return {"active": True, "isDevelopmentOnly": True}
            else:
                return {"active": True, "isDevelopmentOnly": False}

        def mock_end_snapshot(system_name):
            return {"maintainability": 3.5, "testCodeRatio": 0.3}  # all low

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        distribution = stats_obj.test_code_ratio_distribution_percentages

        # Only active_system should be counted
        assert distribution["low"] == 100
        assert distribution["medium"] == 0
        assert distribution["high"] == 0

    def test_test_code_ratio_distribution_no_systems(self, mocker):
        """Test distribution with no systems."""
        stats_obj = MaintainabilityPortfolioStats()

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=[],
        )

        distribution = stats_obj.test_code_ratio_distribution_percentages

        assert distribution["low"] == 0
        assert distribution["medium"] == 0
        assert distribution["high"] == 0

    def test_test_code_ratio_distribution_boundary_values(self, mocker):
        """Test distribution with values exactly at boundaries."""
        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3", "system4"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "testCodeRatio": 0.49,
                },  # low (< 0.5)
                "system2": {
                    "maintainability": 3.5,
                    "testCodeRatio": 0.5,
                },  # medium (>= 0.5, < 1.0)
                "system3": {
                    "maintainability": 3.5,
                    "testCodeRatio": 0.99,
                },  # medium (>= 0.5, < 1.0)
                "system4": {
                    "maintainability": 3.5,
                    "testCodeRatio": 1.0,
                },  # high (>= 1.0)
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        distribution = stats_obj.test_code_ratio_distribution_percentages

        # 1 low, 2 medium, 1 high
        assert distribution["low"] == 25
        assert distribution["medium"] == 50
        assert distribution["high"] == 25


class TestTestCodeRatioChange:
    """Test the test code ratio change tracking in statistics."""

    def test_test_code_ratio_change_tracking(self, mocker):
        """Test that test code ratio changes are tracked correctly in statistics."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3", "system4"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        # System 1: ratio increased from 0.5 to 0.7 (+0.2)
        # System 2: ratio decreased from 0.8 to 0.6 (-0.2)
        # System 3: ratio increased from 0.6 to 0.9 (+0.3) - biggest increase
        # System 4: ratio stable from 0.4 to 0.41 (+0.01, within threshold)

        def mock_start_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "testCodeRatio": 0.5,
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "testCodeRatio": 0.8,
                    "volumeInPersonMonths": 100,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "testCodeRatio": 0.6,
                    "volumeInPersonMonths": 100,
                },
                "system4": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "testCodeRatio": 0.4,
                    "volumeInPersonMonths": 100,
                },
            }
            return snapshots[system_name]

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "testCodeRatio": 0.7,
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "testCodeRatio": 0.6,
                    "volumeInPersonMonths": 100,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "testCodeRatio": 0.9,
                    "volumeInPersonMonths": 100,
                },
                "system4": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "testCodeRatio": 0.41,
                    "volumeInPersonMonths": 100,
                },
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Verify totals
        assert stats["test-code-ratio-change"]["total-start"] == pytest.approx(
            2.3
        )  # 0.5 + 0.8 + 0.6 + 0.4
        assert stats["test-code-ratio-change"]["total-end"] == pytest.approx(
            2.61
        )  # 0.7 + 0.6 + 0.9 + 0.41

        # Verify change counts
        assert (
            stats["test-code-ratio-change"]["systems-increased"] == 2
        )  # system1, system3
        assert stats["test-code-ratio-change"]["systems-decreased"] == 1  # system2
        assert stats["test-code-ratio-change"]["systems-stable"] == 1  # system4

        # Verify biggest changes
        assert "system3" in stats["test-code-ratio-change"]["biggest-increase"]
        assert (
            abs(stats["test-code-ratio-change"]["biggest-increase"]["system3"] - 0.3)
            < 0.001
        )

        assert "system2" in stats["test-code-ratio-change"]["biggest-decrease"]
        assert (
            abs(stats["test-code-ratio-change"]["biggest-decrease"]["system2"] - (-0.2))
            < 0.001
        )

    def test_test_code_ratio_change_with_none_values(self, mocker):
        """Test that systems with None test code ratios are excluded from change tracking."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2", "system3"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        def mock_start_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "testCodeRatio": 0.5,
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "testCodeRatio": None,
                    "volumeInPersonMonths": 100,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-02-01",
                    "volumeInPersonMonths": 100,
                },
                # missing testCodeRatio
            }
            return snapshots[system_name]

        def mock_end_snapshot(system_name):
            snapshots = {
                "system1": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "testCodeRatio": 0.7,
                    "volumeInPersonMonths": 100,
                },
                "system2": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "testCodeRatio": 0.6,
                    "volumeInPersonMonths": 100,
                },
                "system3": {
                    "maintainability": 3.5,
                    "maintainabilityDate": "2024-12-31",
                    "testCodeRatio": None,
                    "volumeInPersonMonths": 100,
                },
            }
            return snapshots[system_name]

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Only system1 should be counted (has both start and end ratios)
        assert stats["test-code-ratio-change"]["total-start"] == pytest.approx(0.5)
        assert stats["test-code-ratio-change"]["total-end"] == pytest.approx(0.7)
        assert stats["test-code-ratio-change"]["systems-increased"] == 1
        assert stats["test-code-ratio-change"]["systems-decreased"] == 0
        assert stats["test-code-ratio-change"]["systems-stable"] == 0

    def test_test_code_ratio_change_no_changes(self, mocker):
        """Test change tracking when there are no changes."""

        stats_obj = MaintainabilityPortfolioStats()

        mock_system_names = ["system1", "system2"]

        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {"active": True, "isDevelopmentOnly": False}

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "period",
            new_callable=mocker.PropertyMock,
            return_value=["2024-01-01", "2024-12-31"],
        )

        def mock_start_snapshot(system_name):
            return {
                "maintainability": 3.5,
                "maintainabilityDate": "2024-02-01",
                "testCodeRatio": 0.5,
                "volumeInPersonMonths": 100,
            }

        def mock_end_snapshot(system_name):
            return {
                "maintainability": 3.5,
                "maintainabilityDate": "2024-12-31",
                "testCodeRatio": 0.5,
                "volumeInPersonMonths": 100,
            }

        mocker.patch.object(
            type(maintainability_portfolio_data),
            "system_names",
            new_callable=mocker.PropertyMock,
            return_value=mock_system_names,
        )
        mock_metadata = [
            {"systemName": system_name, "active": True, "isDevelopmentOnly": False}
            for system_name in mock_system_names
        ]
        mocker.patch.object(
            type(maintainability_portfolio_data),
            "metadata",
            new_callable=mocker.PropertyMock,
            return_value=mock_metadata,
        )
        mocker.patch(
            "report_generator.generator.domain.portfolio.shared.utils.get_system_metadata",
            side_effect=mock_get_system_metadata,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "start_snapshot",
            side_effect=mock_start_snapshot,
        )
        mocker.patch.object(
            maintainability_portfolio_data,
            "end_snapshot",
            side_effect=mock_end_snapshot,
        )

        stats = stats_obj.statistics

        # Both systems stable
        assert stats["test-code-ratio-change"]["total-start"] == pytest.approx(1.0)
        assert stats["test-code-ratio-change"]["total-end"] == pytest.approx(1.0)
        assert stats["test-code-ratio-change"]["systems-increased"] == 0
        assert stats["test-code-ratio-change"]["systems-decreased"] == 0
        assert stats["test-code-ratio-change"]["systems-stable"] == 2
        assert stats["test-code-ratio-change"]["biggest-increase"] == {}


class TestMaintainabilityPortfolioData:
    """Test cases for MaintainabilityPortfolioData model."""

    def setup_method(self):
        """Clean up portfolio context before each test."""
        portfolio_filters._team = None
        portfolio_filters._division = None

        # Clear all cached properties
        cache_attrs = ["data", "metadata", "_statistics", "period", "system_names"]
        for attr in cache_attrs:
            maintainability_portfolio_data.__dict__.pop(attr, None)

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        portfolio_filters._team = None
        portfolio_filters._division = None

        # Clear all cached properties
        cache_attrs = ["data", "metadata", "_statistics", "period", "system_names"]
        for attr in cache_attrs:
            maintainability_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.maintainability_portfolio.data.sigrid_api"
    )
    def test_data_filters_systems_without_maintainability(self, mock_sigrid_api):
        """Test that systems without maintainability data are filtered out."""
        mock_api_response = {
            "systems": [
                {"system": "system1", "maintainability": 4.0},
                {"system": "system2"},  # No maintainability
                {"system": "system3", "maintainability": 3.5},
            ]
        }
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache and get fresh data
        if hasattr(maintainability_portfolio_data, "data"):
            del maintainability_portfolio_data.__dict__["data"]

        data = maintainability_portfolio_data.data

        assert len(data["systems"]) == 2
        assert data["systems"][0]["system"] == "system1"
        assert data["systems"][1]["system"] == "system3"

    @patch(
        "report_generator.generator.domain.portfolio.maintainability_portfolio.data.sigrid_api"
    )
    def test_system_names_returns_filtered_system_list(self, mock_sigrid_api):
        """Test that system_names property returns list of system names."""
        mock_api_response = {
            "systems": [
                {"system": "system1", "maintainability": 4.0},
                {"system": "system2", "maintainability": 3.5},
            ]
        }
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache
        for attr in ["data", "system_names"]:
            if hasattr(maintainability_portfolio_data, attr):
                del maintainability_portfolio_data.__dict__[attr]

        names = maintainability_portfolio_data.system_names

        assert len(names) == 2
        assert "system1" in names
        assert "system2" in names

    @patch(
        "report_generator.generator.domain.portfolio.maintainability_portfolio.data.sigrid_api"
    )
    def test_get_system_returns_correct_system_data(self, mock_sigrid_api):
        """Test that get_system returns data for specific system."""
        mock_api_response = {
            "systems": [
                {"system": "system1", "maintainability": 4.0, "stars": 4},
                {"system": "system2", "maintainability": 3.5, "stars": 3},
            ]
        }
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache
        if hasattr(maintainability_portfolio_data, "data"):
            del maintainability_portfolio_data.__dict__["data"]

        system = maintainability_portfolio_data.get_system("system1")

        assert system is not None
        assert system["system"] == "system1"
        assert abs(system["maintainability"] - 4.0) < 0.01

    @patch(
        "report_generator.generator.domain.portfolio.maintainability_portfolio.data.sigrid_api"
    )
    def test_get_system_returns_none_for_unknown_system(self, mock_sigrid_api):
        """Test that get_system returns None for non-existent system."""
        mock_api_response = {"systems": [{"system": "system1", "maintainability": 4.0}]}
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache
        if hasattr(maintainability_portfolio_data, "data"):
            del maintainability_portfolio_data.__dict__["data"]

        system = maintainability_portfolio_data.get_system("unknown")

        assert system is None

    # Note: get_statistics() tests are complex integration tests requiring extensive mocking
    # of period, snapshots, and metadata. They are covered by integration tests elsewhere.


class TestMaintainabilityPortfolioHelpers:
    """Test cases for helper functions in maintainability_portfolio module."""

    def test_initialize_statistics(self):
        """Test that _initialize_statistics returns correct structure."""
        stats = _initialize_statistics()

        assert "maintainability" in stats
        assert "maintainability-change" in stats
        assert stats["maintainability"]["1-star"] == 0
        assert stats["maintainability"]["5-star"] == 0
        assert stats["maintainability"]["number-of-systems"] == 0

    def test_is_system_active_returns_true_for_active(self):
        """Test that is_system_active returns True for active non-dev systems."""
        metadata = {"active": True, "isDevelopmentOnly": False}

        assert is_system_active(metadata) is True

    def test_is_system_active_returns_false_for_inactive(self):
        """Test that is_system_active returns False for inactive systems."""
        metadata = {"active": False, "isDevelopmentOnly": False}

        assert is_system_active(metadata) is False

    def test_is_system_active_returns_false_for_dev_only(self):
        """Test that is_system_active returns False for dev-only systems."""
        metadata = {"active": True, "isDevelopmentOnly": True}

        assert is_system_active(metadata) is False

    def test_weighted_avg_calculates_correctly(self):
        """Test that _weighted_avg calculates weighted average correctly."""
        values = [4.0, 3.0, 5.0]
        weights = [10, 5, 15]

        # (4.0*10 + 3.0*5 + 5.0*15) / (10+5+15) = (40+15+75) / 30 = 130/30 = 4.333...
        result = _weighted_avg(values, weights)

        assert abs(result - 4.333333) < 0.01

    def test_weighted_avg_handles_zero_weights(self):
        """Test that _weighted_avg handles zero total weight gracefully."""
        values = [4.0, 3.0]
        weights = [0, 0]

        result = _weighted_avg(values, weights)

        # Should return a very small number instead of crashing
        assert abs(result - 0.000001) < 0.00001

    def test_parse_date_converts_string_to_datetime(self):
        """Test that parse_date correctly parses date strings."""
        from datetime import datetime

        result = parse_date("2024-01-15")

        assert result == datetime(2024, 1, 15)

    def test_update_star_statistics_increments_correctly(self):
        """Test that _update_star_statistics updates statistics correctly."""
        stats = _initialize_statistics()
        end_snapshot = {"maintainability": 4.5}

        _update_star_statistics(stats, end_snapshot)

        assert stats["maintainability"]["5-star"] == 1
        assert stats["maintainability"]["number-of-systems"] == 1

    def test_finalize_change_statistics_with_increase(self):
        """Test that _finalize_change_statistics records increases."""
        stats = _initialize_statistics()
        best_inc = ("system1", 0.5)
        best_dec = (None, float("inf"))

        _finalize_change_statistics(stats, best_inc, best_dec)

        assert "system1" in stats["maintainability-change"]["biggest-increase"]
        assert (
            abs(stats["maintainability-change"]["biggest-increase"]["system1"] - 0.5)
            < 0.01
        )

    def test_finalize_change_statistics_with_decrease(self):
        """Test that _finalize_change_statistics records decreases."""
        stats = _initialize_statistics()
        best_inc = (None, float("-inf"))
        best_dec = ("system2", -0.3)

        _finalize_change_statistics(stats, best_inc, best_dec)

        assert "system2" in stats["maintainability-change"]["biggest-decrease"]
        assert (
            abs(stats["maintainability-change"]["biggest-decrease"]["system2"] - (-0.3))
            < 0.01
        )

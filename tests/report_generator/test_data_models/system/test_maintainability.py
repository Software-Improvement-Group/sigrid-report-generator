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


# noinspection PyProtectedMember
from report_generator.generator.domain.system.maintainability import _sort_and_aggregate_technology_data


class TestDataModels:
    def test_sorting_technologies_on_volume_in_pm(self):
        sorted_tech_data = _sort_and_aggregate_technology_data(TestDataModels._mock_tech_data(3))

        assert len(sorted_tech_data) == 3
        assert sorted_tech_data[0]["name"] == "noot"
        assert sorted_tech_data[1]["name"] == "mies"
        assert sorted_tech_data[2]["name"] == "aap"

    def test_aggregate_small_technologies_if_more_than_5(self):
        sorted_tech_data = _sort_and_aggregate_technology_data(TestDataModels._mock_tech_data(7))

        assert len(sorted_tech_data) == 5
        assert sorted_tech_data[0]["name"] == "teun"
        assert sorted_tech_data[1]["name"] == "wim"
        assert sorted_tech_data[2]["name"] == "zus"
        assert sorted_tech_data[3]["name"] == "noot"
        assert sorted_tech_data[4]["name"] == "others"
        assert sorted_tech_data[4]["volumeInPersonMonths"] == 4
        assert abs(sorted_tech_data[4]["maintainability"] - 3.5) < 0.01
        assert abs(sorted_tech_data[4]["testCodeRatio"] - 26.25) < 0.01
        assert sorted_tech_data[4]["technologyRisk"] == "TOLERATE"

    def test_aggregate_removes_technologies_with_zero_loc(self):
        mock_data = TestDataModels._mock_tech_data(3)
        mock_data.append(TestDataModels._mock_technology("zeroLoc", 0, 0, 3.0, 0.13, "TARGET"))

        sorted_tech_data = _sort_and_aggregate_technology_data(mock_data)

        assert len(sorted_tech_data) == 3

    @staticmethod
    def _mock_tech_data(size):
        mock_data = [TestDataModels._mock_technology("aap", 1, 15, 3.0, 45.0, "TARGET"),
                     TestDataModels._mock_technology("noot", 3, 2, 3.0, 15.0, "TARGET"),
                     TestDataModels._mock_technology("mies", 2, 87, 4.0, 15.0, "TARGET"),
                     TestDataModels._mock_technology("wim", 15, 87, 3.0, 15.0, "TARGET"),
                     TestDataModels._mock_technology("zus", 7, 87, 3.0, 15.0, "TARGET"),
                     TestDataModels._mock_technology("jet", 1, 87, 3.0, 30.0, "TOLERATE"),
                     TestDataModels._mock_technology("teun", 18, 87, 3.0, 15.0, "TARGET"), ]

        return mock_data[0:size]

    @staticmethod
    def _mock_technology(name, pm, loc, maint, test_ratio, tech_risk):
        return {
            "name"                : name,
            "displayName"         : name,
            "volumeInPersonMonths": pm,
            "volumeInLoc"         : loc,
            "maintainability"     : maint,
            "testCodeRatio"       : test_ratio,
            "technologyRisk"      : tech_risk
        }


class TestSystemMaintainabilityHelpers:
    """Additional tests for system maintainability helper functions."""

    def test_empty_technology_list(self):
        """Test that empty technology list returns empty result."""
        result = _sort_and_aggregate_technology_data([])
        assert result == []

    def test_single_technology(self):
        """Test handling of single technology."""
        tech = TestDataModels._mock_technology("python", 10, 1000, 4.0, 50.0, "TARGET")
        result = _sort_and_aggregate_technology_data([tech])

        assert len(result) == 1
        assert result[0]["name"] == "python"

    def test_aggregation_calculates_weighted_average_maintainability(self):
        """Test that aggregated 'others' uses weighted average for maintainability."""
        # Need 6 technologies to trigger aggregation (keeps top 4, aggregates rest)
        mock_data = [
            TestDataModels._mock_technology("big1", 10, 1000, 4.0, 20.0, "TARGET"),
            TestDataModels._mock_technology("big2", 8, 800, 3.5, 25.0, "TARGET"),
            TestDataModels._mock_technology("big3", 6, 600, 3.0, 22.0, "TARGET"),
            TestDataModels._mock_technology("big4", 5, 500, 4.2, 18.0, "TARGET"),
            TestDataModels._mock_technology("small1", 2, 200, 5.0, 30.0, "TARGET"),
            TestDataModels._mock_technology("small2", 1, 100, 4.5, 35.0, "TOLERATE"),
        ]

        result = _sort_and_aggregate_technology_data(mock_data)

        # Should have top 4 + others (aggregates last 2)
        assert len(result) == 5
        assert result[4]["name"] == "others"
        # Verify weighted average: (2*5.0 + 1*4.5) / 3 = 4.833...
        assert abs(result[4]["maintainability"] - 4.833333) < 0.01

    def test_risk_aggregation_selects_highest_risk(self):
        """Test that aggregated 'others' selects the highest risk level."""
        # Need 6 technologies to trigger aggregation
        mock_data = [
            TestDataModels._mock_technology("big1", 10, 1000, 4.0, 20.0, "TARGET"),
            TestDataModels._mock_technology("big2", 8, 800, 4.0, 20.0, "TARGET"),
            TestDataModels._mock_technology("big3", 6, 600, 4.0, 20.0, "TARGET"),
            TestDataModels._mock_technology("big4", 5, 500, 4.0, 20.0, "TARGET"),
            TestDataModels._mock_technology("small1", 2, 200, 4.0, 20.0, "TOLERATE"),
            TestDataModels._mock_technology("small2", 1, 100, 4.0, 20.0, "PHASEOUT"),
        ]

        result = _sort_and_aggregate_technology_data(mock_data)

        assert len(result) == 5
        assert result[4]["name"] == "others"
        assert result[4]["technologyRisk"] == "PHASEOUT"  # Worst risk wins

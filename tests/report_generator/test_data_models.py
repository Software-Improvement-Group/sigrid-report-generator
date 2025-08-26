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
from report_generator.generator.data_models.maintainability import _sort_and_aggregate_technology_data


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
        assert sorted_tech_data[4]["maintainability"] == 3.5
        assert sorted_tech_data[4]["testCodeRatio"] == 26.25
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

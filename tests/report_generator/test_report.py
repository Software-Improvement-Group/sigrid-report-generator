import pytest
from src.report_generator.report import Report

class TestReport():

    def test_calc_stars_works(self):
        assert Report.calculate_stars(1.5) == "★★☆☆☆"
        assert Report.calculate_stars(1.499999) == "★☆☆☆☆"
        assert Report.calculate_stars(4.5) == "★★★★★"

        assert Report.calculate_stars(7.5) == "★★★★★"

        assert Report.calculate_stars(-3) == ""

    def test_calculate_volume_indicator(self):

        assert Report.calculate_volume_indicator(0.5) == "very large"
        assert Report.calculate_volume_indicator(4.6) == "very small"
        assert Report.calculate_volume_indicator(4.499999) == "small"

    def test_maintainability_round(self):
        assert Report.maintainability_round(1.50000) == 1.5

        assert Report.maintainability_round(1.499999) == 1.4
        assert Report.maintainability_round(5.4) == 5.4

        assert Report.maintainability_round(3.284) == 3.2

    def test_short_sigrid_token_is_invalid(self):
        with pytest.raises(Exception) as excinfo:  
            Report.test_sigrid_token("eyo")
        assert str(excinfo.value).startswith("Invalid Sigrid token")

    def test_random_string_is_invalid_sigrid_token(self):
        with pytest.raises(Exception) as excinfo:  
            Report.test_sigrid_token("sfkskfiurkfshiuwhfibvcgi43hf2o3h893hg34")
        assert str(excinfo.value).startswith("Invalid Sigrid token")

    def test_valid_sigrid_token_is_valid(self):
        try:
            Report.test_sigrid_token("eyKskfiurkfshiuwhfibvcgi43hf2o3h893hg34")
        except Exception as ex:
            pytest.fail(f"This token was expected to be valid")
            
    def test_sorting_technologies_on_volume_in_pm(self):
        sorted_tech_data = Report.sort_and_aggregate_technology_data(TestReport._mock_tech_data(3))

        assert len(sorted_tech_data) == 3
        assert sorted_tech_data[0]["name"] == "noot"
        assert sorted_tech_data[1]["name"] == "mies"
        assert sorted_tech_data[2]["name"] == "aap"

    def test_aggregate_small_technologies_if_more_than_5(self):
        sorted_tech_data = Report.sort_and_aggregate_technology_data(TestReport._mock_tech_data(7))

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
        mock_data = TestReport._mock_tech_data(3)
        mock_data.append(TestReport._mock_technology("zeroLoc", 0, 0, 3.0, 0.13, "TARGET"))

        sorted_tech_data = Report.sort_and_aggregate_technology_data(mock_data)

        assert len(sorted_tech_data) == 3

    def _mock_tech_data(size):
        mock_data = [TestReport._mock_technology("aap", 1, 15, 3.0, 45.0, "TARGET"),
                TestReport._mock_technology("noot", 3, 2, 3.0, 15.0, "TARGET"),
                TestReport._mock_technology("mies", 2, 87, 4.0, 15.0, "TARGET"),
                TestReport._mock_technology("wim", 15, 87, 3.0, 15.0, "TARGET"),
                TestReport._mock_technology("zus", 7, 87, 3.0, 15.0, "TARGET"),
                TestReport._mock_technology("jet", 1, 87, 3.0, 30.0, "TOLERATE"),
                TestReport._mock_technology("teun", 18, 87, 3.0, 15.0, "TARGET"),]
        
        return mock_data[0:size]

    def _mock_technology(name, pm, loc, maint, testRatio, techRisk):
        return {
            "name": name,
            "displayName": name,
            "volumeInPersonMonths": pm,
            "volumeInLoc": loc,
            "maintainability": maint,
            "testCodeRatio": testRatio,
            "technologyRisk": techRisk
        }

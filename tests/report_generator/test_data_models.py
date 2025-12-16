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

from unittest.mock import patch, MagicMock

# noinspection PyProtectedMember
from report_generator.generator.data_models.system.maintainability import _sort_and_aggregate_technology_data
from report_generator.generator.data_models.portfolio.maintainability_portfolio import maintainability_portfolio_data
from report_generator.generator.data_models.portfolio.base import AbstractPortfolioModel


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


class TestMaintainabilityPortfolioData:
    """Test cases for MaintainabilityPortfolioData model."""

    def setup_method(self):
        """Clean up portfolio context before each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        # Clear all cached properties
        cache_attrs = ['data', 'metadata', '_statistics', 'period', 'system_names']
        for attr in cache_attrs:
            maintainability_portfolio_data.__dict__.pop(attr, None)

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        # Clear all cached properties
        cache_attrs = ['data', 'metadata', '_statistics', 'period', 'system_names']
        for attr in cache_attrs:
            maintainability_portfolio_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.maintainability_portfolio.sigrid_api')
    def test_data_filters_systems_without_maintainability(self, mock_sigrid_api):
        """Test that systems without maintainability data are filtered out."""
        mock_api_response = {
            'systems': [
                {'system': 'system1', 'maintainability': 4.0},
                {'system': 'system2'},  # No maintainability
                {'system': 'system3', 'maintainability': 3.5}
            ]
        }
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache and get fresh data
        if hasattr(maintainability_portfolio_data, 'data'):
            del maintainability_portfolio_data.__dict__['data']
        
        data = maintainability_portfolio_data.data

        assert len(data['systems']) == 2
        assert data['systems'][0]['system'] == 'system1'
        assert data['systems'][1]['system'] == 'system3'

    @patch('report_generator.generator.data_models.portfolio.maintainability_portfolio.sigrid_api')
    def test_system_names_returns_filtered_system_list(self, mock_sigrid_api):
        """Test that system_names property returns list of system names."""
        mock_api_response = {
            'systems': [
                {'system': 'system1', 'maintainability': 4.0},
                {'system': 'system2', 'maintainability': 3.5}
            ]
        }
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache
        for attr in ['data', 'system_names']:
            if hasattr(maintainability_portfolio_data, attr):
                del maintainability_portfolio_data.__dict__[attr]
        
        names = maintainability_portfolio_data.system_names

        assert len(names) == 2
        assert 'system1' in names
        assert 'system2' in names

    @patch('report_generator.generator.data_models.portfolio.maintainability_portfolio.sigrid_api')
    def test_get_system_returns_correct_system_data(self, mock_sigrid_api):
        """Test that get_system returns data for specific system."""
        mock_api_response = {
            'systems': [
                {'system': 'system1', 'maintainability': 4.0, 'stars': 4},
                {'system': 'system2', 'maintainability': 3.5, 'stars': 3}
            ]
        }
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache
        if hasattr(maintainability_portfolio_data, 'data'):
            del maintainability_portfolio_data.__dict__['data']
        
        system = maintainability_portfolio_data.get_system('system1')

        assert system is not None
        assert system['system'] == 'system1'
        assert system['maintainability'] == 4.0

    @patch('report_generator.generator.data_models.portfolio.maintainability_portfolio.sigrid_api')
    def test_get_system_returns_none_for_unknown_system(self, mock_sigrid_api):
        """Test that get_system returns None for non-existent system."""
        mock_api_response = {
            'systems': [
                {'system': 'system1', 'maintainability': 4.0}
            ]
        }
        mock_sigrid_api.get_portfolio_maintainability.return_value = mock_api_response

        # Clear cache
        if hasattr(maintainability_portfolio_data, 'data'):
            del maintainability_portfolio_data.__dict__['data']
        
        system = maintainability_portfolio_data.get_system('unknown')

        assert system is None

    # Note: get_statistics() tests are complex integration tests requiring extensive mocking
    # of period, snapshots, and metadata. They are covered by integration tests elsewhere.


class TestAbstractPortfolioModel:
    """Test cases for AbstractPortfolioModel base class."""

    def test_system_names_helper_extracts_names(self):
        """Test _system_names_helper extracts system names from data."""
        data = [
            {'systemName': 'system1', 'value': 100},
            {'systemName': 'system2', 'value': 200},
            {'systemName': 'system3', 'value': 150}
        ]

        names = AbstractPortfolioModel._system_names_helper(data, 'systemName')

        assert len(names) == 3
        assert names == ['system1', 'system2', 'system3']

    def test_get_system_helper_finds_correct_system(self):
        """Test _get_system_helper finds the correct system."""
        data = [
            {'system': 'sys1', 'maintainability': 4.0},
            {'system': 'sys2', 'maintainability': 3.5},
            {'system': 'sys3', 'maintainability': 4.2}
        ]

        result = AbstractPortfolioModel._get_system_helper('sys2', data, 'system')

        assert result is not None
        assert result['system'] == 'sys2'
        assert result['maintainability'] == 3.5

    def test_get_system_helper_returns_none_for_missing(self):
        """Test _get_system_helper returns None for non-existent system."""
        data = [
            {'system': 'sys1', 'maintainability': 4.0}
        ]

        result = AbstractPortfolioModel._get_system_helper('unknown', data, 'system')

        assert result is None


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


class TestObjectivesData:
    """Test cases for ObjectivesData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        from report_generator.generator.data_models.portfolio.objectives import objectives_data
        cache_attrs = ['periods', 'comparison_period', 'objectives_evaluation_trend', 
                      'objectives_evaluation_status', 'teams']
        for attr in cache_attrs:
            objectives_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_determine_system_status_met(self, mock_sigrid_api):
        """Test that determine_system_status returns MET when target is met."""
        from report_generator.generator.data_models.portfolio.objectives import ObjectivesData, ObjectiveStatus
        
        objective = {
            "targetMetAtEnd": "MET",
            "delta": "SIMILAR"
        }
        
        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.MET

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_determine_system_status_improved(self, mock_sigrid_api):
        """Test that determine_system_status returns IMPROVED when improving."""
        from report_generator.generator.data_models.portfolio.objectives import ObjectivesData, ObjectiveStatus
        
        objective = {
            "targetMetAtEnd": "NOT_MET",
            "delta": "IMPROVING"
        }
        
        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.IMPROVED

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_determine_system_status_worsened(self, mock_sigrid_api):
        """Test that determine_system_status returns WORSENED when deteriorating."""
        from report_generator.generator.data_models.portfolio.objectives import ObjectivesData, ObjectiveStatus
        
        objective = {
            "targetMetAtEnd": "NOT_MET",
            "delta": "DETERIORATING"
        }
        
        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.WORSENED

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_determine_system_status_unchanged(self, mock_sigrid_api):
        """Test that determine_system_status returns UNCHANGED when similar."""
        from report_generator.generator.data_models.portfolio.objectives import ObjectivesData, ObjectiveStatus
        
        objective = {
            "targetMetAtEnd": "NOT_MET",
            "delta": "SIMILAR"
        }
        
        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.UNCHANGED

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_determine_system_status_unknown(self, mock_sigrid_api):
        """Test that determine_system_status returns UNKNOWN for unknown states."""
        from report_generator.generator.data_models.portfolio.objectives import ObjectivesData, ObjectiveStatus
        
        objective = {
            "targetMetAtEnd": "UNKNOWN",
            "delta": "SIMILAR"
        }
        
        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.UNKNOWN

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_filter_system_evaluations(self, mock_sigrid_api):
        """Test that filter_system_evaluations filters systems correctly."""
        from report_generator.generator.data_models.portfolio.objectives import ObjectivesData
        
        evaluation = [
            {"systemName": "system1", "objectives": []},
            {"systemName": "system2", "objectives": []},
            {"systemName": "system3", "objectives": []}
        ]
        
        filtered = ObjectivesData.filter_system_evaluations(evaluation, ["system1", "system3"])
        
        assert len(filtered) == 2
        assert filtered[0]["systemName"] == "system1"
        assert filtered[1]["systemName"] == "system3"

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_get_portfolio_percentage_with_no_objectives(self, mock_sigrid_api):
        """Test that get_portfolio_percentage returns 0 when no objectives exist."""
        from report_generator.generator.data_models.portfolio.objectives import objectives_data, ObjectiveStatus
        
        evaluations = [{"systemName": "system1", "objectives": []}]
        
        percentage = objectives_data.get_portfolio_percentage(evaluations, None, ObjectiveStatus.MET)
        
        assert percentage == 0

    @patch('report_generator.generator.data_models.portfolio.objectives.sigrid_api')
    def test_get_portfolio_percentage_calculates_correctly(self, mock_sigrid_api):
        """Test that get_portfolio_percentage calculates percentage correctly."""
        from report_generator.generator.data_models.portfolio.objectives import objectives_data, ObjectiveStatus
        
        evaluations = [
            {
                "systemName": "system1",
                "objectives": [
                    {"feature": "MAINTAINABILITY", "targetMetAtEnd": "MET", "delta": "SIMILAR"},
                    {"feature": "SECURITY", "targetMetAtEnd": "NOT_MET", "delta": "IMPROVING"},
                    {"feature": "ARCHITECTURE_QUALITY", "targetMetAtEnd": "NOT_MET", "delta": "DETERIORATING"}
                ]
            }
        ]
        
        # 1 out of 3 is MET = 33.33%
        met_percentage = objectives_data.get_portfolio_percentage(evaluations, None, ObjectiveStatus.MET)
        assert abs(met_percentage - 33.333333) < 0.01
        
        # 1 out of 3 is IMPROVED = 33.33%
        improved_percentage = objectives_data.get_portfolio_percentage(evaluations, None, ObjectiveStatus.IMPROVED)
        assert abs(improved_percentage - 33.333333) < 0.01


class TestSecurityPortfolioData:
    """Test cases for SecurityRatingsPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        from report_generator.generator.data_models.portfolio.security_portfolio import security_ratings_portfolio_data
        cache_attrs = ['data', 'metadata', 'period', 'system_names']
        for attr in cache_attrs:
            security_ratings_portfolio_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.security_portfolio.sigrid_api')
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        from report_generator.generator.data_models.portfolio.security_portfolio import security_ratings_portfolio_data
        
        mock_data = [
            {'systemName': 'system1', 'securityRating': 4.5},
            {'systemName': 'system2', 'securityRating': 3.8}
        ]
        mock_sigrid_api.get_portfolio_security_ratings.return_value = mock_data
        
        security_ratings_portfolio_data.__dict__.pop('data', None)
        
        system = security_ratings_portfolio_data.get_system('system1')
        
        assert system is not None
        assert system['systemName'] == 'system1'
        assert system['securityRating'] == 4.5

    @patch('report_generator.generator.data_models.portfolio.security_portfolio.sigrid_api')
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        from report_generator.generator.data_models.portfolio.security_portfolio import security_ratings_portfolio_data
        
        mock_data = [
            {'systemName': 'system1', 'securityRating': 4.5},
            {'systemName': 'system2', 'securityRating': 3.8},
            {'systemName': 'system3', 'securityRating': 4.2}
        ]
        mock_sigrid_api.get_portfolio_security_ratings.return_value = mock_data
        
        for attr in ['data', 'system_names']:
            security_ratings_portfolio_data.__dict__.pop(attr, None)
        
        names = security_ratings_portfolio_data.system_names
        
        assert len(names) == 3
        assert 'system1' in names
        assert 'system2' in names
        assert 'system3' in names


class TestSecurityDashboardFindingsPortfolioData:
    """Test cases for SecurityDashboardFindingsPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        from report_generator.generator.data_models.portfolio.security_dashboard_findings_portfolio import security_dashboard_findings_portfolio_data
        cache_attrs = ['data', 'metadata', 'system_names']
        for attr in cache_attrs:
            security_dashboard_findings_portfolio_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.security_dashboard_findings_portfolio.sigrid_api')
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        from report_generator.generator.data_models.portfolio.security_dashboard_findings_portfolio import security_dashboard_findings_portfolio_data
        
        mock_data = {
            'systems': [
                {'system': 'system1', 'findings': [{'severity': 'HIGH'}]},
                {'system': 'system2', 'findings': [{'severity': 'LOW'}]}
            ]
        }
        mock_sigrid_api.get_portfolio_security_dashboard_findings.return_value = mock_data
        
        security_dashboard_findings_portfolio_data.__dict__.pop('data', None)
        
        system = security_dashboard_findings_portfolio_data.get_system('system1')
        
        assert system is not None
        assert system['system'] == 'system1'
        assert len(system['findings']) == 1

    @patch('report_generator.generator.data_models.portfolio.security_dashboard_findings_portfolio.sigrid_api')
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        from report_generator.generator.data_models.portfolio.security_dashboard_findings_portfolio import security_dashboard_findings_portfolio_data
        
        mock_data = {
            'systems': [
                {'system': 'system1', 'findings': []},
                {'system': 'system2', 'findings': []},
                {'system': 'system3', 'findings': []}
            ]
        }
        mock_sigrid_api.get_portfolio_security_dashboard_findings.return_value = mock_data
        
        for attr in ['data', 'system_names']:
            security_dashboard_findings_portfolio_data.__dict__.pop(attr, None)
        
        names = security_dashboard_findings_portfolio_data.system_names
        
        assert len(names) == 3
        assert 'system1' in names
        assert 'system2' in names
        assert 'system3' in names


class TestSecurityDashboardResolutionTimesPortfolioData:
    """Test cases for SecurityDashboardResolutionTimesPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        from report_generator.generator.data_models.portfolio.security_dashboard_resolution_times_portfolio import security_dashboard_resolution_times_portfolio_data
        cache_attrs = ['data', 'metadata', 'system_names']
        for attr in cache_attrs:
            security_dashboard_resolution_times_portfolio_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.security_dashboard_resolution_times_portfolio.sigrid_api')
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        from report_generator.generator.data_models.portfolio.security_dashboard_resolution_times_portfolio import security_dashboard_resolution_times_portfolio_data
        
        mock_data = {
            'systems': [
                {'system': 'system1', 'avgResolutionTime': 15.5},
                {'system': 'system2', 'avgResolutionTime': 20.3}
            ]
        }
        mock_sigrid_api.get_portfolio_security_resolution_time_findings.return_value = mock_data
        
        security_dashboard_resolution_times_portfolio_data.__dict__.pop('data', None)
        
        system = security_dashboard_resolution_times_portfolio_data.get_system('system1')
        
        assert system is not None
        assert system['system'] == 'system1'
        assert system['avgResolutionTime'] == 15.5

    @patch('report_generator.generator.data_models.portfolio.security_dashboard_resolution_times_portfolio.sigrid_api')
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        from report_generator.generator.data_models.portfolio.security_dashboard_resolution_times_portfolio import security_dashboard_resolution_times_portfolio_data
        
        mock_data = {
            'systems': [
                {'system': 'system1', 'avgResolutionTime': 15.5},
                {'system': 'system2', 'avgResolutionTime': 20.3},
                {'system': 'system3', 'avgResolutionTime': 10.0}
            ]
        }
        mock_sigrid_api.get_portfolio_security_resolution_time_findings.return_value = mock_data
        
        for attr in ['data', 'system_names']:
            security_dashboard_resolution_times_portfolio_data.__dict__.pop(attr, None)
        
        names = security_dashboard_resolution_times_portfolio_data.system_names
        
        assert len(names) == 3
        assert 'system1' in names
        assert 'system2' in names
        assert 'system3' in names


class TestOSHPortfolioData:
    """Test cases for OSHRatingsPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        from report_generator.generator.data_models.portfolio.osh_portfolio import osh_ratings_portfolio_data
        cache_attrs = ['data', 'metadata', 'period', 'system_names']
        for attr in cache_attrs:
            osh_ratings_portfolio_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.osh_portfolio.sigrid_api')
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        from report_generator.generator.data_models.portfolio.osh_portfolio import osh_ratings_portfolio_data
        
        mock_data = {
            'systems': [
                {'systemName': 'system1', 'oshRating': 4.5},
                {'systemName': 'system2', 'oshRating': 3.8}
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data
        
        osh_ratings_portfolio_data.__dict__.pop('data', None)
        
        system = osh_ratings_portfolio_data.get_system('system1')
        
        assert system is not None
        assert system['systemName'] == 'system1'
        assert system['oshRating'] == 4.5

    @patch('report_generator.generator.data_models.portfolio.osh_portfolio.sigrid_api')
    def test_find_system_returns_correct_system(self, mock_sigrid_api):
        """Test that find_system returns correct system data (alias for get_system)."""
        from report_generator.generator.data_models.portfolio.osh_portfolio import osh_ratings_portfolio_data
        
        mock_data = {
            'systems': [
                {'systemName': 'system1', 'oshRating': 4.5}
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data
        
        osh_ratings_portfolio_data.__dict__.pop('data', None)
        
        system = osh_ratings_portfolio_data.find_system('system1')
        
        assert system is not None
        assert system['systemName'] == 'system1'

    @patch('report_generator.generator.data_models.portfolio.osh_portfolio.sigrid_api')
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        from report_generator.generator.data_models.portfolio.osh_portfolio import osh_ratings_portfolio_data
        
        mock_data = {
            'systems': [
                {'systemName': 'system1', 'oshRating': 4.5},
                {'systemName': 'system2', 'oshRating': 3.8},
                {'systemName': 'system3', 'oshRating': 4.2}
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data
        
        for attr in ['data', 'system_names']:
            osh_ratings_portfolio_data.__dict__.pop(attr, None)
        
        names = osh_ratings_portfolio_data.system_names
        
        assert len(names) == 3
        assert 'system1' in names
        assert 'system2' in names
        assert 'system3' in names


class TestMaintainabilityPortfolioHelpers:
    """Test cases for helper functions in maintainability_portfolio module."""

    def test_initialize_statistics(self):
        """Test that _initialize_statistics returns correct structure."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import _initialize_statistics
        
        stats = _initialize_statistics()
        
        assert 'maintainability' in stats
        assert 'maintainability-change' in stats
        assert stats['maintainability']['1-star'] == 0
        assert stats['maintainability']['5-star'] == 0
        assert stats['maintainability']['number-of-systems'] == 0

    def test_is_system_active_returns_true_for_active(self):
        """Test that _is_system_active returns True for active non-dev systems."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import _is_system_active
        
        metadata = {'active': True, 'isDevelopmentOnly': False}
        
        assert _is_system_active(metadata) is True

    def test_is_system_active_returns_false_for_inactive(self):
        """Test that _is_system_active returns False for inactive systems."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import _is_system_active
        
        metadata = {'active': False, 'isDevelopmentOnly': False}
        
        assert _is_system_active(metadata) is False

    def test_is_system_active_returns_false_for_dev_only(self):
        """Test that _is_system_active returns False for dev-only systems."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import _is_system_active
        
        metadata = {'active': True, 'isDevelopmentOnly': True}
        
        assert _is_system_active(metadata) is False

    def test_weighted_avg_calculates_correctly(self):
        """Test that _weighted_avg calculates weighted average correctly."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import _weighted_avg
        
        values = [4.0, 3.0, 5.0]
        weights = [10, 5, 15]
        
        # (4.0*10 + 3.0*5 + 5.0*15) / (10+5+15) = (40+15+75) / 30 = 130/30 = 4.333...
        result = _weighted_avg(values, weights)
        
        assert abs(result - 4.333333) < 0.01

    def test_weighted_avg_handles_zero_weights(self):
        """Test that _weighted_avg handles zero total weight gracefully."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import _weighted_avg
        
        values = [4.0, 3.0]
        weights = [0, 0]
        
        result = _weighted_avg(values, weights)
        
        # Should return a very small number instead of crashing
        assert result == 0.000001

    def test_parse_date_converts_string_to_datetime(self):
        """Test that _parse_date correctly parses date strings."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import _parse_date
        from datetime import datetime
        
        result = _parse_date("2024-01-15")
        
        assert result == datetime(2024, 1, 15)

    def test_update_star_statistics_increments_correctly(self):
        """Test that _update_star_statistics updates statistics correctly."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import (
            _initialize_statistics, _update_star_statistics
        )
        
        stats = _initialize_statistics()
        end_snapshot = {'maintainability': 4.5}
        
        _update_star_statistics(stats, end_snapshot)
        
        assert stats['maintainability']['5-star'] == 1
        assert stats['maintainability']['number-of-systems'] == 1

    def test_finalize_change_statistics_with_increase(self):
        """Test that _finalize_change_statistics records increases."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import (
            _initialize_statistics, _finalize_change_statistics
        )
        
        stats = _initialize_statistics()
        best_inc = ('system1', 0.5)
        best_dec = (None, float('inf'))
        
        _finalize_change_statistics(stats, best_inc, best_dec)
        
        assert 'system1' in stats['maintainability-change']['increase']
        assert stats['maintainability-change']['increase']['system1'] == 0.5

    def test_finalize_change_statistics_with_decrease(self):
        """Test that _finalize_change_statistics records decreases."""
        from report_generator.generator.data_models.portfolio.maintainability_portfolio import (
            _initialize_statistics, _finalize_change_statistics
        )
        
        stats = _initialize_statistics()
        best_inc = (None, float('-inf'))
        best_dec = ('system2', -0.3)
        
        _finalize_change_statistics(stats, best_inc, best_dec)
        
        assert 'system2' in stats['maintainability-change']['decrease']
        assert stats['maintainability-change']['decrease']['system2'] == -0.3


class TestModernizationHelpers:
    """Test cases for helper functions in modernization module."""

    def test_get_renovation_effort_for_keep_as_is(self):
        """Test that get_renovation_effort returns 0 for KEEP_AS_IS."""
        from report_generator.generator.data_models.portfolio.modernization import (
            get_renovation_effort, Scenario
        )
        
        effort = get_renovation_effort(Scenario.KEEP_AS_IS, {}, 100.0)
        
        assert effort == 0.0

    def test_get_renovation_effort_for_replace(self):
        """Test that get_renovation_effort returns 0 for REPLACE."""
        from report_generator.generator.data_models.portfolio.modernization import (
            get_renovation_effort, Scenario
        )
        
        effort = get_renovation_effort(Scenario.REPLACE, {}, 100.0)
        
        assert effort == 0.0

    def test_get_renovation_effort_for_rebuild(self):
        """Test that get_renovation_effort returns volume for REBUILD."""
        from report_generator.generator.data_models.portfolio.modernization import (
            get_renovation_effort, Scenario
        )
        
        effort = get_renovation_effort(Scenario.REBUILD, {}, 100.0)
        
        assert effort == 100.0

    def test_get_renovation_effort_for_renovate(self):
        """Test that get_renovation_effort returns renovation effort for RENOVATE."""
        from report_generator.generator.data_models.portfolio.modernization import (
            get_renovation_effort, Scenario
        )
        
        architecture_metrics = {'RENOVATION_EFFORT': 50.0}
        effort = get_renovation_effort(Scenario.RENOVATE, architecture_metrics, 100.0)
        
        assert effort == 50.0

    def test_get_activity_calculates_from_churn(self):
        """Test that get_activity calculates activity from churn percentage."""
        from report_generator.generator.data_models.portfolio.modernization import get_activity
        
        architecture_graph = {
            'systemElements': [{
                'measurementTimeSeries': {
                    'YEARLY_CHURN_PERCENTAGE': {'averageValue': 10.0}
                }
            }]
        }
        
        activity = get_activity(100.0, architecture_graph)
        
        # (10.0 / 100.0 * 52) * 100.0 = 520.0
        assert activity == 520.0

    def test_get_activity_returns_none_when_no_churn(self):
        """Test that get_activity returns None when churn data is missing."""
        from report_generator.generator.data_models.portfolio.modernization import get_activity
        
        architecture_graph = {
            'systemElements': [{
                'measurementTimeSeries': {}
            }]
        }
        
        activity = get_activity(100.0, architecture_graph)
        
        assert activity is None

    def test_get_change_speed_returns_zero_for_keep_as_is(self):
        """Test that get_change_speed returns 0 for KEEP_AS_IS."""
        from report_generator.generator.data_models.portfolio.modernization import (
            get_change_speed, Scenario
        )
        
        speed = get_change_speed(Scenario.KEEP_AS_IS, {})
        
        assert speed == 0.0

    def test_get_change_speed_returns_potential_for_renovate(self):
        """Test that get_change_speed returns potential change speed for RENOVATE."""
        from report_generator.generator.data_models.portfolio.modernization import (
            get_change_speed, Scenario
        )
        
        architecture_metrics = {'POTENTIAL_CHANGE_SPEED': 1.5}
        speed = get_change_speed(Scenario.RENOVATE, architecture_metrics)
        
        assert speed == 1.5


class TestArchitecturePortfolioData:
    """Test cases for ArchitecturePortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        portfolio_arguments._team = None
        portfolio_arguments._division = None
        
        from report_generator.generator.data_models.portfolio.architecture_portfolio import architecture_portfolio_data
        cache_attrs = ['data', 'metadata', 'period', 'system_names']
        for attr in cache_attrs:
            architecture_portfolio_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.architecture_portfolio.sigrid_api')
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        from report_generator.generator.data_models.portfolio.architecture_portfolio import architecture_portfolio_data
        
        mock_data = [
            {'system': 'system1', 'architectureQuality': 4.5},
            {'system': 'system2', 'architectureQuality': 3.8}
        ]
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = mock_data
        
        architecture_portfolio_data.__dict__.pop('data', None)
        
        system = architecture_portfolio_data.get_system('system1')
        
        assert system is not None
        assert system['system'] == 'system1'
        assert system['architectureQuality'] == 4.5

    @patch('report_generator.generator.data_models.portfolio.architecture_portfolio.sigrid_api')
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        from report_generator.generator.data_models.portfolio.architecture_portfolio import architecture_portfolio_data
        
        mock_data = [
            {'system': 'system1', 'architectureQuality': 4.5},
            {'system': 'system2', 'architectureQuality': 3.8},
            {'system': 'system3', 'architectureQuality': 4.2}
        ]
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = mock_data
        
        for attr in ['data', 'system_names']:
            architecture_portfolio_data.__dict__.pop(attr, None)
        
        names = architecture_portfolio_data.system_names
        
        assert len(names) == 3
        assert 'system1' in names
        assert 'system2' in names
        assert 'system3' in names


class TestMaintainabilityDeltaQualityPortfolio:
    """Test cases for MaintainabilityDeltaQualityPortfolio models."""

    def teardown_method(self):
        """Clean up cached data after each test."""
        from report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio import (
            maintainability_delta_quality_new_code,
            maintainability_delta_quality_changed_code,
            maintainability_delta_quality_new_and_changed_code
        )
        
        for model in [maintainability_delta_quality_new_code, maintainability_delta_quality_changed_code, maintainability_delta_quality_new_and_changed_code]:
            cache_attrs = ['data', 'system_names']
            for attr in cache_attrs:
                model.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.maintainability_portfolio_data')
    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.sigrid_api')
    def test_new_code_get_type_returns_new_code(self, mock_sigrid_api, mock_portfolio_data):
        """Test that new code model returns NEW_CODE type."""
        from report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio import (
            maintainability_delta_quality_new_code
        )
        
        assert maintainability_delta_quality_new_code.get_type() == "NEW_CODE"

    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.maintainability_portfolio_data')
    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.sigrid_api')
    def test_changed_code_get_type_returns_changed_code(self, mock_sigrid_api, mock_portfolio_data):
        """Test that changed code model returns CHANGED_CODE type."""
        from report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio import (
            maintainability_delta_quality_changed_code
        )
        
        assert maintainability_delta_quality_changed_code.get_type() == "CHANGED_CODE"

    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.maintainability_portfolio_data')
    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.sigrid_api')
    def test_new_and_changed_code_get_type_returns_new_and_changed_code(self, mock_sigrid_api, mock_portfolio_data):
        """Test that new and changed code model returns NEW_AND_CHANGED_CODE type."""
        from report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio import (
            maintainability_delta_quality_new_and_changed_code
        )
        
        assert maintainability_delta_quality_new_and_changed_code.get_type() == "NEW_AND_CHANGED_CODE"

    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.maintainability_portfolio_data')
    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.sigrid_api')
    def test_get_system_returns_delta_quality_data(self, mock_sigrid_api, mock_portfolio_data):
        """Test that get_system returns delta quality data for a system."""
        from report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio import (
            maintainability_delta_quality_new_code
        )
        
        mock_portfolio_data.system_names = ['system1', 'system2']
        mock_sigrid_api.get_maintainability_delta_quality.side_effect = [
            {'quality': 4.5},
            {'quality': 3.8}
        ]
        
        maintainability_delta_quality_new_code.__dict__.pop('data', None)
        
        system_data = maintainability_delta_quality_new_code.get_system('system1')
        
        assert system_data is not None
        assert system_data['quality'] == 4.5

    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.maintainability_portfolio_data')
    @patch('report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio.sigrid_api')
    def test_handles_api_request_failed(self, mock_sigrid_api, mock_portfolio_data):
        """Test that API request failures are handled gracefully."""
        from report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio import (
            maintainability_delta_quality_new_code
        )
        
        # Create a proper exception class
        class SigridAPIRequestFailed(Exception):
            pass
        
        mock_sigrid_api.SigridAPIRequestFailed = SigridAPIRequestFailed
        mock_portfolio_data.system_names = ['system1']
        mock_sigrid_api.get_maintainability_delta_quality.side_effect = SigridAPIRequestFailed("Not found")
        
        maintainability_delta_quality_new_code.__dict__.pop('data', None)
        
        system_data = maintainability_delta_quality_new_code.get_system('system1')
        
        assert system_data is None


class TestSystemSecurityData:
    """Test cases for SecurityData model."""

    def teardown_method(self):
        """Clean up cached data after each test."""
        from report_generator.generator.data_models.system.security import security_data
        cache_attrs = ['findings', 'security_rating']
        for attr in cache_attrs:
            security_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.system.security.sigrid_api')
    def test_count_findings_by_severity(self, mock_sigrid_api):
        """Test that count_findings correctly counts findings by severity."""
        from report_generator.generator.data_models.system.security import security_data
        
        mock_findings = [
            {'severity': 'HIGH', 'description': 'Issue 1'},
            {'severity': 'HIGH', 'description': 'Issue 2'},
            {'severity': 'MEDIUM', 'description': 'Issue 3'},
            {'severity': 'LOW', 'description': 'Issue 4'}
        ]
        mock_sigrid_api.get_security_findings.return_value = mock_findings
        
        security_data.__dict__.pop('findings', None)
        
        assert security_data.count_findings('HIGH') == 2
        assert security_data.count_findings('MEDIUM') == 1
        assert security_data.count_findings('LOW') == 1

    @patch('report_generator.generator.data_models.system.security.sigrid_api')
    def test_security_rating_returns_rating(self, mock_sigrid_api):
        """Test that security_rating returns the rating from API."""
        from report_generator.generator.data_models.system.security import security_data
        
        mock_sigrid_api.get_security_ratings.return_value = {'rating': 4.5}
        
        security_data.__dict__.pop('security_rating', None)
        
        rating = security_data.security_rating
        
        assert rating == 4.5


class TestSystemMetadata:
    """Test cases for SystemMetadata model."""

    def teardown_method(self):
        """Clean up cached data after each test."""
        from report_generator.generator.data_models.system.system_metadata import system_metadata
        cache_attrs = ['data']
        for attr in cache_attrs:
            system_metadata.__dict__.pop(attr, None)

    @patch('report_generator.generator.data_models.system.system_metadata.sigrid_api')
    def test_display_name_attribute_access(self, mock_sigrid_api):
        """Test that display_name can be accessed via attribute."""
        from report_generator.generator.data_models.system.system_metadata import system_metadata
        
        mock_sigrid_api.get_system_metadata.return_value = {
            'displayName': 'My System'
        }
        
        system_metadata.__dict__.pop('data', None)
        
        name = system_metadata.display_name
        
        assert name == 'My System'

    @patch('report_generator.generator.data_models.system.system_metadata.sigrid_api')
    def test_division_name_attribute_access(self, mock_sigrid_api):
        """Test that division_name can be accessed via attribute."""
        from report_generator.generator.data_models.system.system_metadata import system_metadata
        
        mock_sigrid_api.get_system_metadata.return_value = {
            'divisionName': 'Engineering'
        }
        
        system_metadata.__dict__.pop('data', None)
        
        division = system_metadata.division_name
        
        assert division == 'Engineering'

    @patch('report_generator.generator.data_models.system.system_metadata.sigrid_api')
    def test_team_names_attribute_access(self, mock_sigrid_api):
        """Test that team_names can be accessed via attribute."""
        from report_generator.generator.data_models.system.system_metadata import system_metadata
        
        mock_sigrid_api.get_system_metadata.return_value = {
            'teamNames': ['Team A', 'Team B']
        }
        
        system_metadata.__dict__.pop('data', None)
        
        teams = system_metadata.team_names
        
        assert teams == ['Team A', 'Team B']


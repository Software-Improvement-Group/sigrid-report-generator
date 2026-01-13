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
from report_generator.generator.data_models.system.maintainability import _sort_and_aggregate_technology_data
# noinspection PyProtectedMember
from report_generator.generator.data_models.portfolio.osh_portfolio import OSHRatingsPortfolioData
# noinspection PyProtectedMember
from report_generator.generator.data_models.portfolio.security_portfolio import SecurityRatingsPortfolioData
# noinspection PyProtectedMember
from report_generator.generator.data_models.portfolio.security_dashboard_findings_portfolio import SecurityDashboardFindingsPortfolioData
# noinspection PyProtectedMember
from report_generator.generator.data_models.portfolio.security_dashboard_resolution_times_portfolio import SecurityDashboardResolutionTimesPortfolioData
# noinspection PyProtectedMember
from report_generator.generator.data_models.portfolio.maintainability_portfolio import (
    MaintainabilityPortfolioData,
    maintainability_portfolio_data
)
# noinspection PyProtectedMember
from report_generator.generator.data_models.portfolio.architecture_portfolio import ArchitecturePortfolioData
# noinspection PyProtectedMember
from report_generator.generator.data_models.portfolio.maintainability_delta_quality_portfolio import (
    _AbstractMaintainabilityDeltaQualityPortfolioData
)


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


class TestOSHPortfolioData:
    def test_extract_osh_rating_with_valid_data(self):
        """Test _extract_osh_rating extracts ratings correctly from SBOM metadata."""
        portfolio = OSHRatingsPortfolioData()
        system = {
            'sbom': {
                'metadata': {
                    'properties': [
                        {'name': 'sigrid:ratings:system', 'value': '4.5'},
                        {'name': 'sigrid:ratings:vulnerability', 'value': '3.2'}
                    ]
                }
            }
        }
        
        rating = portfolio._extract_osh_rating(system, 'system')
        assert rating == 4.5
        
        rating = portfolio._extract_osh_rating(system, 'vulnerability')
        assert rating == 3.2
    
    def test_extract_osh_rating_with_missing_metadata(self):
        """Test _extract_osh_rating returns None when metadata is missing."""
        portfolio = OSHRatingsPortfolioData()
        system = {'sbom': {}}
        
        rating = portfolio._extract_osh_rating(system, 'system')
        assert rating is None
    
    def test_extract_osh_rating_with_missing_property(self):
        """Test _extract_osh_rating returns None when requested property doesn't exist."""
        portfolio = OSHRatingsPortfolioData()
        system = {
            'sbom': {
                'metadata': {
                    'properties': [
                        {'name': 'sigrid:ratings:vulnerability', 'value': '3.2'}
                    ]
                }
            }
        }
        
        rating = portfolio._extract_osh_rating(system, 'system')
        assert rating is None
    
    def test_extract_osh_rating_with_invalid_value(self):
        """Test _extract_osh_rating returns None when rating value is not a valid float."""
        portfolio = OSHRatingsPortfolioData()
        system = {
            'sbom': {
                'metadata': {
                    'properties': [
                        {'name': 'sigrid:ratings:system', 'value': 'invalid'}
                    ]
                }
            }
        }
        
        rating = portfolio._extract_osh_rating(system, 'system')
        assert rating is None


class TestRatingDistributionPercentages:
    def test_osh_rating_distribution_calculation(self, mocker):
        """Test get_rating_distribution_percentages calculates percentages correctly for OSH."""
        portfolio = OSHRatingsPortfolioData()
        
        # Mock raw_data to return test data without making API calls
        mock_data = {
            'systems': [
                self._mock_osh_system('system1', 4.5),  # above market
                self._mock_osh_system('system2', 3.0),  # market average
                self._mock_osh_system('system3', 2.0),  # below market
                self._mock_osh_system('system4', 3.5),  # above market
            ]
        }
        mocker.patch.object(type(portfolio), 'raw_data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        distribution = portfolio.get_rating_distribution_percentages
        assert distribution['above_market'] == 50.0
        assert distribution['market_average'] == 25.0
        assert distribution['below_market'] == 25.0
    
    def test_osh_rating_distribution_with_no_systems(self, mocker):
        """Test get_rating_distribution_percentages handles empty systems list."""
        portfolio = OSHRatingsPortfolioData()
        mocker.patch.object(type(portfolio), 'raw_data', new_callable=mocker.PropertyMock, return_value={'systems': []})
        
        distribution = portfolio.get_rating_distribution_percentages
        assert distribution['above_market'] == 0.0
        assert distribution['market_average'] == 0.0
        assert distribution['below_market'] == 0.0
    
    def test_osh_rating_distribution_all_above_market(self, mocker):
        """Test get_rating_distribution_percentages when all systems are above market."""
        portfolio = OSHRatingsPortfolioData()
        
        mock_data = {
            'systems': [
                self._mock_osh_system('system1', 4.5),
                self._mock_osh_system('system2', 5.0),
                self._mock_osh_system('system3', 3.8),
            ]
        }
        mocker.patch.object(type(portfolio), 'raw_data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        distribution = portfolio.get_rating_distribution_percentages
        assert distribution['above_market'] == 100.0
        assert distribution['market_average'] == 0.0
        assert distribution['below_market'] == 0.0
    
    def test_security_rating_distribution_calculation(self, mocker):
        """Test get_rating_distribution_percentages for security portfolio."""
        portfolio = SecurityRatingsPortfolioData()
        
        # Test with 'rating' field (actual API response format)
        mock_data = [
            {'systemName': 'system1', 'rating': 4.5},  # above market
            {'systemName': 'system2', 'rating': 3.0},  # market average
            {'systemName': 'system3', 'rating': 2.0},  # below market
            {'systemName': 'system4', 'rating': 3.7},  # above market
        ]
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        distribution = portfolio.get_rating_distribution_percentages
        assert distribution['above_market'] == 50.0
        assert distribution['market_average'] == 25.0
        assert distribution['below_market'] == 25.0
    
    def test_rating_distribution_edge_case_exact_thresholds(self, mocker):
        """Test rating distribution with values exactly at thresholds."""
        portfolio = OSHRatingsPortfolioData()
        
        mock_data = {
            'systems': [
                self._mock_osh_system('system1', 3.5),  # exactly at upper threshold (above market)
                self._mock_osh_system('system2', 2.5),  # exactly at lower threshold (market average)
            ]
        }
        mocker.patch.object(type(portfolio), 'raw_data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        distribution = portfolio.get_rating_distribution_percentages
        assert distribution['above_market'] == 50.0
        assert distribution['market_average'] == 50.0
        assert distribution['below_market'] == 0.0
    
    @staticmethod
    def _mock_osh_system(name, rating):
        return {
            'systemName': name,
            'sbom': {
                'metadata': {
                    'properties': [
                        {'name': 'sigrid:ratings:system', 'value': str(rating)}
                    ]
                }
            }
        }


class TestWeightedAverageRatings:
    def test_security_weighted_average_rating(self, mocker):
        """Test weighted average rating calculation for security portfolio."""
        portfolio = SecurityRatingsPortfolioData()
        
        mock_data = [
            {'systemName': 'system1', 'rating': 4.0},
            {'systemName': 'system2', 'rating': 3.0},
            {'systemName': 'system3', 'rating': 2.0},
        ]
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        # Mock maintainability portfolio to return volume data
        def mock_end_snapshot(system_name):
            volumes = {'system1': 100, 'system2': 200, 'system3': 100}
            return {'volumeInPersonMonths': volumes.get(system_name, 0)}
        
        mocker.patch.object(maintainability_portfolio_data, 'end_snapshot', side_effect=mock_end_snapshot)
        
        # Weighted average = (4.0*100 + 3.0*200 + 2.0*100) / (100+200+100) = 1200/400 = 3.0
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == 3.0
    
    def test_security_weighted_average_with_zero_volume(self, mocker):
        """Test weighted average handles systems with zero volume."""
        
        portfolio = SecurityRatingsPortfolioData()
        
        mock_data = [
            {'systemName': 'system1', 'rating': 4.0},
            {'systemName': 'system2', 'rating': 5.0},  # Should be excluded due to zero volume
        ]
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        # Mock maintainability portfolio to return volume data
        def mock_end_snapshot(system_name):
            volumes = {'system1': 100, 'system2': 0}
            return {'volumeInPersonMonths': volumes.get(system_name, 0)}
        
        mocker.patch.object(maintainability_portfolio_data, 'end_snapshot', side_effect=mock_end_snapshot)
        
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == 4.0
    
    def test_security_weighted_average_empty_data(self, mocker):
        """Test weighted average returns 0 for empty data."""
        portfolio = SecurityRatingsPortfolioData()
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=[])
        
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == 0.0
    
    def test_osh_weighted_average_rating(self, mocker):
        """Test weighted average rating calculation for OSH portfolio."""
        portfolio = OSHRatingsPortfolioData()
        
        mock_raw_data = {
            'systems': [
                {
                    'systemName': 'system1',
                    'sbom': {
                        'metadata': {
                            'properties': [{'name': 'sigrid:ratings:system', 'value': '4.0'}]
                        }
                    }
                },
                {
                    'systemName': 'system2',
                    'sbom': {
                        'metadata': {
                            'properties': [{'name': 'sigrid:ratings:system', 'value': '3.0'}]
                        }
                    }
                }
            ]
        }
        mocker.patch.object(type(portfolio), 'raw_data', new_callable=mocker.PropertyMock, return_value=mock_raw_data)
        
        # Mock maintainability portfolio to return volume data
        def mock_end_snapshot(system_name):
            volumes = {'system1': 10000, 'system2': 20000}
            return {'volumeInPersonMonths': volumes.get(system_name, 0)}
        
        mocker.patch.object(maintainability_portfolio_data, 'end_snapshot', side_effect=mock_end_snapshot)
        
        # Weighted average = (4.0*10000 + 3.0*20000) / (10000+20000) = 100000/30000 = 3.333... truncated to 3.3
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == 3.3
    
    def test_maintainability_weighted_average_rating(self, mocker):
        """Test weighted average rating calculation for maintainability portfolio."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        def mock_end_snapshot(system_name):
            if system_name == 'system1':
                return {'maintainability': 4.0, 'volumeInPersonMonths': 50}
            else:
                return {'maintainability': 3.0, 'volumeInPersonMonths': 100}
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        # Weighted average = (4.0*50 + 3.0*100) / (50+100) = 500/150 = 3.333... truncated to 3.3
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == 3.3
    
    def test_architecture_weighted_average_rating(self, mocker):
        """Test weighted average rating calculation for architecture portfolio."""
        portfolio = ArchitecturePortfolioData()
        
        mock_data = [
            {'system': 'system1', 'ratings': {'architecture': 4.0}},
            {'system': 'system2', 'ratings': {'architecture': 2.0}},
        ]
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        # Mock maintainability portfolio to return volume data
        def mock_end_snapshot(system_name):
            volumes = {'system1': 80, 'system2': 40}
            return {'volumeInPersonMonths': volumes.get(system_name, 0)}
        
        mocker.patch.object(maintainability_portfolio_data, 'end_snapshot', side_effect=mock_end_snapshot)
        
        # Weighted average = (4.0*80 + 2.0*40) / (80+40) = 400/120 = 3.333... truncated to 3.3
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == 3.3


class TestMaintainabilityStatistics:
    """Test the statistics cached property for maintainability portfolio."""
    
    def test_statistics_with_changes(self, mocker):
        """Test statistics calculation with systems that have increased, decreased, and stayed stable."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3', 'system4']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        # Mock period
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        # System 1: Improved from 2.5 (3 stars) to 3.5 (4 stars) - diff = 1.0
        # System 2: Declined from 4.5 (5 stars) to 3.5 (4 stars) - diff = -1.0
        # System 3: Stable at 3.5 (4 stars) - diff = 0.0
        # System 4: Improved from 3.0 (3 stars) to 3.8 (4 stars) - diff = 0.8
        
        def mock_start_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 2.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 4.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 200},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 150},
                'system4': {'maintainability': 3.0, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 50}
            }
            return snapshots[system_name]
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 200},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 150},
                'system4': {'maintainability': 3.8, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 50}
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Verify star distribution (all systems are 4 stars at end)
        assert stats['maintainability']['1-star'] == 0
        assert stats['maintainability']['2-star'] == 0
        assert stats['maintainability']['3-star'] == 0
        assert stats['maintainability']['4-star'] == 4  # All systems end at 3.5-3.8 which is 4 stars
        assert stats['maintainability']['5-star'] == 0
        assert stats['maintainability']['number-of-systems'] == 4
        
        # Verify change counts (system4 improved from 3 stars to 4 stars)
        assert stats['maintainability-change']['systems-increased'] == 2  # system1 (2→4), system4 (3→4)
        assert stats['maintainability-change']['systems-decreased'] == 1  # system2 (4→4 but rating decreased)
        assert stats['maintainability-change']['systems-stable'] == 1    # system3 (4→4 and stable rating)
        
        # Verify biggest changes
        assert 'system1' in stats['maintainability-change']['biggest-increase']
        assert stats['maintainability-change']['biggest-increase']['system1'] == 1.0
        assert 'system2' in stats['maintainability-change']['biggest-decrease']
        assert stats['maintainability-change']['biggest-decrease']['system2'] == -1.0
        
        # Verify averages exist
        assert 'start-average' in stats['maintainability']
        assert 'end-average' in stats['maintainability']
    
    def test_statistics_all_stable(self, mocker):
        """Test statistics when all systems remain stable."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(maintainability_portfolio_data), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        def mock_start_snapshot(system_name):
            return {
                'maintainability': 3.5,
                'maintainabilityDate': '2024-02-01',
                'volumeInPersonMonths': 100
            }
        
        def mock_end_snapshot(system_name):
            return {
                'maintainability': 3.5,
                'maintainabilityDate': '2024-12-31',
                'volumeInPersonMonths': 100
            }
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        assert stats['maintainability-change']['systems-increased'] == 0
        assert stats['maintainability-change']['systems-decreased'] == 0
        assert stats['maintainability-change']['systems-stable'] == 2
        assert stats['maintainability-change']['biggest-increase'] == {}
        assert stats['maintainability-change']['biggest-decrease'] == {}
    
    def test_statistics_excludes_inactive_systems(self, mocker):
        """Test that inactive and development-only systems are excluded from statistics."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['active_system', 'inactive_system', 'dev_only_system']
        
        def mock_get_system_metadata(system_name):
            if system_name == 'inactive_system':
                return {'active': False, 'isDevelopmentOnly': False}
            elif system_name == 'dev_only_system':
                return {'active': True, 'isDevelopmentOnly': True}
            else:
                return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        def mock_start_snapshot(system_name):
            return {
                'maintainability': 3.0,
                'maintainabilityDate': '2024-02-01',
                'volumeInPersonMonths': 100
            }
        
        def mock_end_snapshot(system_name):
            return {
                'maintainability': 4.0,
                'maintainabilityDate': '2024-12-31',
                'volumeInPersonMonths': 100
            }
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Only active_system should be counted
        assert stats['maintainability']['number-of-systems'] == 1
        assert stats['maintainability-change']['systems-increased'] == 1
    
    def test_statistics_no_change_when_dates_same(self, mocker):
        """Test that systems with same start and end date count as stable (diff=0)."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(maintainability_portfolio_data), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        def mock_start_snapshot(system_name):
            return {
                'maintainability': 3.0,
                'maintainabilityDate': '2024-12-31',  # Same as end date
                'volumeInPersonMonths': 100
            }
        
        def mock_end_snapshot(system_name):
            return {
                'maintainability': 4.0,
                'maintainabilityDate': '2024-12-31',
                'volumeInPersonMonths': 100
            }
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # System should be counted in star statistics, and when dates are same, diff=0 counts as stable
        assert stats['maintainability']['number-of-systems'] == 1
        assert stats['maintainability-change']['systems-increased'] == 0
        assert stats['maintainability-change']['systems-decreased'] == 0
        assert stats['maintainability-change']['systems-stable'] == 1
    
    def test_statistics_volume_change_tracking(self, mocker):
        """Test that volume changes are tracked correctly in statistics."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        # System 1: volume increased from 100 to 150 (+50)
        # System 2: volume decreased from 200 to 180 (-20)
        # System 3: volume increased from 50 to 90 (+40)
        # Total start: 350, Total end: 420, biggest change: system1 (+50)
        
        def mock_start_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 200},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 50}
            }
            return snapshots[system_name]
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 150},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 180},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 90}
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Verify volume totals
        assert stats['volume-change']['total-start'] == 350
        assert stats['volume-change']['total-end'] == 420
        
        # Verify biggest change tracking
        assert stats['volume-change']['biggest-change-system'] == 'system1'
        assert stats['volume-change']['biggest-change-amount'] == 50
    
    def test_statistics_volume_decrease(self, mocker):
        """Test that volume decreases are tracked correctly."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        # System 1: volume decreased from 100 to 80 (-20)
        # System 2: volume decreased from 200 to 50 (-150) - biggest change
        
        def mock_start_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 200}
            }
            return snapshots[system_name]
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 80},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 50}
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Verify volume totals
        assert stats['volume-change']['total-start'] == 300
        assert stats['volume-change']['total-end'] == 130
        
        # Verify biggest change tracking (should track the largest absolute change)
        assert stats['volume-change']['biggest-change-system'] == 'system2'
        assert stats['volume-change']['biggest-change-amount'] == -150
    
    def test_statistics_volume_no_change(self, mocker):
        """Test volume tracking when there are no volume changes."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        def mock_start_snapshot(system_name):
            return {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 100}
        
        def mock_end_snapshot(system_name):
            return {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'volumeInPersonMonths': 100}
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Verify volume totals are equal
        assert stats['volume-change']['total-start'] == 100
        assert stats['volume-change']['total-end'] == 100
        
        # When all changes are 0, there's no "biggest" change - it remains None
        assert stats['volume-change']['biggest-change-system'] is None
        assert stats['volume-change']['biggest-change-amount'] == 0
    
    def test_statistics_with_none_ratings(self, mocker):
        """Test statistics when some systems have None ratings."""
        class TestDeltaQualityPortfolio(_AbstractMaintainabilityDeltaQualityPortfolioData):
            def get_type(self):
                return "NEW_CODE"
        
        portfolio = TestDeltaQualityPortfolio()
        
        mock_system_names = ['system1', 'system2', 'system3']
        mock_data = {
            'system1': {
                'filesRatingAtEnd': 4.0,
                'systemRatingAtEnd': 3.5
            },
            'system2': {
                'filesRatingAtEnd': None,  # No new code
                'systemRatingAtEnd': 3.0
            },
            'system3': {
                'filesRatingAtEnd': 3.0,
                'systemRatingAtEnd': 3.0
            }
        }
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        stats = portfolio.statistics
        
        # Should only count system1 and system3: (4.0 + 3.0) / 2 = 3.5
        assert stats['avg_stars'] == 3.5
        assert stats['count'] == 2
        
        # Extremes should only be from systems with ratings
        assert stats['lowest_system'][0] == 'system3'
        assert stats['lowest_system'][1] == 3.0
        assert stats['highest_system'][0] == 'system1'
        assert stats['highest_system'][1] == 4.0
    
    def test_statistics_with_no_systems(self, mocker):
        """Test statistics when there are no systems."""
        class TestDeltaQualityPortfolio(_AbstractMaintainabilityDeltaQualityPortfolioData):
            def get_type(self):
                return "NEW_CODE"
        
        portfolio = TestDeltaQualityPortfolio()
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=[])
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value={})
        
        stats = portfolio.statistics
        
        assert stats['avg_stars'] == 0
        assert stats['count'] == 0
        assert stats['lowest_system'] is None
        assert stats['highest_system'] is None
    
    def test_statistics_with_all_none_ratings(self, mocker):
        """Test statistics when all systems have None ratings."""
        class TestDeltaQualityPortfolio(_AbstractMaintainabilityDeltaQualityPortfolioData):
            def get_type(self):
                return "NEW_CODE"
        
        portfolio = TestDeltaQualityPortfolio()
        
        mock_system_names = ['system1', 'system2']
        mock_data = {
            'system1': {
                'filesRatingAtEnd': None,
                'systemRatingAtEnd': 3.0
            },
            'system2': {
                'filesRatingAtEnd': None,
                'systemRatingAtEnd': 3.5
            }
        }
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        stats = portfolio.statistics
        
        assert stats['avg_stars'] == 0
        assert stats['count'] == 0
        assert stats['lowest_system'] is None
        assert stats['highest_system'] is None
    
    def test_statistics_single_system(self, mocker):
        """Test statistics with a single system."""
        class TestDeltaQualityPortfolio(_AbstractMaintainabilityDeltaQualityPortfolioData):
            def get_type(self):
                return "CHANGED_CODE"
        
        portfolio = TestDeltaQualityPortfolio()
        
        mock_system_names = ['only_system']
        mock_data = {
            'only_system': {
                'filesRatingAtEnd': 3.7,
                'systemRatingAtEnd': 3.5
            }
        }
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        stats = portfolio.statistics
        
        assert stats['avg_stars'] == 3.7
        assert stats['count'] == 1
        assert stats['lowest_system'][0] == 'only_system'
        assert stats['lowest_system'][1] == 3.7
        assert stats['highest_system'][0] == 'only_system'
        assert stats['highest_system'][1] == 3.7
    
    def test_update_extremes(self, mocker):
        """Test the _update_extremes method updates lowest and highest correctly."""
        class TestDeltaQualityPortfolio(_AbstractMaintainabilityDeltaQualityPortfolioData):
            def get_type(self):
                return "NEW_CODE"
        
        portfolio = TestDeltaQualityPortfolio()
        
        lowest = (None, float('inf'))
        highest = (None, float('-inf'))
        
        # First update
        lowest, highest = portfolio._update_extremes(3.5, 'system1', lowest, highest)
        assert lowest == ('system1', 3.5)
        assert highest == ('system1', 3.5)
        
        # Update with higher rating
        lowest, highest = portfolio._update_extremes(4.2, 'system2', lowest, highest)
        assert lowest == ('system1', 3.5)
        assert highest == ('system2', 4.2)
        
        # Update with lower rating
        lowest, highest = portfolio._update_extremes(2.1, 'system3', lowest, highest)
        assert lowest == ('system3', 2.1)
        assert highest == ('system2', 4.2)
        
        # Update with middle rating (shouldn't change extremes)
        lowest, highest = portfolio._update_extremes(3.0, 'system4', lowest, highest)
        assert lowest == ('system3', 2.1)
        assert highest == ('system2', 4.2)


class TestTestCodeRatioDistribution:
    """Test the test_code_ratio_distribution_percentages method."""
    
    def test_test_code_ratio_distribution_mixed(self, mocker):
        """Test distribution with systems in all three categories."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3', 'system4', 'system5']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'testCodeRatio': 0.3},   # low (< 50%)
                'system2': {'maintainability': 3.5, 'testCodeRatio': 0.6},   # medium (50-100%)
                'system3': {'maintainability': 3.5, 'testCodeRatio': 1.2},   # high (≥ 100%)
                'system4': {'maintainability': 3.5, 'testCodeRatio': 0.8},   # medium (50-100%)
                'system5': {'maintainability': 3.5, 'testCodeRatio': 0.4},   # low (< 50%)
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        distribution = portfolio.test_code_ratio_distribution_percentages
        
        # 2 out of 5 = 40% low, 2 out of 5 = 40% medium, 1 out of 5 = 20% high
        assert distribution['low'] == 40
        assert distribution['medium'] == 40
        assert distribution['high'] == 20
    
    def test_test_code_ratio_distribution_all_low(self, mocker):
        """Test distribution when all systems have low test code ratio."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'testCodeRatio': 0.1},
                'system2': {'maintainability': 3.5, 'testCodeRatio': 0.25},
                'system3': {'maintainability': 3.5, 'testCodeRatio': 0.49},
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        distribution = portfolio.test_code_ratio_distribution_percentages
        
        assert distribution['low'] == 100
        assert distribution['medium'] == 0
        assert distribution['high'] == 0
    
    def test_test_code_ratio_distribution_with_none_values(self, mocker):
        """Test distribution when some systems have None test code ratio."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3', 'system4']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'testCodeRatio': 0.3},   # low
                'system2': {'maintainability': 3.5, 'testCodeRatio': None},  # should be excluded
                'system3': {'maintainability': 3.5, 'testCodeRatio': 1.0},   # high
                'system4': {'maintainability': 3.5},                         # missing key, should be excluded
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        distribution = portfolio.test_code_ratio_distribution_percentages
        
        # Only 2 systems counted: 1 low, 1 high = 50% each
        assert distribution['low'] == 50
        assert distribution['medium'] == 0
        assert distribution['high'] == 50
    
    def test_test_code_ratio_distribution_excludes_inactive_systems(self, mocker):
        """Test that inactive and development-only systems are excluded."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['active_system', 'inactive_system', 'dev_only_system']
        
        def mock_get_system_metadata(system_name):
            if system_name == 'inactive_system':
                return {'active': False, 'isDevelopmentOnly': False}
            elif system_name == 'dev_only_system':
                return {'active': True, 'isDevelopmentOnly': True}
            else:
                return {'active': True, 'isDevelopmentOnly': False}
        
        def mock_end_snapshot(system_name):
            return {'maintainability': 3.5, 'testCodeRatio': 0.3}  # all low
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        distribution = portfolio.test_code_ratio_distribution_percentages
        
        # Only active_system should be counted
        assert distribution['low'] == 100
        assert distribution['medium'] == 0
        assert distribution['high'] == 0
    
    def test_test_code_ratio_distribution_no_systems(self, mocker):
        """Test distribution with no systems."""
        portfolio = MaintainabilityPortfolioData()
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=[])
        
        distribution = portfolio.test_code_ratio_distribution_percentages
        
        assert distribution['low'] == 0
        assert distribution['medium'] == 0
        assert distribution['high'] == 0
    
    def test_test_code_ratio_distribution_boundary_values(self, mocker):
        """Test distribution with values exactly at boundaries."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3', 'system4']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'testCodeRatio': 0.49},  # low (< 0.5)
                'system2': {'maintainability': 3.5, 'testCodeRatio': 0.5},   # medium (>= 0.5, < 1.0)
                'system3': {'maintainability': 3.5, 'testCodeRatio': 0.99},  # medium (>= 0.5, < 1.0)
                'system4': {'maintainability': 3.5, 'testCodeRatio': 1.0},   # high (>= 1.0)
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        distribution = portfolio.test_code_ratio_distribution_percentages
        
        # 1 low, 2 medium, 1 high
        assert distribution['low'] == 25
        assert distribution['medium'] == 50
        assert distribution['high'] == 25


class TestTestCodeRatioChange:
    """Test the test code ratio change tracking in statistics."""
    
    def test_test_code_ratio_change_tracking(self, mocker):
        """Test that test code ratio changes are tracked correctly in statistics."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3', 'system4']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        # System 1: ratio increased from 0.5 to 0.7 (+0.2)
        # System 2: ratio decreased from 0.8 to 0.6 (-0.2)
        # System 3: ratio increased from 0.6 to 0.9 (+0.3) - biggest increase
        # System 4: ratio stable from 0.4 to 0.41 (+0.01, within threshold)
        
        def mock_start_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'testCodeRatio': 0.5, 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'testCodeRatio': 0.8, 'volumeInPersonMonths': 100},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'testCodeRatio': 0.6, 'volumeInPersonMonths': 100},
                'system4': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'testCodeRatio': 0.4, 'volumeInPersonMonths': 100}
            }
            return snapshots[system_name]
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': 0.7, 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': 0.6, 'volumeInPersonMonths': 100},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': 0.9, 'volumeInPersonMonths': 100},
                'system4': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': 0.41, 'volumeInPersonMonths': 100}
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Verify totals
        assert stats['test-code-ratio-change']['total-start'] == 2.3  # 0.5 + 0.8 + 0.6 + 0.4
        assert stats['test-code-ratio-change']['total-end'] == 2.61  # 0.7 + 0.6 + 0.9 + 0.41
        
        # Verify change counts
        assert stats['test-code-ratio-change']['systems-increased'] == 2  # system1, system3
        assert stats['test-code-ratio-change']['systems-decreased'] == 1  # system2
        assert stats['test-code-ratio-change']['systems-stable'] == 1  # system4
        
        # Verify biggest changes
        assert 'system3' in stats['test-code-ratio-change']['biggest-increase']
        assert abs(stats['test-code-ratio-change']['biggest-increase']['system3'] - 0.3) < 0.001
        
        assert 'system2' in stats['test-code-ratio-change']['biggest-decrease']
        assert abs(stats['test-code-ratio-change']['biggest-decrease']['system2'] - (-0.2)) < 0.001
    
    def test_test_code_ratio_change_with_none_values(self, mocker):
        """Test that systems with None test code ratios are excluded from change tracking."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2', 'system3']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        def mock_start_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'testCodeRatio': 0.5, 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'testCodeRatio': None, 'volumeInPersonMonths': 100},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'volumeInPersonMonths': 100}  # missing testCodeRatio
            }
            return snapshots[system_name]
        
        def mock_end_snapshot(system_name):
            snapshots = {
                'system1': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': 0.7, 'volumeInPersonMonths': 100},
                'system2': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': 0.6, 'volumeInPersonMonths': 100},
                'system3': {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': None, 'volumeInPersonMonths': 100}
            }
            return snapshots[system_name]
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Only system1 should be counted (has both start and end ratios)
        assert stats['test-code-ratio-change']['total-start'] == 0.5
        assert stats['test-code-ratio-change']['total-end'] == 0.7
        assert stats['test-code-ratio-change']['systems-increased'] == 1
        assert stats['test-code-ratio-change']['systems-decreased'] == 0
        assert stats['test-code-ratio-change']['systems-stable'] == 0
    
    def test_test_code_ratio_change_no_changes(self, mocker):
        """Test change tracking when there are no changes."""
        
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2']
        
        def mock_get_system_metadata(system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=['2024-01-01', '2024-12-31'])
        
        def mock_start_snapshot(system_name):
            return {'maintainability': 3.5, 'maintainabilityDate': '2024-02-01', 'testCodeRatio': 0.5, 'volumeInPersonMonths': 100}
        
        def mock_end_snapshot(system_name):
            return {'maintainability': 3.5, 'maintainabilityDate': '2024-12-31', 'testCodeRatio': 0.5, 'volumeInPersonMonths': 100}
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(portfolio, 'get_system_metadata', side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'start_snapshot', side_effect=mock_start_snapshot)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        stats = portfolio.statistics
        
        # Both systems stable
        assert stats['test-code-ratio-change']['total-start'] == 1.0
        assert stats['test-code-ratio-change']['total-end'] == 1.0
        assert stats['test-code-ratio-change']['systems-increased'] == 0
        assert stats['test-code-ratio-change']['systems-decreased'] == 0
        assert stats['test-code-ratio-change']['systems-stable'] == 2
        assert stats['test-code-ratio-change']['biggest-increase'] == {}


class TestSecurityCriticalFindingsStatistics:
    """Test the critical findings statistics for security dashboard."""
    
    def test_critical_findings_statistics_with_resolved_and_added(self, mocker):
        """Test statistics calculation with both resolved and added critical findings."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 5, 'existing': 10, 'new': 2},
                                'HIGH': {'resolved': 3, 'existing': 8, 'new': 1}
                            }
                        },
                        {
                            'month': '2025-02-01',
                            'severities': {
                                'CRITICAL': {'resolved': 3, 'existing': 9, 'new': 1},
                                'HIGH': {'resolved': 2, 'existing': 7, 'new': 0}
                            }
                        }
                    ]
                },
                {
                    'system': 'system2',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 2, 'existing': 5, 'new': 4},
                                'HIGH': {'resolved': 1, 'existing': 3, 'new': 2}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_findings_statistics
        
        # Total resolved: 5 + 3 + 2 = 10
        assert stats['resolved'] == 10
        # Total added: 2 + 1 + 4 = 7
        assert stats['added'] == 7
        # Net change: 7 - 10 = -3 (decrease of 3)
        assert stats['net_change'] == -3
    
    def test_critical_findings_statistics_with_only_additions(self, mocker):
        """Test statistics when only new critical findings are added."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 0, 'existing': 5, 'new': 8},
                                'HIGH': {'resolved': 1, 'existing': 3, 'new': 2}
                            }
                        }
                    ]
                },
                {
                    'system': 'system2',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 0, 'existing': 2, 'new': 5},
                                'HIGH': {'resolved': 0, 'existing': 1, 'new': 1}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_findings_statistics
        
        assert stats['resolved'] == 0
        assert stats['added'] == 13  # 8 + 5
        assert stats['net_change'] == 13  # All new findings
    
    def test_critical_findings_statistics_with_only_resolutions(self, mocker):
        """Test statistics when only critical findings are resolved."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 10, 'existing': 0, 'new': 0},
                                'HIGH': {'resolved': 5, 'existing': 2, 'new': 0}
                            }
                        }
                    ]
                },
                {
                    'system': 'system2',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 7, 'existing': 0, 'new': 0}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_findings_statistics
        
        assert stats['resolved'] == 17  # 10 + 7
        assert stats['added'] == 0
        assert stats['net_change'] == -17  # All resolved, net decrease
    
    def test_critical_findings_statistics_ignores_other_severities(self, mocker):
        """Test that only CRITICAL severity findings are counted, not HIGH, MEDIUM, or LOW."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 3, 'existing': 5, 'new': 2},
                                'HIGH': {'resolved': 10, 'existing': 8, 'new': 15},
                                'MEDIUM': {'resolved': 20, 'existing': 10, 'new': 25},
                                'LOW': {'resolved': 5, 'existing': 3, 'new': 8}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_findings_statistics
        
        # Only CRITICAL findings should be counted
        assert stats['resolved'] == 3
        assert stats['added'] == 2
        assert stats['net_change'] == -1
    
    def test_critical_findings_statistics_with_empty_data(self, mocker):
        """Test statistics with no systems or findings."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {'systems': []}
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_findings_statistics
        
        assert stats['resolved'] == 0
        assert stats['added'] == 0
        assert stats['net_change'] == 0
    
    def test_critical_findings_statistics_with_missing_critical_severity(self, mocker):
        """Test statistics when CRITICAL severity data is missing from some months."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'HIGH': {'resolved': 5, 'existing': 3, 'new': 2}
                                # CRITICAL is missing
                            }
                        },
                        {
                            'month': '2025-02-01',
                            'severities': {
                                'CRITICAL': {'resolved': 4, 'existing': 2, 'new': 3},
                                'HIGH': {'resolved': 1, 'existing': 1, 'new': 1}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_findings_statistics
        
        # Only the second month's CRITICAL data should be counted
        assert stats['resolved'] == 4
        assert stats['added'] == 3
        assert stats['net_change'] == -1


class TestSecurityHighMediumLowFindingsStatistics:
    """Test the high, medium, and low severity findings statistics."""
    
    def test_high_findings_statistics(self, mocker):
        """Test high severity findings statistics calculation."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'HIGH': {'resolved': 10, 'existing': 5, 'new': 3},
                                'MEDIUM': {'resolved': 2, 'existing': 1, 'new': 1}
                            }
                        },
                        {
                            'month': '2025-02-01',
                            'severities': {
                                'HIGH': {'resolved': 5, 'existing': 3, 'new': 7},
                                'MEDIUM': {'resolved': 1, 'existing': 0, 'new': 0}
                            }
                        }
                    ]
                },
                {
                    'system': 'system2',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'HIGH': {'resolved': 8, 'existing': 4, 'new': 2}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.high_findings_statistics
        
        # Total resolved: 10 + 5 + 8 = 23
        assert stats['resolved'] == 23
        # Total added: 3 + 7 + 2 = 12
        assert stats['added'] == 12
        # Net change: 12 - 23 = -11 (decrease)
        assert stats['net_change'] == -11
    
    def test_medium_findings_statistics(self, mocker):
        """Test medium severity findings statistics calculation."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'MEDIUM': {'resolved': 3, 'existing': 8, 'new': 5},
                                'LOW': {'resolved': 1, 'existing': 2, 'new': 0}
                            }
                        },
                        {
                            'month': '2025-02-01',
                            'severities': {
                                'MEDIUM': {'resolved': 2, 'existing': 11, 'new': 4}
                            }
                        }
                    ]
                },
                {
                    'system': 'system2',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'MEDIUM': {'resolved': 1, 'existing': 5, 'new': 6}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.medium_findings_statistics
        
        # Total resolved: 3 + 2 + 1 = 6
        assert stats['resolved'] == 6
        # Total added: 5 + 4 + 6 = 15
        assert stats['added'] == 15
        # Net change: 15 - 6 = 9 (increase)
        assert stats['net_change'] == 9
    
    def test_low_findings_statistics(self, mocker):
        """Test low severity findings statistics calculation."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'LOW': {'resolved': 20, 'existing': 15, 'new': 10}
                            }
                        },
                        {
                            'month': '2025-02-01',
                            'severities': {
                                'LOW': {'resolved': 15, 'existing': 10, 'new': 5}
                            }
                        }
                    ]
                },
                {
                    'system': 'system2',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'LOW': {'resolved': 12, 'existing': 8, 'new': 3}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.low_findings_statistics
        
        # Total resolved: 20 + 15 + 12 = 47
        assert stats['resolved'] == 47
        # Total added: 10 + 5 + 3 = 18
        assert stats['added'] == 18
        # Net change: 18 - 47 = -29 (decrease)
        assert stats['net_change'] == -29
    
    def test_all_severities_calculated_efficiently(self, mocker):
        """Test that all severity statistics are calculated from the same cached data."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 1, 'existing': 0, 'new': 2},
                                'HIGH': {'resolved': 3, 'existing': 1, 'new': 4},
                                'MEDIUM': {'resolved': 5, 'existing': 2, 'new': 6},
                                'LOW': {'resolved': 7, 'existing': 3, 'new': 8}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        # Access all statistics
        critical = portfolio.critical_findings_statistics
        high = portfolio.high_findings_statistics
        medium = portfolio.medium_findings_statistics
        low = portfolio.low_findings_statistics
        
        # Verify each severity has correct values
        assert critical == {'resolved': 1, 'added': 2, 'net_change': 1}
        assert high == {'resolved': 3, 'added': 4, 'net_change': 1}
        assert medium == {'resolved': 5, 'added': 6, 'net_change': 1}
        assert low == {'resolved': 7, 'added': 8, 'net_change': 1}
        
        # Verify that _all_findings_statistics is the same object (cached)
        assert portfolio._all_findings_statistics['CRITICAL'] is critical
        assert portfolio._all_findings_statistics['HIGH'] is high
        assert portfolio._all_findings_statistics['MEDIUM'] is medium
        assert portfolio._all_findings_statistics['LOW'] is low
    
    def test_missing_severity_data_returns_zero(self, mocker):
        """Test that missing severity data returns zero values instead of errors."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {'resolved': 5, 'existing': 2, 'new': 3}
                                # HIGH, MEDIUM, LOW are missing
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        # Missing severities should return all zeros
        assert portfolio.high_findings_statistics == {'resolved': 0, 'added': 0, 'net_change': 0}
        assert portfolio.medium_findings_statistics == {'resolved': 0, 'added': 0, 'net_change': 0}
        assert portfolio.low_findings_statistics == {'resolved': 0, 'added': 0, 'net_change': 0}
        
        # CRITICAL should still have data
        assert portfolio.critical_findings_statistics == {'resolved': 5, 'added': 3, 'net_change': -2}
    
    def test_empty_systems_returns_zero(self, mocker):
        """Test that empty systems list returns zero values."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {'systems': []}
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        # All severities should return zeros
        assert portfolio.critical_findings_statistics == {'resolved': 0, 'added': 0, 'net_change': 0}
        assert portfolio.high_findings_statistics == {'resolved': 0, 'added': 0, 'net_change': 0}
        assert portfolio.medium_findings_statistics == {'resolved': 0, 'added': 0, 'net_change': 0}
        assert portfolio.low_findings_statistics == {'resolved': 0, 'added': 0, 'net_change': 0}
    
    def test_findings_filtered_by_period(self, mocker):
        """Test that only findings within the specified period are counted."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2024-12-01',  # Before period
                            'severities': {
                                'CRITICAL': {'resolved': 100, 'existing': 50, 'new': 100}
                            }
                        },
                        {
                            'month': '2025-01-01',  # Start of period
                            'severities': {
                                'CRITICAL': {'resolved': 5, 'existing': 10, 'new': 3}
                            }
                        },
                        {
                            'month': '2025-06-01',  # Middle of period
                            'severities': {
                                'CRITICAL': {'resolved': 2, 'existing': 11, 'new': 1}
                            }
                        },
                        {
                            'month': '2025-12-31',  # End of period
                            'severities': {
                                'CRITICAL': {'resolved': 3, 'existing': 9, 'new': 2}
                            }
                        },
                        {
                            'month': '2026-01-01',  # After period
                            'severities': {
                                'CRITICAL': {'resolved': 200, 'existing': 100, 'new': 200}
                            }
                        }
                    ]
                }
            ]
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_findings_statistics
        
        # Only data from 2025-01-01 to 2025-12-31 should be counted
        # Resolved: 5 + 2 + 3 = 10 (excluding 100 from before and 200 from after)
        assert stats['resolved'] == 10
        # Added: 3 + 1 + 2 = 6 (excluding 100 from before and 200 from after)
        assert stats['added'] == 6
        # Net change: 6 - 10 = -4
        assert stats['net_change'] == -4
    
    def test_findings_with_single_month_period(self, mocker):
        """Test that findings are counted when period is within a single month (e.g., 2025-01-15 to 2025-01-31)."""
        
        portfolio = SecurityDashboardFindingsPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'findingRatio': [
                        {
                            'month': '2024-12-01',  # Different month, should be excluded
                            'severities': {
                                'CRITICAL': {'resolved': 100, 'existing': 50, 'new': 100}
                            }
                        },
                        {
                            'month': '2025-01-01',  # Same month as period, should be included
                            'severities': {
                                'CRITICAL': {'resolved': 5, 'existing': 10, 'new': 3},
                                'HIGH': {'resolved': 10, 'existing': 5, 'new': 8}
                            }
                        },
                        {
                            'month': '2025-02-01',  # Different month, should be excluded
                            'severities': {
                                'CRITICAL': {'resolved': 200, 'existing': 100, 'new': 200}
                            }
                        }
                    ]
                }
            ]
        }
        
        # Period is within January 2025
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-15', '2025-01-31'))
        
        stats = portfolio.critical_findings_statistics
        high_stats = portfolio.high_findings_statistics
        
        # Should include data from 2025-01-01 (same year-month as period)
        assert stats['resolved'] == 5
        assert stats['added'] == 3
        assert stats['net_change'] == -2
        
        assert high_stats['resolved'] == 10
        assert high_stats['added'] == 8
        assert high_stats['net_change'] == -2


class TestSecurityCriticalResolutionTimes:
    """Test the critical findings resolution time statistics."""
    
    def test_critical_resolution_statistics_basic(self, mocker):
        """Test basic resolution time statistics calculation."""
        
        portfolio = SecurityDashboardResolutionTimesPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'resolutionTimes': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 10,  # Within 7 days
                                    'lowRisk': 5,  # 8-14 days
                                    'mediumRisk': 3,  # 15-30 days
                                    'highRisk': 2  # 30+ days
                                }
                            }
                        },
                        {
                            'month': '2025-02-01',
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 8,
                                    'lowRisk': 4,
                                    'mediumRisk': 2,
                                    'highRisk': 1
                                }
                            }
                        }
                    ]
                },
                {
                    'system': 'system2',
                    'resolutionTimes': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 12,
                                    'lowRisk': 3,
                                    'mediumRisk': 1,
                                    'highRisk': 0
                                }
                            }
                        }
                    ]
                }
            ],
            'legend': {
                'CRITICAL': {
                    'noRisk': 'at most 7 days',
                    'lowRisk': 'between 7 and 14 days',
                    'mediumRisk': 'between 14 and 30 days',
                    'highRisk': 'at least 30 days'
                }
            }
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_resolution_statistics
        
        # Total counts across all systems and months
        assert stats['no_risk'] == 30  # 10 + 8 + 12
        assert stats['low_risk'] == 12  # 5 + 4 + 3
        assert stats['medium_risk'] == 6  # 3 + 2 + 1
        assert stats['high_risk'] == 3  # 2 + 1 + 0
        
        # Most common bucket should be noRisk with 30 findings
        assert stats['most_days'] == 'at most 7 days'
        assert stats['most_findings'] == 30
    
    def test_critical_resolution_statistics_most_is_high_risk(self, mocker):
        """Test when most findings are in the high risk category."""
        
        portfolio = SecurityDashboardResolutionTimesPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'resolutionTimes': [
                        {
                            'month': '2025-01-01',
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 2,
                                    'lowRisk': 3,
                                    'mediumRisk': 5,
                                    'highRisk': 50  # Most in high risk
                                }
                            }
                        }
                    ]
                }
            ],
            'legend': {
                'CRITICAL': {
                    'noRisk': 'at most 7 days',
                    'lowRisk': 'between 7 and 14 days',
                    'mediumRisk': 'between 14 and 30 days',
                    'highRisk': 'at least 30 days'
                }
            }
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_resolution_statistics
        
        assert stats['high_risk'] == 50
        assert stats['most_days'] == 'at least 30 days'
        assert stats['most_findings'] == 50
    
    def test_critical_resolution_statistics_filtered_by_period(self, mocker):
        """Test that resolution times are filtered by the reporting period."""
        
        portfolio = SecurityDashboardResolutionTimesPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'resolutionTimes': [
                        {
                            'month': '2024-12-01',  # Before period
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 100,
                                    'lowRisk': 100,
                                    'mediumRisk': 100,
                                    'highRisk': 100
                                }
                            }
                        },
                        {
                            'month': '2025-01-01',  # Within period
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 5,
                                    'lowRisk': 3,
                                    'mediumRisk': 2,
                                    'highRisk': 1
                                }
                            }
                        },
                        {
                            'month': '2026-01-01',  # After period
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 200,
                                    'lowRisk': 200,
                                    'mediumRisk': 200,
                                    'highRisk': 200
                                }
                            }
                        }
                    ]
                }
            ],
            'legend': {
                'CRITICAL': {
                    'noRisk': 'at most 7 days',
                    'lowRisk': 'between 7 and 14 days',
                    'mediumRisk': 'between 14 and 30 days',
                    'highRisk': 'at least 30 days'
                }
            }
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_resolution_statistics
        
        # Should only include data from 2025-01-01
        assert stats['no_risk'] == 5
        assert stats['low_risk'] == 3
        assert stats['medium_risk'] == 2
        assert stats['high_risk'] == 1
    
    def test_critical_resolution_statistics_empty_data(self, mocker):
        """Test with empty systems data."""
        
        portfolio = SecurityDashboardResolutionTimesPortfolioData()
        
        mock_data = {
            'systems': [],
            'legend': {
                'CRITICAL': {
                    'noRisk': 'at most 7 days',
                    'lowRisk': 'between 7 and 14 days',
                    'mediumRisk': 'between 14 and 30 days',
                    'highRisk': 'at least 30 days'
                }
            }
        }
        
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-01', '2025-12-31'))
        
        stats = portfolio.critical_resolution_statistics
        
        assert stats['no_risk'] == 0
        assert stats['low_risk'] == 0
        assert stats['medium_risk'] == 0
        assert stats['high_risk'] == 0
        assert stats['most_days'] == 'at most 7 days'  # From legend
        assert stats['most_findings'] == 0
    
    def test_critical_resolution_statistics_with_single_month_period(self, mocker):
        """Test resolution times with period within a single month."""
        
        portfolio = SecurityDashboardResolutionTimesPortfolioData()
        
        mock_data = {
            'systems': [
                {
                    'system': 'system1',
                    'resolutionTimes': [
                        {
                            'month': '2024-12-01',  # Different month
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 100,
                                    'lowRisk': 100,
                                    'mediumRisk': 100,
                                    'highRisk': 100
                                }
                            }
                        },
                        {
                            'month': '2025-01-01',  # Same month as period
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 15,
                                    'lowRisk': 8,
                                    'mediumRisk': 5,
                                    'highRisk': 3
                                }
                            }
                        },
                        {
                            'month': '2025-02-01',  # Different month
                            'severities': {
                                'CRITICAL': {
                                    'noRisk': 200,
                                    'lowRisk': 200,
                                    'mediumRisk': 200,
                                    'highRisk': 200
                                }
                            }
                        }
                    ]
                }
            ],
            'legend': {
                'CRITICAL': {
                    'noRisk': 'at most 7 days',
                    'lowRisk': 'between 7 and 14 days',
                    'mediumRisk': 'between 14 and 30 days',
                    'highRisk': 'at least 30 days'
                }
            }
        }
        
        # Period is within January 2025
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        mocker.patch.object(type(portfolio), 'period', new_callable=mocker.PropertyMock, return_value=('2025-01-15', '2025-01-31'))
        
        stats = portfolio.critical_resolution_statistics
        
        # Should include data from 2025-01-01 (same year-month)
        assert stats['no_risk'] == 15
        assert stats['low_risk'] == 8
        assert stats['medium_risk'] == 5
        assert stats['high_risk'] == 3
        assert stats['most_days'] == 'at most 7 days'
        assert stats['most_findings'] == 15

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

from report_generator.generator.domain.portfolio.architecture_portfolio import (
    ArchitecturePortfolioData
)
from report_generator.generator.domain.portfolio.maintainability_portfolio import (
    MaintainabilityPortfolioData
)
from report_generator.generator.domain.portfolio.osh_portfolio import OSHRatingsPortfolioData
from report_generator.generator.domain.portfolio.security_portfolio import SecurityRatingsPortfolioData


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
        assert distribution['above_market'] == pytest.approx(50.0)
        assert distribution['market_average'] == pytest.approx(25.0)
        assert distribution['below_market'] == pytest.approx(25.0)
    
    def test_osh_rating_distribution_with_no_systems(self, mocker):
        """Test get_rating_distribution_percentages handles empty systems list."""
        portfolio = OSHRatingsPortfolioData()
        mocker.patch.object(type(portfolio), 'raw_data', new_callable=mocker.PropertyMock, return_value={'systems': []})
        
        distribution = portfolio.get_rating_distribution_percentages
        assert distribution['above_market'] == pytest.approx(0.0)
        assert distribution['market_average'] == pytest.approx(0.0)
        assert distribution['below_market'] == pytest.approx(0.0)
    
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
        assert distribution['above_market'] == pytest.approx(100.0)
        assert distribution['market_average'] == pytest.approx(0.0)
        assert distribution['below_market'] == pytest.approx(0.0)
    
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
        assert distribution['above_market'] == pytest.approx(50.0)
        assert distribution['market_average'] == pytest.approx(25.0)
        assert distribution['below_market'] == pytest.approx(25.0)
    
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
        assert distribution['above_market'] == pytest.approx(50.0)
        assert distribution['market_average'] == pytest.approx(50.0)
        assert distribution['below_market'] == pytest.approx(0.0)
    
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
        
        # Mock utils._get_volume to return volume data
        def mock_get_volume(system_name):
            volumes = {'system1': 100, 'system2': 200, 'system3': 100}
            return volumes.get(system_name, 0)

        mocker.patch('report_generator.generator.domain.portfolio.portfolio_utils._get_volume',
                     side_effect=mock_get_volume)
        
        # Weighted average = (4.0*100 + 3.0*200 + 2.0*100) / (100+200+100) = 1200/400 = 3.0
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == pytest.approx(3.0)
    
    def test_security_weighted_average_with_zero_volume(self, mocker):
        """Test weighted average handles systems with zero volume."""
        
        portfolio = SecurityRatingsPortfolioData()
        
        mock_data = [
            {'systemName': 'system1', 'rating': 4.0},
            {'systemName': 'system2', 'rating': 5.0},  # Should be excluded due to zero volume
        ]
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        # Mock utils._get_volume to return volume data
        def mock_get_volume(system_name):
            volumes = {'system1': 100, 'system2': 0}
            return volumes.get(system_name, 0)

        mocker.patch('report_generator.generator.domain.portfolio.portfolio_utils._get_volume',
                     side_effect=mock_get_volume)
        
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == pytest.approx(4.0)
    
    def test_security_weighted_average_empty_data(self, mocker):
        """Test weighted average returns 0 for empty data."""
        portfolio = SecurityRatingsPortfolioData()
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=[])
        
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == pytest.approx(0.0)
    
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
        
        # Mock utils._get_volume to return volume data
        def mock_get_volume(system_name):
            volumes = {'system1': 10000, 'system2': 20000}
            return volumes.get(system_name, 0)

        mocker.patch('report_generator.generator.domain.portfolio.portfolio_utils._get_volume',
                     side_effect=mock_get_volume)
        
        # Weighted average = (4.0*10000 + 3.0*20000) / (10000+20000) = 100000/30000 = 3.333...
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == pytest.approx(3.333333, rel=1e-5)
    
    def test_maintainability_weighted_average_rating(self, mocker):
        """Test weighted average rating calculation for maintainability portfolio."""
        portfolio = MaintainabilityPortfolioData()
        
        mock_system_names = ['system1', 'system2']
        
        mock_metadata = [
            {'systemName': 'system1', 'active': True, 'isDevelopmentOnly': False},
            {'systemName': 'system2', 'active': True, 'isDevelopmentOnly': False}
        ]
        
        def mock_get_system_metadata(portfolio_metadata, system_name):
            return {'active': True, 'isDevelopmentOnly': False}
        
        def mock_end_snapshot(system_name):
            if system_name == 'system1':
                return {'maintainability': 4.0, 'volumeInPersonMonths': 50}
            else:
                return {'maintainability': 3.0, 'volumeInPersonMonths': 100}
        
        mocker.patch.object(type(portfolio), 'system_names', new_callable=mocker.PropertyMock, return_value=mock_system_names)
        mocker.patch.object(type(portfolio), 'metadata', new_callable=mocker.PropertyMock, return_value=mock_metadata)
        mocker.patch('report_generator.generator.domain.portfolio.portfolio_utils.get_system_metadata',
                     side_effect=mock_get_system_metadata)
        mocker.patch.object(portfolio, 'end_snapshot', side_effect=mock_end_snapshot)
        
        # Weighted average = (4.0*50 + 3.0*100) / (50+100) = 500/150 = 3.333...
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == pytest.approx(3.333333, rel=1e-5)
    
    def test_architecture_weighted_average_rating(self, mocker):
        """Test weighted average rating calculation for architecture portfolio."""
        portfolio = ArchitecturePortfolioData()
        
        mock_data = [
            {'system': 'system1', 'ratings': {'architecture': 4.0}},
            {'system': 'system2', 'ratings': {'architecture': 2.0}},
        ]
        mocker.patch.object(type(portfolio), 'data', new_callable=mocker.PropertyMock, return_value=mock_data)
        
        # Mock utils._get_volume to return volume data
        def mock_get_volume(system_name):
            volumes = {'system1': 80, 'system2': 40}
            return volumes.get(system_name, 0)

        mocker.patch('report_generator.generator.domain.portfolio.portfolio_utils._get_volume',
                     side_effect=mock_get_volume)
        
        # Weighted average = (4.0*80 + 2.0*40) / (80+40) = 400/120 = 3.333...
        avg_rating = portfolio.weighted_average_rating
        assert avg_rating == pytest.approx(3.333333, rel=1e-5)



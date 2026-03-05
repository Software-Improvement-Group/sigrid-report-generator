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

from report_generator.generator.context import portfolio_filters
from report_generator.generator.domain.portfolio.architecture_portfolio import (
    architecture_portfolio_data
)


class TestArchitecturePortfolioData:
    """Test cases for ArchitecturePortfolioData model."""

    def setup_method(self):
        """Reset portfolio context before each test."""
        portfolio_filters._team = None
        portfolio_filters._division = None

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        portfolio_filters._team = None
        portfolio_filters._division = None
        
        cache_attrs = ['data', 'metadata', 'period', 'system_names']
        for attr in cache_attrs:
            architecture_portfolio_data.__dict__.pop(attr, None)

    @patch('report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api')
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = [
            {'system': 'system1', 'architectureQuality': 4.5},
            {'system': 'system2', 'architectureQuality': 3.8}
        ]
        mock_sigrid_api.get_portfolio_architecture_findings.return_value = mock_data
        
        architecture_portfolio_data.__dict__.pop('data', None)
        
        system = architecture_portfolio_data.get_system('system1')
        
        assert system is not None
        assert system['system'] == 'system1'
        assert abs(system['architectureQuality'] - 4.5) < 0.01

    @patch('report_generator.generator.domain.portfolio.architecture_portfolio.sigrid_api')
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
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



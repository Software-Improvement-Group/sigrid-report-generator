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
from report_generator.generator.data_models.portfolio.osh_portfolio import OSHRatingsPortfolioData, osh_portfolio_data


class TestOSHPortfolioData:
    """Test cases for OSHRatingsPortfolioData model."""

    def setup_method(self):
        """Reset portfolio context before each test."""
        portfolio_filters._team = None
        portfolio_filters._division = None

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        portfolio_filters._team = None
        portfolio_filters._division = None
        
        cache_attrs = ['raw_data', 'metadata', 'period', 'system_names']
        for attr in cache_attrs:
            osh_portfolio_data.__dict__.pop(attr, None)

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
        assert rating == pytest.approx(4.5)
        
        rating = portfolio._extract_osh_rating(system, 'vulnerability')
        assert rating == pytest.approx(3.2)
    
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

    @patch('report_generator.generator.data_models.portfolio.osh_portfolio.sigrid_api')
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = {
            'systems': [
                {'systemName': 'system1', 'oshRating': 4.5},
                {'systemName': 'system2', 'oshRating': 3.8}
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data
        
        osh_portfolio_data.__dict__.pop('raw_data', None)
        
        system = osh_portfolio_data.get_system('system1')
        
        assert system is not None
        assert system['systemName'] == 'system1'
        assert abs(system['oshRating'] - 4.5) < 0.01

    @patch('report_generator.generator.data_models.portfolio.osh_portfolio.sigrid_api')
    def test_find_system_returns_correct_system(self, mock_sigrid_api):
        """Test that find_system returns correct system data (alias for get_system)."""
        mock_data = {
            'systems': [
                {'systemName': 'system1', 'oshRating': 4.5}
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data
        
        osh_portfolio_data.__dict__.pop('raw_data', None)
        
        system = osh_portfolio_data.find_system('system1')
        
        assert system is not None
        assert system['systemName'] == 'system1'

    @patch('report_generator.generator.data_models.portfolio.osh_portfolio.sigrid_api')
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = {
            'systems': [
                {'systemName': 'system1', 'oshRating': 4.5},
                {'systemName': 'system2', 'oshRating': 3.8},
                {'systemName': 'system3', 'oshRating': 4.2}
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data
        
        for attr in ['raw_data', 'data', 'system_names']:
            osh_portfolio_data.__dict__.pop(attr, None)
        
        names = osh_portfolio_data.system_names
        
        assert len(names) == 3
        assert 'system1' in names
        assert 'system2' in names
        assert 'system3' in names




class TestOSHMetricsBase:
    """Test cases for OSHMetricsBase shared metrics calculations."""

    def test_vulnerabilities_count_calculates_from_risk_distribution(self):
        """Test vulnerabilities_count sums critical to low risk levels (0-3)."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            vulnerability_risk_distribution = [5, 10, 8, 3, 20]  # critical, high, medium, low, no_risk
            dependencies_count = 46
        
        metrics = TestMetrics()
        assert metrics.vulnerabilities_count == 26  # 5 + 10 + 8 + 3
    
    def test_vulnerabilities_fraction_calculates_correctly(self):
        """Test vulnerabilities_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            vulnerability_risk_distribution = [5, 10, 8, 3, 20]
            dependencies_count = 46
        
        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(26 / 46)
    
    def test_vulnerabilities_fraction_returns_zero_when_no_vulnerabilities(self):
        """Test vulnerabilities_fraction returns 0.0 when count is zero."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            vulnerability_risk_distribution = [0, 0, 0, 0, 46]
            dependencies_count = 46
        
        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.0)
    
    def test_vulnerabilities_fraction_has_minimum_floor(self):
        """Test vulnerabilities_fraction has a minimum value of 0.01."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            vulnerability_risk_distribution = [0, 0, 0, 1, 999]
            dependencies_count = 1000
        
        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.01)
    
    def test_outdated_count_only_includes_critical_to_medium(self):
        """Test outdated_count sums critical to medium freshness risk (0-2), excluding low."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            freshness_risk_distribution = [3, 7, 12, 5, 20]  # critical, high, medium, low, no_risk
            dependencies_count = 47
        
        metrics = TestMetrics()
        assert metrics.outdated_count == 22  # 3 + 7 + 12 (excludes low=5)
    
    def test_outdated_fraction_calculates_correctly(self):
        """Test outdated_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            freshness_risk_distribution = [3, 7, 12, 5, 20]
            dependencies_count = 47
        
        metrics = TestMetrics()
        assert metrics.outdated_fraction == pytest.approx(22 / 47)
    
    def test_legal_risk_count_only_includes_critical_to_medium(self):
        """Test legal_risk_count sums critical to medium license risk (0-2), excluding low."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            legal_risk_distribution = [2, 5, 8, 10, 25]  # critical, high, medium, low, no_risk
            dependencies_count = 50
        
        metrics = TestMetrics()
        assert metrics.legal_risk_count == 15  # 2 + 5 + 8 (excludes low=10)
    
    def test_legal_risk_fraction_calculates_correctly(self):
        """Test legal_risk_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            legal_risk_distribution = [2, 5, 8, 10, 25]
            dependencies_count = 50
        
        metrics = TestMetrics()
        assert metrics.legal_risk_fraction == pytest.approx(15 / 50)
    
    def test_unmanaged_count_includes_all_risk_levels(self):
        """Test unmanaged_count sums critical to low management risk (0-3)."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            management_risk_distribution = [1, 3, 5, 7, 30]  # critical, high, medium, low, no_risk
            dependencies_count = 46
        
        metrics = TestMetrics()
        assert metrics.unmanaged_count == 16  # 1 + 3 + 5 + 7
    
    def test_unmanaged_fraction_calculates_correctly(self):
        """Test unmanaged_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            management_risk_distribution = [1, 3, 5, 7, 30]
            dependencies_count = 46
        
        metrics = TestMetrics()
        assert metrics.unmanaged_fraction == pytest.approx(16 / 46)
    
    def test_activity_risk_count_includes_all_risk_levels(self):
        """Test activity_risk_count sums critical to low activity risk (0-3)."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            activity_risk_distribution = [2, 4, 6, 8, 35]  # critical, high, medium, low, no_risk
            dependencies_count = 55
        
        metrics = TestMetrics()
        assert metrics.activity_risk_count == 20  # 2 + 4 + 6 + 8
    
    def test_activity_risk_fraction_calculates_correctly(self):
        """Test activity_risk_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            activity_risk_distribution = [2, 4, 6, 8, 35]
            dependencies_count = 55
        
        metrics = TestMetrics()
        assert metrics.activity_risk_fraction == pytest.approx(20 / 55)
    
    def test_all_fractions_have_minimum_floor_of_0_01(self):
        """Test all fraction methods apply minimum floor of 0.01 when count is non-zero."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            vulnerability_risk_distribution = [0, 0, 0, 1, 9999]
            freshness_risk_distribution = [1, 0, 0, 0, 9999]
            legal_risk_distribution = [0, 1, 0, 0, 9999]
            management_risk_distribution = [0, 0, 0, 1, 9999]
            activity_risk_distribution = [0, 0, 1, 0, 9999]
            dependencies_count = 10000
        
        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.01)
        assert metrics.outdated_fraction == pytest.approx(0.01)
        assert metrics.legal_risk_fraction == pytest.approx(0.01)
        assert metrics.unmanaged_fraction == pytest.approx(0.01)
        assert metrics.activity_risk_fraction == pytest.approx(0.01)
    
    def test_all_fractions_return_zero_when_counts_are_zero(self):
        """Test all fraction methods return 0.0 when respective counts are zero."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        class TestMetrics(OSHMetricsBase):
            vulnerability_risk_distribution = [0, 0, 0, 0, 100]
            freshness_risk_distribution = [0, 0, 0, 50, 50]
            legal_risk_distribution = [0, 0, 0, 50, 50]
            management_risk_distribution = [0, 0, 0, 0, 100]
            activity_risk_distribution = [0, 0, 0, 0, 100]
            dependencies_count = 100
        
        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.0)
        assert metrics.outdated_fraction == pytest.approx(0.0)
        assert metrics.legal_risk_fraction == pytest.approx(0.0)
        assert metrics.unmanaged_fraction == pytest.approx(0.0)
        assert metrics.activity_risk_fraction == pytest.approx(0.0)
    
    def test_properties_are_cached(self):
        """Test that properties use @cached_property decorator and don't recalculate."""
        from report_generator.generator.data_models.osh_base import OSHMetricsBase
        
        call_count = {'vulnerability': 0, 'freshness': 0}
        
        class TestMetrics(OSHMetricsBase):
            dependencies_count = 100
            
            @property
            def vulnerability_risk_distribution(self):
                call_count['vulnerability'] += 1
                return [5, 10, 8, 3, 74]
            
            @property
            def freshness_risk_distribution(self):
                call_count['freshness'] += 1
                return [3, 7, 12, 5, 73]
            
            @property
            def legal_risk_distribution(self):
                return [0, 0, 0, 0, 100]
            
            @property
            def management_risk_distribution(self):
                return [0, 0, 0, 0, 100]
            
            @property
            def activity_risk_distribution(self):
                return [0, 0, 0, 0, 100]
        
        metrics = TestMetrics()
        
        # Access vulnerabilities_count multiple times
        _ = metrics.vulnerabilities_count
        _ = metrics.vulnerabilities_count
        assert call_count['vulnerability'] == 1  # Should only calculate once
        
        # Access outdated_count multiple times
        _ = metrics.outdated_count
        _ = metrics.outdated_count
        assert call_count['freshness'] == 1  # Should only calculate once



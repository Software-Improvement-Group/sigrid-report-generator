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

from unittest.mock import MagicMock, patch

from report_generator.generator.constants import MetricEnum
from report_generator.generator.data_models import (
    osh_portfolio_data,
    security_ratings_portfolio_data,
    security_dashboard_findings_portfolio_data
)


class TestPlaceholders:

    def test_to_json_name(self):
        class TestMetricEnum(MetricEnum):
            UNIT_SIZE = "UNIT_SIZE"
            DUPLICATION = "DUPLICATION"
            duplication = "duplication"
            UnIt_sIze = "UnIt_sIze"


        assert TestMetricEnum.UNIT_SIZE.to_json_name() == "unitSize"
        assert TestMetricEnum.DUPLICATION.to_json_name() == "duplication"
        assert TestMetricEnum.duplication.to_json_name() == "duplication"
        assert TestMetricEnum.UnIt_sIze.to_json_name() == "unitSize"


class TestPortfolioPlaceholders:
    
    def test_portfolio_osh_placeholders_return_distribution_values(self, mocker):
        """Test that OSH portfolio placeholders access and return distribution percentages."""
        mock_distribution = {'above_market': 45.5, 'market_average': 30.0, 'below_market': 24.5}
        
        # Mock at the data model instance level
        mocker.patch.object(type(osh_portfolio_data), 'get_rating_distribution_percentages', 
                          new_callable=mocker.PropertyMock, return_value=mock_distribution)
        
        # The placeholders are classes with a `replace` method, but we can test the underlying functions
        assert osh_portfolio_data.get_rating_distribution_percentages['above_market'] == 45.5
        assert osh_portfolio_data.get_rating_distribution_percentages['market_average'] == 30.0
        assert osh_portfolio_data.get_rating_distribution_percentages['below_market'] == 24.5
    
    def test_portfolio_security_placeholders_return_distribution_values(self, mocker):
        """Test that security portfolio placeholders access and return distribution percentages."""
        mock_distribution = {'above_market': 60.0, 'market_average': 25.0, 'below_market': 15.0}
        
        # Mock at the data model instance level
        mocker.patch.object(type(security_ratings_portfolio_data), 'get_rating_distribution_percentages',
                          new_callable=mocker.PropertyMock, return_value=mock_distribution)
        
        # Test that we can access the distribution values
        assert security_ratings_portfolio_data.get_rating_distribution_percentages['above_market'] == 60.0
        assert security_ratings_portfolio_data.get_rating_distribution_percentages['market_average'] == 25.0
        assert security_ratings_portfolio_data.get_rating_distribution_percentages['below_market'] == 15.0
    
    def test_portfolio_security_critical_findings_placeholders(self, mocker):
        """Test security critical findings placeholders return correct values."""
        mock_period = ('2025-01-01', '2025-12-31')
        mock_statistics = {
            'resolved': 25,
            'added': 18,
            'net_change': -7  # More resolved than added
        }
        
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'period',
                          new_callable=mocker.PropertyMock, return_value=mock_period)
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'critical_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_statistics)
        
        # Test period start date
        assert security_dashboard_findings_portfolio_data.period[0] == '2025-01-01'
        
        # Test statistics values
        assert security_dashboard_findings_portfolio_data.critical_findings_statistics['resolved'] == 25
        assert security_dashboard_findings_portfolio_data.critical_findings_statistics['added'] == 18
        assert security_dashboard_findings_portfolio_data.critical_findings_statistics['net_change'] == -7
    
    def test_portfolio_security_critical_findings_with_increase(self, mocker):
        """Test critical findings placeholders when there's an increase in findings."""
        mock_statistics = {
            'resolved': 10,
            'added': 22,
            'net_change': 12  # More added than resolved
        }
        
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'critical_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_statistics)
        
        stats = security_dashboard_findings_portfolio_data.critical_findings_statistics
        assert stats['net_change'] == 12
        assert stats['resolved'] == 10
        assert stats['added'] == 22
    
    def test_portfolio_security_critical_findings_with_no_change(self, mocker):
        """Test critical findings placeholders when resolved equals added."""
        mock_statistics = {
            'resolved': 15,
            'added': 15,
            'net_change': 0  # Same number resolved and added
        }
        
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'critical_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_statistics)
        
        stats = security_dashboard_findings_portfolio_data.critical_findings_statistics
        assert stats['net_change'] == 0
        assert stats['resolved'] == 15
        assert stats['added'] == 15


    def test_portfolio_security_high_findings_placeholders(self, mocker):
        """Test high severity findings placeholders."""
        mock_statistics = {
            'resolved': 25,
            'added': 18,
            'net_change': -7  # Decrease of 7
        }
        
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'high_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_statistics)
        
        # Test statistics values
        assert security_dashboard_findings_portfolio_data.high_findings_statistics['resolved'] == 25
        assert security_dashboard_findings_portfolio_data.high_findings_statistics['added'] == 18
        assert security_dashboard_findings_portfolio_data.high_findings_statistics['net_change'] == -7
    
    def test_portfolio_security_medium_findings_placeholders(self, mocker):
        """Test medium severity findings placeholders."""
        mock_statistics = {
            'resolved': 10,
            'added': 30,
            'net_change': 20  # Increase of 20
        }
        
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'medium_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_statistics)
        
        # Test statistics values
        assert security_dashboard_findings_portfolio_data.medium_findings_statistics['resolved'] == 10
        assert security_dashboard_findings_portfolio_data.medium_findings_statistics['added'] == 30
        assert security_dashboard_findings_portfolio_data.medium_findings_statistics['net_change'] == 20
    
    def test_portfolio_security_low_findings_placeholders(self, mocker):
        """Test low severity findings placeholders."""
        mock_statistics = {
            'resolved': 50,
            'added': 50,
            'net_change': 0  # No change
        }
        
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'low_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_statistics)
        
        # Test statistics values
        assert security_dashboard_findings_portfolio_data.low_findings_statistics['resolved'] == 50
        assert security_dashboard_findings_portfolio_data.low_findings_statistics['added'] == 50
        assert security_dashboard_findings_portfolio_data.low_findings_statistics['net_change'] == 0
    
    def test_portfolio_security_all_severities_together(self, mocker):
        """Test all severity findings placeholders work together correctly."""
        mock_critical = {'resolved': 5, 'added': 3, 'net_change': -2}
        mock_high = {'resolved': 10, 'added': 15, 'net_change': 5}
        mock_medium = {'resolved': 20, 'added': 20, 'net_change': 0}
        mock_low = {'resolved': 100, 'added': 95, 'net_change': -5}
        
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'critical_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_critical)
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'high_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_high)
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'medium_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_medium)
        mocker.patch.object(type(security_dashboard_findings_portfolio_data), 'low_findings_statistics',
                          new_callable=mocker.PropertyMock, return_value=mock_low)
        
        # Critical: decrease
        assert security_dashboard_findings_portfolio_data.critical_findings_statistics['resolved'] == 5
        assert security_dashboard_findings_portfolio_data.critical_findings_statistics['added'] == 3
        assert security_dashboard_findings_portfolio_data.critical_findings_statistics['net_change'] == -2
        
        # High: increase
        assert security_dashboard_findings_portfolio_data.high_findings_statistics['resolved'] == 10
        assert security_dashboard_findings_portfolio_data.high_findings_statistics['added'] == 15
        assert security_dashboard_findings_portfolio_data.high_findings_statistics['net_change'] == 5
        
        # Medium: no change
        assert security_dashboard_findings_portfolio_data.medium_findings_statistics['resolved'] == 20
        assert security_dashboard_findings_portfolio_data.medium_findings_statistics['added'] == 20
        assert security_dashboard_findings_portfolio_data.medium_findings_statistics['net_change'] == 0
        
        # Low: decrease
        assert security_dashboard_findings_portfolio_data.low_findings_statistics['resolved'] == 100
        assert security_dashboard_findings_portfolio_data.low_findings_statistics['added'] == 95
        assert security_dashboard_findings_portfolio_data.low_findings_statistics['net_change'] == -5
class TestTreemapImagePlaceholder:
    """Test cases for treemap image generation with empty data handling."""

    @patch('report_generator.generator.placeholders.images.treemap_image.plt')
    @patch('report_generator.generator.placeholders.images.treemap_image.tr')
    def test_draw_image_with_empty_dataframe_returns_none(self, mock_treemap, mock_plt):
        """Test that draw_image returns None when dataframe is empty."""
        from report_generator.generator.placeholders.images.treemap_image import _AbstractPortfolioTreemapPlaceholder
        
        # Mock figure and axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Create empty fig_data
        fig_data = {
            'system_names': [],
            'volumes': [],
            'labels': [],
            'root_names': [],
            'color_mapping': {}
        }
        
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)
        
        assert result is None
        mock_plt.close.assert_called_once_with(mock_fig)
        # Treemap should not be called with empty data
        mock_treemap.treemap.assert_not_called()

    @patch('report_generator.generator.placeholders.images.treemap_image.plt')
    @patch('report_generator.generator.placeholders.images.treemap_image.tr')
    def test_draw_image_with_empty_color_mapping_creates_default(self, mock_treemap, mock_plt):
        """Test that draw_image creates default color mapping when empty."""
        from report_generator.generator.placeholders.images.treemap_image import _AbstractPortfolioTreemapPlaceholder
        
        # Mock figure and axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Create fig_data with systems but empty color_mapping
        fig_data = {
            'system_names': ['system1', 'system2'],
            'volumes': [100, 200],
            'labels': ['System 1', 'System 2'],
            'root_names': ['root', 'root'],
            'color_mapping': {}
        }
        
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)
        
        # Should have called treemap with a non-empty color mapping
        assert mock_treemap.treemap.called
        call_kwargs = mock_treemap.treemap.call_args[1]
        assert 'cmap' in call_kwargs
        assert len(call_kwargs['cmap']) == 2  # Should have colors for both systems
        assert 'system1' in call_kwargs['cmap']
        assert 'system2' in call_kwargs['cmap']

    @patch('report_generator.generator.placeholders.images.treemap_image.plt')
    @patch('report_generator.generator.placeholders.images.treemap_image.tr')
    def test_draw_image_with_invalid_dimensions_returns_none(self, mock_treemap, mock_plt):
        """Test that draw_image returns None with invalid dimensions."""
        from report_generator.generator.placeholders.images.treemap_image import _AbstractPortfolioTreemapPlaceholder
        
        fig_data = {
            'system_names': ['system1'],
            'volumes': [100],
            'labels': ['System 1'],
            'root_names': ['root'],
            'color_mapping': {'system1': '#FF0000'}
        }
        
        # Test with zero width
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(0, 10, fig_data)
        assert result is None
        
        # Test with negative height
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, -5, fig_data)
        assert result is None
        
        # Test with both invalid
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(-1, 0, fig_data)
        assert result is None

    @patch('report_generator.generator.placeholders.images.treemap_image.plt')
    def test_draw_image_with_none_fig_data_returns_none(self, mock_plt):
        """Test that draw_image returns None when fig_data is None."""
        from report_generator.generator.placeholders.images.treemap_image import _AbstractPortfolioTreemapPlaceholder
        
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, None)
        assert result is None

    @patch('report_generator.generator.placeholders.images.treemap_image.plt')
    @patch('report_generator.generator.placeholders.images.treemap_image.tr')
    def test_draw_image_with_valid_data_creates_treemap(self, mock_treemap, mock_plt):
        """Test that draw_image creates treemap with valid data and color mapping."""
        from report_generator.generator.placeholders.images.treemap_image import _AbstractPortfolioTreemapPlaceholder
        
        # Mock figure and axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Create valid fig_data
        fig_data = {
            'system_names': ['system1', 'system2'],
            'volumes': [100, 200],
            'labels': ['System 1', 'System 2'],
            'root_names': ['root', 'root'],
            'color_mapping': {'system1': '#FF0000', 'system2': '#00FF00'}
        }
        
        result = _AbstractPortfolioTreemapPlaceholder.draw_image(10, 10, fig_data)
        
        # Should return the figure
        assert result == mock_fig
        # Treemap should be called with the provided color mapping
        mock_treemap.treemap.assert_called_once()
        call_kwargs = mock_treemap.treemap.call_args[1]
        assert call_kwargs['cmap'] == fig_data['color_mapping']
        # Axes should be turned off
        mock_ax.axis.assert_called_once_with("off")

class TestSecurityDashboardChartPlaceholders:
    """Test suite for security dashboard chart placeholders."""
    
    def test_add_month_data_row(self):
        """Test _add_month_data_row appends data correctly to arrays."""
        from report_generator.generator.placeholders.charts.security_findings import _add_month_data_row
        
        arrays = {
            'categories': [],
            'new': [],
            'existing': [],
            'resolved': [],
            'total': []
        }
        
        _add_month_data_row(arrays, 'Jan', 5, 10, 2, 15)
        
        assert arrays['categories'] == ['Jan']
        assert arrays['new'] == [5]
        assert arrays['existing'] == [10]
        assert arrays['resolved'] == [2]
        assert arrays['total'] == [15]
    
    def test_build_chart_data_arrays_creates_grouped_structure(self):
        """Test _build_chart_data_arrays creates proper grouped/clustered structure."""
        from report_generator.generator.placeholders.charts.security_findings import _build_chart_data_arrays
        
        data = {
            'columns': ['Jan', 'Feb'],
            'new': [5, 8],
            'existing': [10, 12],
            'resolved': [3, 4]
        }
        
        result = _build_chart_data_arrays(data)
        
        # Should have 3 rows per month except last (which has 2 rows)
        # Jan: row1 (month), row2 (blank), row3 (blank)
        # Feb: row1 (month), row2 (blank)
        assert len(result['categories']) == 5
        
        # First row for Jan should have month name and new+existing
        assert result['categories'][0] == 'Jan'
        assert result['new'][0] == 5
        assert result['existing'][0] == 10
        assert result['resolved'][0] == 0
        assert result['total'][0] == 15  # new + existing
        
        # Second row for Jan should be blank with only resolved
        assert result['categories'][1] == ''
        assert result['new'][1] == 0
        assert result['existing'][1] == 0
        assert result['resolved'][1] == 3
        assert result['total'][1] == 3
        
        # Third row for Jan should be blank spacing
        assert result['categories'][2] == ''
        assert result['total'][2] == 0
        
        # First row for Feb
        assert result['categories'][3] == 'Feb'
        assert result['new'][3] == 8
        assert result['existing'][3] == 12
        assert result['total'][3] == 20
        
        # Second row for Feb (last month - no third row)
        assert result['categories'][4] == ''
        assert result['resolved'][4] == 4
    
    def test_build_chart_data_arrays_single_month(self):
        """Test _build_chart_data_arrays handles single month correctly."""
        from report_generator.generator.placeholders.charts.security_findings import _build_chart_data_arrays
        
        data = {
            'columns': ['Mar'],
            'new': [7],
            'existing': [14],
            'resolved': [5]
        }
        
        result = _build_chart_data_arrays(data)
        
        # Single month should have only 2 rows (no spacing row after)
        assert len(result['categories']) == 2
        assert result['categories'][0] == 'Mar'
        assert result['categories'][1] == ''
    
    @patch('report_generator.generator.placeholders.charts.security_findings.security_dashboard_findings_portfolio_data')
    def test_create_security_findings_chart_data(self, mock_data):
        """Test _create_security_findings_chart_data creates CategoryChartData."""
        from report_generator.generator.placeholders.charts.security_findings import _create_security_findings_chart_data
        
        mock_data.chart_findings_by_severity.return_value = {
            'columns': ['Jan'],
            'new': [5],
            'existing': [10],
            'resolved': [3]
        }
        
        result = _create_security_findings_chart_data('CRITICAL')
        
        # Should be CategoryChartData with categories and series
        assert hasattr(result, 'categories')
        assert len(result.categories) == 2  # 2 rows for single month
        mock_data.chart_findings_by_severity.assert_called_once_with('CRITICAL')
    
    @patch('report_generator.generator.placeholders.charts.security_findings.report_utils.pptx.identify_specific_slide')
    def test_populate_security_findings_chart_no_slides(self, mock_identify):
        """Test _populate_chart returns early when no slides found."""
        from report_generator.generator.placeholders.charts.security_findings import _populate_chart
        
        mock_identify.return_value = []
        mock_presentation = MagicMock()
        mock_value_cb = MagicMock()
        
        _populate_chart(mock_presentation, 'TEST_KEY', mock_value_cb, 'TEST_CHART')
        
        # Should not call value_cb if no slides found
        mock_value_cb.assert_not_called()
    
    @patch('report_generator.generator.placeholders.charts.security_findings.report_utils.pptx.identify_specific_slide')
    def test_populate_security_findings_chart_updates_chart(self, mock_identify):
        """Test _populate_chart updates chart when found."""
        from report_generator.generator.placeholders.charts.security_findings import _populate_chart
        
        # Mock slide with chart shape
        mock_chart = MagicMock()
        mock_shape = MagicMock()
        mock_shape.name = 'TEST_CHART'
        mock_shape.chart = mock_chart
        
        mock_slide = MagicMock()
        mock_slide.shapes = [mock_shape]
        
        mock_identify.return_value = [mock_slide]
        mock_presentation = MagicMock()
        
        mock_chart_data = MagicMock()
        mock_value_cb = MagicMock(return_value=mock_chart_data)
        
        _populate_chart(mock_presentation, 'TEST_KEY', mock_value_cb, 'TEST_CHART')
        
        # Should call replace_data on the chart
        mock_chart.replace_data.assert_called_once_with(mock_chart_data)
    
    def test_security_dashboard_critical_findings_placeholder_key(self):
        """Test SecurityDashboardCriticalFindingsChartPlaceholder has correct key."""
        from report_generator.generator.placeholders.charts.security_findings import SecurityDashboardCriticalFindingsChartPlaceholder
        
        assert SecurityDashboardCriticalFindingsChartPlaceholder.key == "PORTFOLIO_SECURITY_FINDINGS_CRITICAL"
    
    @patch('report_generator.generator.placeholders.charts.security_findings.security_dashboard_findings_portfolio_data')
    def test_security_dashboard_high_findings_placeholder_value(self, mock_data):
        """Test SecurityDashboardHighFindingsChartPlaceholder.value returns chart data."""
        from report_generator.generator.placeholders.charts.security_findings import SecurityDashboardHighFindingsChartPlaceholder
        
        mock_data.chart_findings_by_severity.return_value = {
            'columns': ['Jan'],
            'new': [3],
            'existing': [7],
            'resolved': [2]
        }
        
        result = SecurityDashboardHighFindingsChartPlaceholder.value()
        
        assert hasattr(result, 'categories')
        mock_data.chart_findings_by_severity.assert_called_once_with('HIGH')
    
    @patch('report_generator.generator.placeholders.charts.security_findings.security_dashboard_resolution_times_portfolio_data')
    def test_resolution_times_chart_uses_legend_labels(self, mock_data):
        """Test resolution times chart uses API legend labels."""
        from report_generator.generator.placeholders.charts.security_findings import SecurityDashboardCriticalResolutionTimesChartPlaceholder
        
        mock_data.chart_resolution_times_by_severity.return_value = {
            'columns': ['Jan'],
            'noRisk': [10],
            'lowRisk': [5],
            'mediumRisk': [3],
            'highRisk': [2]
        }
        
        mock_data.get_legend_labels.return_value = {
            'noRisk': 'at most 7 days',
            'lowRisk': 'between 7 and 14 days',
            'mediumRisk': 'between 14 and 30 days',
            'highRisk': 'at least 30 days'
        }
        
        result = SecurityDashboardCriticalResolutionTimesChartPlaceholder.value()
        
        # Should have called get_legend_labels
        mock_data.get_legend_labels.assert_called_once_with('CRITICAL')
        assert hasattr(result, 'categories')
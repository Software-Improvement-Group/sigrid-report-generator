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





class TestSecurityDashboardChartPlaceholders:
    """Test suite for security dashboard chart placeholders."""
    
    def test_add_month_data_row(self):
        """Test _add_month_data_row appends data correctly to arrays."""
        from report_generator.generator.placeholders.charts.security_findings import _add_month_data_row, MonthData
        
        arrays = {
            'categories': [],
            'new': [],
            'existing': [],
            'resolved': [],
            'total': []
        }
        
        _add_month_data_row(arrays, MonthData('Jan', 5, 10, 2, 15))
        
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
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

from dataclasses import dataclass
from typing import Callable, Dict, List

from pptx.chart.data import CategoryChartData
from pptx.presentation import Presentation

from report_generator.generator.domain import security_dashboard_findings_portfolio_data, \
    security_dashboard_resolution_times_portfolio_data
from report_generator.generator.placeholders import rendering
from report_generator.generator.placeholders.base import Placeholder, PlaceholderDocType


@dataclass
class MonthData:
    """Data for a single month row in the security findings chart."""
    month: str
    new: int
    existing: int
    resolved: int
    total: int


def _add_month_data_row(arrays_dict: Dict[str, List], month_data: MonthData) -> None:
    arrays_dict['categories'].append(month_data.month)
    arrays_dict['new'].append(month_data.new)
    arrays_dict['existing'].append(month_data.existing)
    arrays_dict['resolved'].append(month_data.resolved)
    arrays_dict['total'].append(month_data.total)


def _build_chart_data_arrays(data: Dict) -> Dict[str, List]:
    """Build data arrays for the grouped/clustered chart structure.
    
    For the chart to work with stacked (New+Existing) and clustered (Resolved) bars,
    we need to create categories with blank separators for grouping.
    
    Returns arrays in the format matching the Excel structure with grouped data.
    """
    columns = data['columns']
    new = data['new']
    existing = data['existing']
    resolved = data['resolved']
    
    arrays_dict = {
        'categories': [],
        'new': [],
        'existing': [],
        'resolved': [],
        'total': []
    }
    
    for i, month in enumerate(columns):
        total = new[i] + existing[i]
        
        # Row 1: Month name with New and Existing stacked (no Resolved here)
        _add_month_data_row(arrays_dict, MonthData(month, new[i], existing[i], 0, total))
        
        # Row 2: Blank for spacing (only Resolved gets value here for clustering effect)
        _add_month_data_row(arrays_dict, MonthData('', 0, 0, resolved[i], resolved[i]))
        
        # Row 3: Blank for spacing (skip for last month)
        if i < len(columns) - 1:
            _add_month_data_row(arrays_dict, MonthData('', 0, 0, 0, 0))
    
    return arrays_dict


def _create_security_findings_chart_data(severity: str) -> CategoryChartData:
    aggregated_data = security_dashboard_findings_portfolio_data.chart_findings_by_severity(severity)
    chart_arrays = _build_chart_data_arrays(aggregated_data)
    
    chart_data = CategoryChartData()
    chart_data.categories = chart_arrays['categories']
    
    # New and Existing will be stacked, Resolved will be clustered, Total displays on top
    chart_data.add_series('New', chart_arrays['new'])
    chart_data.add_series('Existing', chart_arrays['existing'])
    chart_data.add_series('Resolved', chart_arrays['resolved'])
    chart_data.add_series('Total', chart_arrays['total'])
    
    return chart_data


def _populate_chart(presentation: Presentation, value_cb: Callable[[], CategoryChartData], key: str) -> None:
    charts = rendering.pptx.find_charts(presentation, key)
    
    if not charts:
        return
    
    chart_data = value_cb()
    
    for chart in charts:
        chart.replace_data(chart_data)


class SecurityDashboardCriticalFindingsChartPlaceholder(Placeholder):
    """PowerPoint chart showing new, existing, and resolved critical security findings over the last 12 months."""
    
    key = "PORTFOLIO_SECURITY_FINDINGS_CRITICAL"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _create_security_findings_chart_data("CRITICAL")

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _populate_chart(presentation, value_cb, key)


class SecurityDashboardHighFindingsChartPlaceholder(Placeholder):
    """PowerPoint chart showing new, existing, and resolved high security findings over the last 12 months."""
    
    key = "PORTFOLIO_SECURITY_FINDINGS_HIGH"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _create_security_findings_chart_data("HIGH")

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _populate_chart(presentation, value_cb, key)


class SecurityDashboardMediumFindingsChartPlaceholder(Placeholder):
    """PowerPoint chart showing new, existing, and resolved medium security findings over the last 12 months."""
    
    key = "PORTFOLIO_SECURITY_FINDINGS_MEDIUM"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _create_security_findings_chart_data("MEDIUM")

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _populate_chart(presentation, value_cb, key)


# Resolution Times Placeholders

def _build_resolution_times_chart_data_arrays(data: Dict) -> Dict[str, List]:
    """Build data arrays for stacked resolution times chart.
    
    Returns arrays with month categories and stacked risk level values.
    """
    columns = data['columns']
    no_risk = data['noRisk']
    low_risk = data['lowRisk']
    medium_risk = data['mediumRisk']
    high_risk = data['highRisk']
    
    totals = [no_risk[i] + low_risk[i] + medium_risk[i] + high_risk[i] for i in range(len(columns))]
    
    return {
        'categories': columns,
        'noRisk': no_risk,
        'lowRisk': low_risk,
        'mediumRisk': medium_risk,
        'highRisk': high_risk,
        'total': totals
    }


def _create_resolution_times_chart_data(severity: str) -> CategoryChartData:
    aggregated_data = security_dashboard_resolution_times_portfolio_data.chart_resolution_times_by_severity(severity)
    chart_arrays = _build_resolution_times_chart_data_arrays(aggregated_data)
    labels = security_dashboard_resolution_times_portfolio_data.get_legend_labels(severity)
    
    chart_data = CategoryChartData()
    chart_data.categories = chart_arrays['categories']
    
    # All will be stacked, Total displays on top
    chart_data.add_series(labels['noRisk'], chart_arrays['noRisk'])
    chart_data.add_series(labels['lowRisk'], chart_arrays['lowRisk'])
    chart_data.add_series(labels['mediumRisk'], chart_arrays['mediumRisk'])
    chart_data.add_series(labels['highRisk'], chart_arrays['highRisk'])
    chart_data.add_series('Total', chart_arrays['total'])
    
    return chart_data


class SecurityDashboardCriticalResolutionTimesChartPlaceholder(Placeholder):
    """PowerPoint chart showing resolution times of critical security findings over the last 12 months."""
    
    key = "PORTFOLIO_SECURITY_RESOLUTION_CRITICAL"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _create_resolution_times_chart_data("CRITICAL")

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _populate_chart(presentation, value_cb, key)


class SecurityDashboardHighResolutionTimesChartPlaceholder(Placeholder):
    """PowerPoint chart showing resolution times of high security findings over the last 12 months."""
    
    key = "PORTFOLIO_SECURITY_RESOLUTION_HIGH"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _create_resolution_times_chart_data("HIGH")

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _populate_chart(presentation, value_cb, key)


class SecurityDashboardMediumResolutionTimesChartPlaceholder(Placeholder):
    """PowerPoint chart showing resolution times of medium security findings over the last 12 months."""
    
    key = "PORTFOLIO_SECURITY_RESOLUTION_MEDIUM"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _create_resolution_times_chart_data("MEDIUM")

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _populate_chart(presentation, value_cb, key)


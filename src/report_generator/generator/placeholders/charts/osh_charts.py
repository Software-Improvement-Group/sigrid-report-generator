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

import logging
from typing import Callable, List, Tuple

from pptx.chart.data import ChartData
from pptx.presentation import Presentation

from report_generator.generator import report_utils
from report_generator.generator.data_models import osh_data, osh_portfolio_data
from report_generator.generator.placeholders import Placeholder
from report_generator.generator.placeholders.base import PlaceholderDocType


def _format_osh_chart_data(data, categories: List[Tuple[str, str]]) -> ChartData:
    """
    Format OSH risk distribution data for a chart.
    
    Args:
        data: Risk distributions data dictionary
        categories: List of (display_name, data_key) tuples for each category
                   e.g., [("Vulnerability risk", "vulnerability"), ("Legal risk", "legal")]
    
    Returns:
        ChartData object ready for chart population
    """
    chart_data = ChartData()
    chart_data.categories = [display_name for display_name, _ in categories]
    
    risk_levels = ["Critical risk", "High risk", "Medium risk", "Low risk"]
    for index, risk_level in enumerate(risk_levels):
        values = [data[key][index] for _, key in categories]
        chart_data.add_series(risk_level, values)
    
    return chart_data


def _determine_chart_axis_max(original_data):
    data = original_data.risk_distributions
    max_bar_length = max(sum(data["vulnerability"][0:4]), sum(data["legal"][0:4]), sum(data["freshness"][0:4]),
                         sum(data["activity"][0:4]), sum(data["stability"][0:4]), sum(data["management"][0:4]))

    return max_bar_length * 1.1


def _set_chart_data_and_axis(chart, data, axis_max):
    chart.replace_data(data)
    chart.value_axis.minimum_scale = 0
    chart.value_axis.maximum_scale = axis_max


def _resolve_single_osh_chart(presentation: Presentation, key: str, value_cb, data_source) -> None:
    """Resolver for a single OSH chart."""
    charts = report_utils.pptx.find_charts(presentation, key)
    logging.debug(f"Finds for {key}: {len(charts)}")
    if not charts:
        return
    
    chart_data = value_cb()
    chart_axis_max = _determine_chart_axis_max(data_source)
    for chart in charts:
        _set_chart_data_and_axis(chart, chart_data, chart_axis_max)


VULN_LIC_CATEGORIES = [("Vulnerability risk", "vulnerability"), ("Legal risk", "legal")]
OTHER_RISKS_CATEGORIES = [
    ("Freshness risk", "freshness"),
    ("Stability risk", "stability"),
    ("Management risk", "management"),
    ("Activity risk", "activity")
]


class OSHVulnLegalGraphPlaceholder(Placeholder):
    """OSH system-level vulnerability and legal risk bar chart."""
    key = "OSH_VULN_LEGAL_GRAPH"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _format_osh_chart_data(osh_data.risk_distributions, VULN_LIC_CATEGORIES)

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _resolve_single_osh_chart(presentation, key, value_cb, osh_data)


class OSHOtherRisksGraphPlaceholder(Placeholder):
    """OSH system-level freshness, stability, management, and activity risk bar chart."""
    key = "OSH_OTHER_RISKS_GRAPH"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _format_osh_chart_data(osh_data.risk_distributions, OTHER_RISKS_CATEGORIES)

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _resolve_single_osh_chart(presentation, key, value_cb, osh_data)


class OSHPortfolioVulnLegalGraphPlaceholder(Placeholder):
    """OSH portfolio-level vulnerability and legal risk bar chart."""
    key = "OSH_PORTFOLIO_VULN_LEGAL_GRAPH"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _format_osh_chart_data(osh_portfolio_data.risk_distributions, VULN_LIC_CATEGORIES)

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _resolve_single_osh_chart(presentation, key, value_cb, osh_portfolio_data)


class OSHPortfolioOtherRisksGraphPlaceholder(Placeholder):
    """OSH portfolio-level freshness, stability, management, and activity risk bar chart."""
    key = "OSH_PORTFOLIO_OTHER_RISKS_GRAPH"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls, parameter=None):
        return _format_osh_chart_data(osh_portfolio_data.risk_distributions, OTHER_RISKS_CATEGORIES)

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, value_cb: Callable) -> None:
        _resolve_single_osh_chart(presentation, key, value_cb, osh_portfolio_data)

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

from pptx.chart.data import XyChartData
from pptx.presentation import Presentation

from report_generator.generator.domain import (
    maintainability_portfolio_data,
    reliability_ratings_portfolio_data,
    security_ratings_portfolio_data,
)
from report_generator.generator.placeholders import rendering
from report_generator.generator.placeholders.implementations.base import (
    Placeholder,
    PlaceholderDocType,
)
from report_generator.generator.placeholders.implementations.charts.base import (
    findings_x_axis_max,
)


def _build_scatterplot_data(domain_data, series_name: str) -> tuple[XyChartData, list[str], int]:
    findings_index = {
        entry["systemName"]: entry["findings_above_objective"]
        for entry in domain_data.findings_above_objective
    }
    points, display_names = _collect_points(domain_data, findings_index)
    chart_data = XyChartData()
    series = chart_data.add_series(series_name)
    for x, y in points:
        series.add_data_point(x, y)
    max_findings = findings_x_axis_max(max(findings_index.values(), default=0))
    return chart_data, display_names, max_findings


def _collect_points(domain_data, findings_by_name: dict[str, int]) -> tuple[list, list[str]]:
    points = []
    display_names = []
    for system_name in domain_data.system_names:
        system = domain_data.get_system(system_name)
        if system is None:
            continue
        rating = system.get("rating")
        if rating is None:
            continue
        points.append((findings_by_name.get(system_name, 0), rating))
        display_names.append(
            maintainability_portfolio_data.get_system_display_name(system_name)
        )
    return points, display_names


def _populate_charts(charts, chart_data, display_names: list[str], max_findings: int) -> None:
    for chart in charts:
        chart.replace_data(chart_data)
        chart.category_axis.minimum_scale = 0
        chart.category_axis.maximum_scale = max_findings
        for i, point in enumerate(chart.series[0].points):
            point.data_label.text_frame.text = display_names[i]


def _resolve_scatterplot_pptx(presentation, key: str, domain_data, series_name: str) -> None:
    charts = rendering.pptx.find_charts(presentation, key)
    if not charts:
        return
    chart_data, display_names, max_findings = _build_scatterplot_data(domain_data, series_name)
    _populate_charts(charts, chart_data, display_names, max_findings)


class PortfolioSecurityScatterplotPlaceholder(Placeholder):
    """Portfolio scatterplot: open security findings above objective (X) vs security rating (Y)."""

    key = "PORTFOLIO_SECURITY_SCATTERPLOT"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls):
        chart_data, _, __ = _build_scatterplot_data(security_ratings_portfolio_data, "Security")
        return chart_data

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, _) -> None:
        _resolve_scatterplot_pptx(presentation, key, security_ratings_portfolio_data, "Security")


class PortfolioReliabilityScatterplotPlaceholder(Placeholder):
    """Portfolio scatterplot: open reliability findings above objective (X) vs reliability rating (Y)."""

    key = "PORTFOLIO_RELIABILITY_SCATTERPLOT"
    __doc_type__ = PlaceholderDocType.CHART

    @classmethod
    def value(cls):
        chart_data, _, __ = _build_scatterplot_data(reliability_ratings_portfolio_data, "Reliability")
        return chart_data

    @staticmethod
    def resolve_pptx(presentation: Presentation, key: str, _) -> None:
        _resolve_scatterplot_pptx(presentation, key, reliability_ratings_portfolio_data, "Reliability")

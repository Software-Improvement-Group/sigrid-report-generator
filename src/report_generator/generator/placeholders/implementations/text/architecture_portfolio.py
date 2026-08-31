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

from report_generator.generator.domain import (
    architecture_portfolio_data,
)
from report_generator.generator.placeholders.formatting.formatters import (
    biggest_changes_summary,
    change_short_summary,
    star_rating_round,
)
from report_generator.generator.utils.constants import ArchMetric

from .base import (
    delta_text_placeholder,
    market_average_text_placeholder,
    parameterized_text_placeholder,
    text_placeholder,
)


@text_placeholder()
def portfolio_arch_above_market():
    """Percentage of systems scoring above market average (≥3.5 stars) on architecture quality."""
    distribution = architecture_portfolio_data.rating_distribution_percentages
    return distribution["above_market"]


@text_placeholder()
def portfolio_arch_market_average():
    """Percentage of systems scoring market average (2.5-3.5 stars) on architecture quality."""
    distribution = architecture_portfolio_data.rating_distribution_percentages
    return distribution["market_average"]


@text_placeholder()
def portfolio_arch_below_market():
    """Percentage of systems scoring below market average (<2.5 stars) on architecture quality."""
    distribution = architecture_portfolio_data.rating_distribution_percentages
    return distribution["below_market"]


@text_placeholder()
def portfolio_arch_avg_rating():
    """Volume-weighted average architecture rating across all systems in the portfolio."""
    return star_rating_round(architecture_portfolio_data.weighted_average_rating)


@market_average_text_placeholder()
def portfolio_arch_avg_market_average():
    """Colored indication of whether the portfolio's volume-weighted average architecture quality
    rating is below (red), at (blue) or above (green) market average."""
    return architecture_portfolio_data.weighted_average_rating


@delta_text_placeholder()
def portfolio_arch_average_delta():
    """Signed change in the portfolio's volume-weighted architecture quality average over the period (e.g. +0.01, -0.01, =), colored green up / red down / blue unchanged."""
    return architecture_portfolio_data.average_delta


@text_placeholder()
def portfolio_arch_increased():
    """Percentage of systems that have seen an increase in architecture quality rating."""
    return architecture_portfolio_data.change_distribution_percentages["increased"]


@text_placeholder()
def portfolio_arch_stable():
    """Percentage of systems whose architecture quality rating has remained stable."""
    return architecture_portfolio_data.change_distribution_percentages["stable"]


@text_placeholder()
def portfolio_arch_decreased():
    """Percentage of systems that have seen a decrease in architecture quality rating."""
    return architecture_portfolio_data.change_distribution_percentages["decreased"]


@text_placeholder()
def portfolio_arch_biggest_changes():
    """Descriptive summary of the biggest architecture quality rating changes in the portfolio."""
    return biggest_changes_summary(
        architecture_portfolio_data, "architecture quality rating"
    )


@text_placeholder()
def portfolio_period_arch_change_short_summary():
    """The portfolio architecture quality rating change short summary over the reporting period."""
    return change_short_summary(architecture_portfolio_data, "architecture quality")


@dataclass
class _MetricChange:
    biggest_increase: tuple[str, float] | None
    biggest_decrease: tuple[str, float] | None


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_AVG_RATING_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_avg_rating_param(metric: ArchMetric):
    """Volume-weighted average rating for this metric across all systems in the portfolio."""
    rating = architecture_portfolio_data.weighted_average_rating_for_metric(
        metric.to_json_name()
    )
    return star_rating_round(rating)


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_ABOVE_MARKET_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_above_market_param(metric: ArchMetric):
    """Percentage of systems scoring above market average (≥3.5 stars) for this metric."""
    distribution = (
        architecture_portfolio_data.rating_distribution_percentages_for_metric(
            metric.to_json_name()
        )
    )
    return distribution["above_market"]


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_MARKET_AVERAGE_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_market_average_param(metric: ArchMetric):
    """Percentage of systems scoring market average (2.5-3.5 stars) for this metric."""
    distribution = (
        architecture_portfolio_data.rating_distribution_percentages_for_metric(
            metric.to_json_name()
        )
    )
    return distribution["market_average"]


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_BELOW_MARKET_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_below_market_param(metric: ArchMetric):
    """Percentage of systems scoring below market average (<2.5 stars) for this metric."""
    distribution = (
        architecture_portfolio_data.rating_distribution_percentages_for_metric(
            metric.to_json_name()
        )
    )
    return distribution["below_market"]


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_INCREASED_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_increased_param(metric: ArchMetric):
    """Percentage of systems that have seen an increase in this metric."""
    distribution = (
        architecture_portfolio_data.change_distribution_percentages_for_metric(
            metric.to_json_name()
        )
    )
    return distribution["increased"]


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_STABLE_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_stable_param(metric: ArchMetric):
    """Percentage of systems that have remained stable in this metric."""
    distribution = (
        architecture_portfolio_data.change_distribution_percentages_for_metric(
            metric.to_json_name()
        )
    )
    return distribution["stable"]


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_DECREASED_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_decreased_param(metric: ArchMetric):
    """Percentage of systems that have seen a decrease in this metric."""
    distribution = (
        architecture_portfolio_data.change_distribution_percentages_for_metric(
            metric.to_json_name()
        )
    )
    return distribution["decreased"]


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_ARCH_BIGGEST_CHANGES_{parameter}", parameters=list(ArchMetric)
)
def portfolio_arch_biggest_changes_param(metric: ArchMetric):
    """Descriptive summary of the biggest changes in the portfolio for this metric."""
    metric_key = metric.to_json_name()
    metric_label = metric.value.replace("_", " ").title()
    change = _MetricChange(
        biggest_increase=architecture_portfolio_data.biggest_increase_for_metric(
            metric_key
        ),
        biggest_decrease=architecture_portfolio_data.biggest_decrease_for_metric(
            metric_key
        ),
    )
    return biggest_changes_summary(change, f"{metric_label} rating")

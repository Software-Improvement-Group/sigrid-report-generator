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

from report_generator.generator.domain import (
    architecture_portfolio_data,
)
from report_generator.generator.placeholders.formatting.formatters import (
    star_rating_round,
)

from .base import (
    delta_text_placeholder,
    market_average_text_placeholder,
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
    res = []
    increase = architecture_portfolio_data.biggest_increase
    if increase:
        res.append(
            f"The largest increase in architecture quality rating was experienced by {increase[0]} ({increase[1]} stars)."
        )
    decrease = architecture_portfolio_data.biggest_decrease
    if decrease:
        res.append(
            f"The largest decrease in architecture quality rating was experienced by {decrease[0]} ({decrease[1]} stars)."
        )
    return " ".join(res)


@text_placeholder()
def portfolio_period_arch_change_short_summary():
    """The portfolio architecture quality rating change short summary over the reporting period."""
    start_avg = int(architecture_portfolio_data.start_weighted_average * 10) / 10
    end_avg = int(architecture_portfolio_data.end_weighted_average * 10) / 10
    diff = int((end_avg - start_avg) * 10) / 10
    if abs(diff) < 0.01:
        return f"The portfolio remained stable ({end_avg}) during the measured period"
    return f"The portfolio's architecture quality has {'increased' if start_avg < end_avg else 'decreased'} (with {diff} to {end_avg}) during the measured period"

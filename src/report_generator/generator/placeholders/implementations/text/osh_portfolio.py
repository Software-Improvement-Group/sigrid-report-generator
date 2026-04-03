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

from report_generator.generator.domain import osh_portfolio_data
from report_generator.generator.placeholders.formatting.formatters import (
    calculate_stars,
    star_rating_round,
)
from report_generator.generator.utils.constants import OSHMetric

from ...formatting import smart_remarks
from .base import parameterized_text_placeholder, text_placeholder


@text_placeholder()
def portfolio_osh_total_deps():
    """Total number of identified open-source dependencies."""
    return osh_portfolio_data.dependencies_count


@text_placeholder()
def portfolio_osh_total_vuln():
    """Number of identified open-source dependencies with a known vulnerability."""
    return osh_portfolio_data.vulnerabilities_count


@text_placeholder()
def portfolio_osh_critical_risk():
    """Number of library-risk occurrences with critical-level risk across all OSH categories."""
    return osh_portfolio_data.library_risk_levels["critical"]


@text_placeholder()
def portfolio_osh_high_risk():
    """Number of library-risk occurrences with high-level risk across all OSH categories."""
    return osh_portfolio_data.library_risk_levels["high"]


@text_placeholder()
def portfolio_osh_medium_risk():
    """Number of library-risk occurrences with medium-level risk across all OSH categories."""
    return osh_portfolio_data.library_risk_levels["medium"]


@text_placeholder()
def portfolio_osh_low_risk():
    """Number of library-risk occurrences with low-level risk across all OSH categories."""
    return osh_portfolio_data.library_risk_levels["low"]


@text_placeholder()
def portfolio_osh_no_risk():
    """Number of library-risk occurrences with no OSH risk."""
    return osh_portfolio_data.library_risk_levels["no_risk"]


@text_placeholder()
def portfolio_osh_date_day():
    """The day of the month the latest system snapshot which was analyzed."""
    return osh_portfolio_data.date.strftime("%d")


@text_placeholder()
def portfolio_osh_date_month():
    """The month of the latest system snapshot which was analyzed."""
    return osh_portfolio_data.date.strftime("%b").upper()


@text_placeholder()
def portfolio_osh_date_year():
    """The year of the latest system snapshot which was analyzed."""
    return osh_portfolio_data.date.strftime("%Y")


@text_placeholder()
def portfolio_osh_vuln_summary():
    """Descriptive summary of open-source vulnerability issues identified."""
    return osh_portfolio_data.vulnerability_summary


@text_placeholder()
def portfolio_osh_freshness_summary():
    """Descriptive summary of open-source freshness issues identified."""
    return osh_portfolio_data.freshness_summary


@text_placeholder()
def portfolio_osh_legal_summary():
    """Descriptive summary of open-source legal issues identified."""
    return osh_portfolio_data.legal_summary


@text_placeholder()
def portfolio_osh_management_summary():
    """Descriptive summary of open-source management issues identified."""
    return osh_portfolio_data.management_summary


@text_placeholder()
def portfolio_osh_relative():
    """Relative rating remark for open-source health."""
    system_rating = osh_portfolio_data.get_score_for_prop("system")
    return smart_remarks.osh_relative_rating(system_rating)


@parameterized_text_placeholder(
    custom_key="PORTFOLIO_OSH_RATING_{parameter}", parameters=list(OSHMetric)
)
def portfolio_osh_rating_param(metric: OSHMetric):
    """The 0.5-5.5 star rating for this OSH metric."""
    metric_key = metric.to_json_name()
    return star_rating_round(osh_portfolio_data.get_score_for_prop(metric_key))


@parameterized_text_placeholder(
    custom_key="STARS_PF_{parameter}", parameters=list(OSHMetric)
)
def portfolio_osh_stars_param(metric: OSHMetric):
    """Stars corresponding to this OSH metric rating."""
    metric_key = metric.to_json_name()
    return calculate_stars(osh_portfolio_data.get_score_for_prop(metric_key))


@text_placeholder()
def portfolio_osh_above_market():
    """Percentage of systems scoring above market average (≥3.5 stars) on open-source health."""
    distribution = osh_portfolio_data.rating_distribution_percentages
    return distribution["above_market"]


@text_placeholder()
def portfolio_osh_market_average():
    """Percentage of systems scoring market average (2.5-3.5 stars) on open-source health."""
    distribution = osh_portfolio_data.rating_distribution_percentages
    return distribution["market_average"]


@text_placeholder()
def portfolio_osh_below_market():
    """Percentage of systems scoring below market average (<2.5 stars) on open-source health."""
    distribution = osh_portfolio_data.rating_distribution_percentages
    return distribution["below_market"]


@text_placeholder()
def portfolio_osh_avg_rating():
    """Volume-weighted average OSH rating across all systems in the portfolio."""
    return star_rating_round(osh_portfolio_data.weighted_average_rating)

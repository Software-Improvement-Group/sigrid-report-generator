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

import statistics

from report_generator.generator.domain import osh_portfolio_data
from report_generator.generator.placeholders.formatting.formatters import (
    calculate_stars,
    format_percentage_excluding_100_percent,
    star_rating_round,
)
from report_generator.generator.placeholders.implementations.misc.color_rating import (
    AbstractUrgencyShapePlaceholder,
)
from report_generator.generator.placeholders.implementations.shared.urgency import (
    UrgencyColors,
    exploit_probability_colors,
    exploit_probability_label,
    library_age_colors,
    library_age_label,
    urgency_colors,
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


@text_placeholder()
def osh_portfolio_probability_of_exploit():
    """Probability that at least one known vulnerability across the portfolio can be exploited within 30 days."""
    return format_percentage_excluding_100_percent(
        osh_portfolio_data.exploit_probability
    )


@text_placeholder()
def osh_portfolio_average_library_age():
    """Average number of days since the next release of each dependency across the portfolio."""
    distr = osh_portfolio_data.age_distribution
    if not distr:
        return "N/A"
    return f"{int(statistics.mean(distr))} days"


@text_placeholder()
def osh_portfolio_known_vulnerabilities_total_minus_unknown():
    """Total number of known vulnerabilities with a CVSS severity across the portfolio (critical + high + medium + low)."""
    distr = osh_portfolio_data.vulnerability_distribution
    return f"{distr['critical'] + distr['high'] + distr['medium'] + distr['low']}"


@text_placeholder()
def osh_portfolio_known_vulnerabilities_critical():
    """Number of known vulnerabilities with CVSS critical severity across the portfolio."""
    distr = osh_portfolio_data.vulnerability_distribution
    return f"{distr['critical']}"


@text_placeholder()
def osh_portfolio_known_vulnerabilities_high():
    """Number of known vulnerabilities with CVSS high severity across the portfolio."""
    distr = osh_portfolio_data.vulnerability_distribution
    return f"{distr['high']}"


@text_placeholder()
def osh_portfolio_known_vulnerabilities_medium():
    """Number of known vulnerabilities with CVSS medium severity across the portfolio."""
    distr = osh_portfolio_data.vulnerability_distribution
    return f"{distr['medium']}"


@text_placeholder()
def osh_portfolio_known_vulnerabilities_low():
    """Number of known vulnerabilities with CVSS low severity across the portfolio."""
    distr = osh_portfolio_data.vulnerability_distribution
    return f"{distr['low']}"


@text_placeholder()
def osh_portfolio_known_vulnerabilities_urgency_explanation():
    """Provides the explanation for the urgency reported by OSH_PORTFOLIO_KNOWN_VULNERABILITIES_URGENCY."""
    distr = osh_portfolio_data.vulnerability_distribution
    return smart_remarks.urgency_explanation(distr=distr)


class OSHPortfolioKnownVulnerabilitiesUrgency(AbstractUrgencyShapePlaceholder):
    """Colors a shape red, yellow, or green based on the urgency of known vulnerabilities across the portfolio."""

    key = "OSH_PORTFOLIO_KNOWN_VULNERABILITIES_URGENCY"

    @classmethod
    def value(cls):
        return "review"

    @classmethod
    def _get_colors(cls) -> UrgencyColors:
        return urgency_colors(osh_portfolio_data.vulnerability_distribution)


class OSHPortfolioAverageLibraryAgeUrgency(AbstractUrgencyShapePlaceholder):
    """Colors a shape red, orange, yellow, or green based on the average library age across the portfolio."""

    key = "OSH_PORTFOLIO_AVERAGE_LIBRARY_AGE_URGENCY"

    @classmethod
    def value(cls):
        return library_age_label(statistics.mean(osh_portfolio_data.age_distribution))

    @classmethod
    def _get_colors(cls) -> UrgencyColors:
        return library_age_colors(statistics.mean(osh_portfolio_data.age_distribution))


class OSHPortfolioExploitProbabilityUrgency(AbstractUrgencyShapePlaceholder):
    """Colors a shape red, orange, yellow, or green based on the probability of exploit across the portfolio."""

    key = "OSH_PORTFOLIO_PROBABILITY_OF_EXPLOIT_URGENCY"

    @classmethod
    def value(cls):
        return exploit_probability_label(osh_portfolio_data.exploit_probability)

    @classmethod
    def _get_colors(cls) -> UrgencyColors:
        return exploit_probability_colors(osh_portfolio_data.exploit_probability)

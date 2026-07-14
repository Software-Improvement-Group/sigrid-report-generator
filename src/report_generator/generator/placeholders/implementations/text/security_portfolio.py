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
    security_dashboard_findings_portfolio_data,
    security_dashboard_resolution_times_portfolio_data,
    security_findings_portfolio_data,
    security_ratings_change_portfolio_data,
    security_ratings_portfolio_data,
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
def portfolio_sec_above_market():
    """Percentage of systems scoring above market average (≥3.5 stars) on security."""
    distribution = security_ratings_portfolio_data.rating_distribution_percentages
    return distribution["above_market"]


@text_placeholder()
def portfolio_sec_market_average():
    """Percentage of systems scoring market average (2.5-3.5 stars) on security."""
    distribution = security_ratings_portfolio_data.rating_distribution_percentages
    return distribution["market_average"]


@text_placeholder()
def portfolio_sec_below_market():
    """Percentage of systems scoring below market average (<2.5 stars) on security."""
    distribution = security_ratings_portfolio_data.rating_distribution_percentages
    return distribution["below_market"]


@text_placeholder()
def portfolio_sec_avg_rating():
    """Volume-weighted average security rating across all systems in the portfolio."""
    return star_rating_round(security_ratings_portfolio_data.weighted_average_rating)


@market_average_text_placeholder()
def portfolio_sec_avg_market_average():
    """Colored indication of whether the portfolio's volume-weighted average security rating is
    below (red), at (blue) or above (green) market average."""
    return security_ratings_portfolio_data.weighted_average_rating


@delta_text_placeholder()
def portfolio_sec_average_delta():
    """Signed change in the portfolio's volume-weighted security average over the period (e.g. +0.01, -0.01, =), colored green up / red down / blue unchanged."""
    return security_ratings_change_portfolio_data.average_delta


@text_placeholder()
def portfolio_sec_period_start_date():
    """Start date of the reporting period for security findings.

    Returns the earliest month date from the actual API data.
    Security findings data includes month fields that are always the first of the month.
    """
    return security_dashboard_findings_portfolio_data._get_earliest_month()


@text_placeholder()
def portfolio_sec_critical_resolved():
    """Number of critical security findings that have been resolved."""
    return security_dashboard_findings_portfolio_data.critical_findings_statistics[
        "resolved"
    ]


@text_placeholder()
def portfolio_sec_critical_added():
    """Number of critical security findings that have been added."""
    return security_dashboard_findings_portfolio_data.critical_findings_statistics[
        "added"
    ]


@text_placeholder()
def portfolio_sec_relative_critical():
    """Whether there was an increase or decrease in critical security findings."""
    net_change = (
        security_dashboard_findings_portfolio_data.critical_findings_statistics[
            "net_change"
        ]
    )
    return (
        "an increase"
        if net_change > 0
        else "a decrease"
        if net_change < 0
        else "no change"
    )


@text_placeholder()
def portfolio_sec_critical_difference():
    """The absolute difference in critical security findings."""
    return abs(
        security_dashboard_findings_portfolio_data.critical_findings_statistics[
            "net_change"
        ]
    )


@text_placeholder()
def portfolio_sec_high_resolved():
    """Number of high severity security findings that have been resolved."""
    return security_dashboard_findings_portfolio_data.high_findings_statistics[
        "resolved"
    ]


@text_placeholder()
def portfolio_sec_high_added():
    """Number of high severity security findings that have been added."""
    return security_dashboard_findings_portfolio_data.high_findings_statistics["added"]


@text_placeholder()
def portfolio_sec_relative_high():
    """Whether there was an increase or decrease in high severity security findings."""
    net_change = security_dashboard_findings_portfolio_data.high_findings_statistics[
        "net_change"
    ]
    return (
        "an increase"
        if net_change > 0
        else "a decrease"
        if net_change < 0
        else "no change"
    )


@text_placeholder()
def portfolio_sec_high_difference():
    """The absolute difference in high severity security findings."""
    return abs(
        security_dashboard_findings_portfolio_data.high_findings_statistics[
            "net_change"
        ]
    )


@text_placeholder()
def portfolio_sec_medium_resolved():
    """Number of medium severity security findings that have been resolved."""
    return security_dashboard_findings_portfolio_data.medium_findings_statistics[
        "resolved"
    ]


@text_placeholder()
def portfolio_sec_medium_added():
    """Number of medium severity security findings that have been added."""
    return security_dashboard_findings_portfolio_data.medium_findings_statistics[
        "added"
    ]


@text_placeholder()
def portfolio_sec_relative_medium():
    """Whether there was an increase or decrease in medium severity security findings."""
    net_change = security_dashboard_findings_portfolio_data.medium_findings_statistics[
        "net_change"
    ]
    return (
        "an increase"
        if net_change > 0
        else "a decrease"
        if net_change < 0
        else "no change"
    )


@text_placeholder()
def portfolio_sec_medium_difference():
    """The absolute difference in medium severity security findings."""
    return abs(
        security_dashboard_findings_portfolio_data.medium_findings_statistics[
            "net_change"
        ]
    )


@text_placeholder()
def portfolio_sec_low_resolved():
    """Number of low severity security findings that have been resolved."""
    return security_dashboard_findings_portfolio_data.low_findings_statistics[
        "resolved"
    ]


@text_placeholder()
def portfolio_sec_low_added():
    """Number of low severity security findings that have been added."""
    return security_dashboard_findings_portfolio_data.low_findings_statistics["added"]


@text_placeholder()
def portfolio_sec_relative_low():
    """Whether there was an increase or decrease in low severity security findings."""
    net_change = security_dashboard_findings_portfolio_data.low_findings_statistics[
        "net_change"
    ]
    return (
        "an increase"
        if net_change > 0
        else "a decrease"
        if net_change < 0
        else "no change"
    )


@text_placeholder()
def portfolio_sec_low_difference():
    """The absolute difference in low severity security findings."""
    return abs(
        security_dashboard_findings_portfolio_data.low_findings_statistics["net_change"]
    )


@text_placeholder()
def portfolio_sec_critical_resolution_most():
    """The time bucket (in days) with the most critical findings resolved."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics[
        "most_days"
    ]


@text_placeholder()
def portfolio_sec_critical_resolution_findings_most():
    """Number of critical findings in the most common resolution time bucket."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics[
        "most_findings"
    ]


@text_placeholder()
def portfolio_sec_critical_resolution_no_risk():
    """Number of critical findings resolved within the recommended 7 days."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics[
        "no_risk"
    ]


@text_placeholder()
def portfolio_sec_critical_resolution_high_risk():
    """Number of critical findings resolved after 30 days or more."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics[
        "high_risk"
    ]


@text_placeholder()
def portfolio_sec_high_resolution_most():
    """The time bucket (in days) with the most high severity findings resolved."""
    return (
        security_dashboard_resolution_times_portfolio_data.high_resolution_statistics[
            "most_days"
        ]
    )


@text_placeholder()
def portfolio_sec_high_resolution_findings_most():
    """Number of high severity findings in the most common resolution time bucket."""
    return (
        security_dashboard_resolution_times_portfolio_data.high_resolution_statistics[
            "most_findings"
        ]
    )


@text_placeholder()
def portfolio_sec_high_resolution_no_risk():
    """Number of high severity findings resolved within the recommended 7 days."""
    return (
        security_dashboard_resolution_times_portfolio_data.high_resolution_statistics[
            "no_risk"
        ]
    )


@text_placeholder()
def portfolio_sec_high_resolution_high_risk():
    """Number of high severity findings resolved after 30 days or more."""
    return (
        security_dashboard_resolution_times_portfolio_data.high_resolution_statistics[
            "high_risk"
        ]
    )


@text_placeholder()
def portfolio_sec_medium_resolution_most():
    """The time bucket (in days) with the most medium severity findings resolved."""
    return (
        security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics[
            "most_days"
        ]
    )


@text_placeholder()
def portfolio_sec_medium_resolution_findings_most():
    """Number of medium severity findings in the most common resolution time bucket."""
    return (
        security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics[
            "most_findings"
        ]
    )


@text_placeholder()
def portfolio_sec_medium_resolution_no_risk():
    """Number of medium severity findings resolved within the recommended 7 days."""
    return (
        security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics[
            "no_risk"
        ]
    )


@text_placeholder()
def portfolio_sec_medium_resolution_high_risk():
    """Number of medium severity findings resolved after 30 days or more."""
    return (
        security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics[
            "high_risk"
        ]
    )


@text_placeholder()
def portfolio_sec_low_resolution_most():
    """The time bucket (in days) with the most low severity findings resolved."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics[
        "most_days"
    ]


@text_placeholder()
def portfolio_sec_low_resolution_findings_most():
    """Number of low severity findings in the most common resolution time bucket."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics[
        "most_findings"
    ]


@text_placeholder()
def portfolio_sec_low_resolution_no_risk():
    """Number of low severity findings resolved within the recommended 7 days."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics[
        "no_risk"
    ]


@text_placeholder()
def portfolio_sec_low_resolution_high_risk():
    """Number of low severity findings resolved after 30 days or more."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics[
        "high_risk"
    ]


@text_placeholder()
def security_portfolio_total_cvss_findings_raw():
    """Total number of security findings with a CVSS severity across the portfolio (critical + high + medium + low)."""
    return f"{security_findings_portfolio_data.count_findings('CRITICAL') + security_findings_portfolio_data.count_findings('HIGH') + security_findings_portfolio_data.count_findings('MEDIUM') + security_findings_portfolio_data.count_findings('LOW')}"


@text_placeholder()
def security_portfolio_cvss_critical_raw():
    """Number of security findings with CVSS critical severity across the portfolio."""
    return f"{security_findings_portfolio_data.count_findings('CRITICAL')}"


@text_placeholder()
def security_portfolio_cvss_high_raw():
    """Number of security findings with CVSS high severity across the portfolio."""
    return f"{security_findings_portfolio_data.count_findings('HIGH')}"


@text_placeholder()
def security_portfolio_cvss_medium_raw():
    """Number of security findings with CVSS medium severity across the portfolio."""
    return f"{security_findings_portfolio_data.count_findings('MEDIUM')}"


@text_placeholder()
def security_portfolio_cvss_low_raw():
    """Number of security findings with CVSS low severity across the portfolio."""
    return f"{security_findings_portfolio_data.count_findings('LOW')}"


@text_placeholder()
def portfolio_sec_increased():
    """Percentage of systems that have seen an increase in security rating."""
    return security_ratings_change_portfolio_data.change_distribution_percentages[
        "increased"
    ]


@text_placeholder()
def portfolio_sec_stable():
    """Percentage of systems whose security rating has remained stable."""
    return security_ratings_change_portfolio_data.change_distribution_percentages[
        "stable"
    ]


@text_placeholder()
def portfolio_sec_decreased():
    """Percentage of systems that have seen a decrease in security rating."""
    return security_ratings_change_portfolio_data.change_distribution_percentages[
        "decreased"
    ]


@text_placeholder()
def portfolio_sec_biggest_changes():
    """Descriptive summary of the biggest security rating changes in the portfolio."""
    res = []
    increase = security_ratings_change_portfolio_data.biggest_increase
    if increase:
        res.append(
            f"The largest increase in security rating was experienced by {increase[0]} ({increase[1]} stars)."
        )
    decrease = security_ratings_change_portfolio_data.biggest_decrease
    if decrease:
        res.append(
            f"The largest decrease in security rating was experienced by {decrease[0]} ({decrease[1]} stars)."
        )
    return " ".join(res)


@text_placeholder()
def portfolio_period_sec_change_short_summary():
    """The portfolio security rating change short summary over the reporting period."""
    start_avg = (
        int(security_ratings_change_portfolio_data.start_weighted_average * 10) / 10
    )
    end_avg = int(security_ratings_change_portfolio_data.end_weighted_average * 10) / 10
    diff = int((end_avg - start_avg) * 10) / 10
    if abs(diff) < 0.01:
        return f"The portfolio remained stable ({end_avg}) during the measured period"
    return f"The portfolio's security has {'increased' if start_avg < end_avg else 'decreased'} (with {diff} to {end_avg}) during the measured period"

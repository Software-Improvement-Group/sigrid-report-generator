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

from report_generator.generator.domain import (security_dashboard_findings_portfolio_data,
                                               security_dashboard_resolution_times_portfolio_data,
                                               security_ratings_portfolio_data)
from report_generator.generator.placeholders.formatting.formatters import star_rating_round
from .base import text_placeholder


@text_placeholder()
def portfolio_sec_above_market():
    """Percentage of systems scoring above market average (≥3.5 stars) on security."""
    distribution = security_ratings_portfolio_data.get_rating_distribution_percentages
    return distribution['above_market']


@text_placeholder()
def portfolio_sec_market_average():
    """Percentage of systems scoring market average (2.5-3.5 stars) on security."""
    distribution = security_ratings_portfolio_data.get_rating_distribution_percentages
    return distribution['market_average']


@text_placeholder()
def portfolio_sec_below_market():
    """Percentage of systems scoring below market average (<2.5 stars) on security."""
    distribution = security_ratings_portfolio_data.get_rating_distribution_percentages
    return distribution['below_market']


@text_placeholder()
def portfolio_sec_avg_rating():
    """Volume-weighted average security rating across all systems in the portfolio."""
    return star_rating_round(security_ratings_portfolio_data.weighted_average_rating)


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
    return security_dashboard_findings_portfolio_data.critical_findings_statistics['resolved']


@text_placeholder()
def portfolio_sec_critical_added():
    """Number of critical security findings that have been added."""
    return security_dashboard_findings_portfolio_data.critical_findings_statistics['added']


@text_placeholder()
def portfolio_sec_relative_critical():
    """Whether there was an increase or decrease in critical security findings."""
    net_change = security_dashboard_findings_portfolio_data.critical_findings_statistics['net_change']
    return 'an increase' if net_change > 0 else 'a decrease' if net_change < 0 else 'no change'


@text_placeholder()
def portfolio_sec_critical_difference():
    """The absolute difference in critical security findings."""
    return abs(security_dashboard_findings_portfolio_data.critical_findings_statistics['net_change'])


@text_placeholder()
def portfolio_sec_high_resolved():
    """Number of high severity security findings that have been resolved."""
    return security_dashboard_findings_portfolio_data.high_findings_statistics['resolved']


@text_placeholder()
def portfolio_sec_high_added():
    """Number of high severity security findings that have been added."""
    return security_dashboard_findings_portfolio_data.high_findings_statistics['added']


@text_placeholder()
def portfolio_sec_relative_high():
    """Whether there was an increase or decrease in high severity security findings."""
    net_change = security_dashboard_findings_portfolio_data.high_findings_statistics['net_change']
    return 'an increase' if net_change > 0 else 'a decrease' if net_change < 0 else 'no change'


@text_placeholder()
def portfolio_sec_high_difference():
    """The absolute difference in high severity security findings."""
    return abs(security_dashboard_findings_portfolio_data.high_findings_statistics['net_change'])


@text_placeholder()
def portfolio_sec_medium_resolved():
    """Number of medium severity security findings that have been resolved."""
    return security_dashboard_findings_portfolio_data.medium_findings_statistics['resolved']


@text_placeholder()
def portfolio_sec_medium_added():
    """Number of medium severity security findings that have been added."""
    return security_dashboard_findings_portfolio_data.medium_findings_statistics['added']


@text_placeholder()
def portfolio_sec_relative_medium():
    """Whether there was an increase or decrease in medium severity security findings."""
    net_change = security_dashboard_findings_portfolio_data.medium_findings_statistics['net_change']
    return 'an increase' if net_change > 0 else 'a decrease' if net_change < 0 else 'no change'


@text_placeholder()
def portfolio_sec_medium_difference():
    """The absolute difference in medium severity security findings."""
    return abs(security_dashboard_findings_portfolio_data.medium_findings_statistics['net_change'])


@text_placeholder()
def portfolio_sec_low_resolved():
    """Number of low severity security findings that have been resolved."""
    return security_dashboard_findings_portfolio_data.low_findings_statistics['resolved']


@text_placeholder()
def portfolio_sec_low_added():
    """Number of low severity security findings that have been added."""
    return security_dashboard_findings_portfolio_data.low_findings_statistics['added']


@text_placeholder()
def portfolio_sec_relative_low():
    """Whether there was an increase or decrease in low severity security findings."""
    net_change = security_dashboard_findings_portfolio_data.low_findings_statistics['net_change']
    return 'an increase' if net_change > 0 else 'a decrease' if net_change < 0 else 'no change'


@text_placeholder()
def portfolio_sec_low_difference():
    """The absolute difference in low severity security findings."""
    return abs(security_dashboard_findings_portfolio_data.low_findings_statistics['net_change'])


@text_placeholder()
def portfolio_sec_critical_resolution_most():
    """The time bucket (in days) with the most critical findings resolved."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics['most_days']


@text_placeholder()
def portfolio_sec_critical_resolution_findings_most():
    """Number of critical findings in the most common resolution time bucket."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics['most_findings']


@text_placeholder()
def portfolio_sec_critical_resolution_no_risk():
    """Number of critical findings resolved within the recommended 7 days."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics['no_risk']


@text_placeholder()
def portfolio_sec_critical_resolution_high_risk():
    """Number of critical findings resolved after 30 days or more."""
    return security_dashboard_resolution_times_portfolio_data.critical_resolution_statistics['high_risk']


@text_placeholder()
def portfolio_sec_high_resolution_most():
    """The time bucket (in days) with the most high severity findings resolved."""
    return security_dashboard_resolution_times_portfolio_data.high_resolution_statistics['most_days']


@text_placeholder()
def portfolio_sec_high_resolution_findings_most():
    """Number of high severity findings in the most common resolution time bucket."""
    return security_dashboard_resolution_times_portfolio_data.high_resolution_statistics['most_findings']


@text_placeholder()
def portfolio_sec_high_resolution_no_risk():
    """Number of high severity findings resolved within the recommended 7 days."""
    return security_dashboard_resolution_times_portfolio_data.high_resolution_statistics['no_risk']


@text_placeholder()
def portfolio_sec_high_resolution_high_risk():
    """Number of high severity findings resolved after 30 days or more."""
    return security_dashboard_resolution_times_portfolio_data.high_resolution_statistics['high_risk']


@text_placeholder()
def portfolio_sec_medium_resolution_most():
    """The time bucket (in days) with the most medium severity findings resolved."""
    return security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics['most_days']


@text_placeholder()
def portfolio_sec_medium_resolution_findings_most():
    """Number of medium severity findings in the most common resolution time bucket."""
    return security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics['most_findings']


@text_placeholder()
def portfolio_sec_medium_resolution_no_risk():
    """Number of medium severity findings resolved within the recommended 7 days."""
    return security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics['no_risk']


@text_placeholder()
def portfolio_sec_medium_resolution_high_risk():
    """Number of medium severity findings resolved after 30 days or more."""
    return security_dashboard_resolution_times_portfolio_data.medium_resolution_statistics['high_risk']


@text_placeholder()
def portfolio_sec_low_resolution_most():
    """The time bucket (in days) with the most low severity findings resolved."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics['most_days']


@text_placeholder()
def portfolio_sec_low_resolution_findings_most():
    """Number of low severity findings in the most common resolution time bucket."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics['most_findings']


@text_placeholder()
def portfolio_sec_low_resolution_no_risk():
    """Number of low severity findings resolved within the recommended 7 days."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics['no_risk']


@text_placeholder()
def portfolio_sec_low_resolution_high_risk():
    """Number of low severity findings resolved after 30 days or more."""
    return security_dashboard_resolution_times_portfolio_data.low_resolution_statistics['high_risk']

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

from report_generator.generator.constants import OSHMetric
from report_generator.generator.data_models import *
from report_generator.generator.formatters import smart_remarks
from report_generator.generator.formatters.formatters import calculate_stars, maintainability_round
from .base import parameterized_text_placeholder, text_placeholder


@text_placeholder()
def osh_risk_summary():
    """One-sentence summary of main OSH findings."""
    return smart_remarks.osh_remark(osh_data.raw_data)


@text_placeholder()
def osh_total_deps():
    """Total number of identified open-source dependencies."""
    return osh_data.data.total_deps


@text_placeholder()
def osh_total_vuln():
    """Number of identified open-source dependencies with a known vulnerability."""
    return osh_data.data.total_vulnerable


@text_placeholder()
def osh_date_day():
    """The day of the month the latest system snapshot which was analyzed."""
    return osh_data.data.date_day


@text_placeholder()
def osh_date_month():
    """The month of the latest system snapshot which was analyzed."""
    return osh_data.data.date_month


@text_placeholder()
def osh_date_year():
    """The year of the latest system snapshot which was analyzed."""
    return osh_data.data.date_year


@text_placeholder()
def osh_vuln_summary():
    """Descriptive summary of open-source vulnerability issues identified."""
    return osh_data.vulnerability_summary


@text_placeholder()
def osh_freshness_summary():
    """Descriptive summary of open-source freshness issues identified."""
    return osh_data.freshness_summary


@text_placeholder()
def osh_legal_summary():
    """Descriptive summary of open-source legal issues identified."""
    return osh_data.legal_summary


@text_placeholder()
def osh_management_summary():
    """Descriptive summary of open-source management issues identified."""
    return osh_data.management_summary


@text_placeholder()
def osh_relative():
    """Relative rating remark for open-source health."""
    return smart_remarks.osh_relative_rating(osh_data.data.ratings["system"])


@parameterized_text_placeholder(custom_key="OSH_RATING_{parameter}",
                                parameters=list(OSHMetric))
def osh_rating_param(metric: OSHMetric):
    """The 0.5-5.5 star rating for this OSH metric."""
    metric_key = metric.to_json_name()
    return maintainability_round(osh_data.get_score_for_prop(metric_key))


@parameterized_text_placeholder(custom_key="STARS_{parameter}",
                                parameters=list(OSHMetric))
def osh_stars_param(metric: OSHMetric):
    """Stars corresponding to this OSH metric rating."""
    metric_key = metric.to_json_name()
    return calculate_stars(osh_data.get_score_for_prop(metric_key))

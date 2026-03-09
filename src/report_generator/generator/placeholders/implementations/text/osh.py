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

from report_generator.generator.domain import *
from report_generator.generator.placeholders.formatting.formatters import (
    calculate_stars,
    star_rating_round,
)
from report_generator.generator.utils.constants import OSHMetric

from ...formatting import smart_remarks
from .base import parameterized_text_placeholder, text_placeholder


@text_placeholder()
def osh_risk_summary():
    """One-sentence summary of main OSH findings."""
    return smart_remarks.osh_remark(osh_data.raw_data)


@text_placeholder()
def osh_total_deps():
    """Total number of identified open-source dependencies."""
    return osh_data.dependencies_count


@text_placeholder()
def osh_total_vuln():
    """Number of open-source dependencies with a known vulnerability."""
    return osh_data.vulnerabilities_count


@text_placeholder()
def osh_total_legal_risk():
    """Number of open-source dependencies with a medium to critical license risk."""
    return osh_data.legal_risk_count


@text_placeholder()
def osh_total_outdated():
    """Number of open-source dependencies not updated in the last 2 years."""
    return osh_data.outdated_count


@text_placeholder()
def osh_total_unmanaged():
    """Number of open-source dependencies not managed using a package manager."""
    return osh_data.unmanaged_count


@text_placeholder()
def osh_total_activity_risk():
    """Number of open-source dependencies with activity risk."""
    return osh_data.activity_risk_count


@text_placeholder()
def osh_date_day():
    """The day of the month the latest system snapshot which was analyzed."""
    return osh_data.date.strftime("%d")


@text_placeholder()
def osh_date_month():
    """The month of the latest system snapshot which was analyzed."""
    return osh_data.date.strftime("%b").upper()


@text_placeholder()
def osh_date_month_full():
    """The month of the latest system snapshot which was analyzed, full name."""
    return osh_data.date.strftime("%B")


@text_placeholder()
def osh_date_year():
    """The year of the latest system snapshot which was analyzed."""
    return osh_data.date.strftime("%Y")


@text_placeholder()
def osh_vuln_summary():
    """Descriptive summary of open-source vulnerability issues identified."""
    if not osh_data.vulnerabilities_count:
        return "The system is free of known vulnerabilities."

    return f"{osh_data.vulnerabilities_fraction:.0%} of dependencies ({osh_data.vulnerabilities_count} in total) used in the system contain one or more known vulnerabilities."


@text_placeholder()
def osh_freshness_summary():
    """Descriptive summary of open-source freshness issues identified."""
    if not osh_data.outdated_count:
        return "All dependencies in the system have been updated in the last 2 years."

    return f"{osh_data.outdated_fraction:.0%} of dependencies ({osh_data.outdated_count} in total) used in the system have not been updated for over 2 years."


@text_placeholder()
def osh_legal_summary():
    """Descriptive summary of open-source legal issues identified."""
    if not osh_data.legal_risk_count:
        return "All dependencies in the system use relatively liberal open-source licenses."

    return f"{osh_data.legal_risk_fraction:.0%} of dependencies ({osh_data.legal_risk_count} in total) uses a potentially restrictive open-source license (e.g. GPL/AGPL)."


@text_placeholder()
def osh_management_summary():
    """Descriptive summary of open-source management issues identified."""
    if not osh_data.unmanaged_count:
        return "All dependencies in the system are managed by a package manager."

    return f"{osh_data.unmanaged_fraction:.0%} of dependencies ({osh_data.unmanaged_count} in total) does not use a package manager but is placed in the codebase directly."


@text_placeholder()
def osh_relative():
    """Relative rating remark for open-source health."""
    return smart_remarks.osh_relative_rating(osh_data.system_rating)


@parameterized_text_placeholder(
    custom_key="OSH_RATING_{parameter}", parameters=list(OSHMetric)
)
def osh_rating_param(metric: OSHMetric):
    """The 0.5-5.5 star rating for this OSH metric."""
    return star_rating_round(osh_data.get_rating_for_metric(metric))


@parameterized_text_placeholder(
    custom_key="STARS_{parameter}", parameters=list(OSHMetric)
)
def osh_stars_param(metric: OSHMetric):
    """Stars corresponding to this OSH metric rating."""
    return calculate_stars(osh_data.get_rating_for_metric(metric))

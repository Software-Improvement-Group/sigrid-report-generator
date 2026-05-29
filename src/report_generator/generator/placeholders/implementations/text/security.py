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

from report_generator.generator.domain import security_data
from report_generator.generator.placeholders.formatting.smart_remarks import (
    relative_to_market_average,
)

from .base import text_placeholder

from datetime import date


@text_placeholder()
def security_total_findings():
    return f"{len(security_data.findings)} security findings"


@text_placeholder()
def security_cvss_critical():
    return f"{security_data.count_findings('CRITICAL')} Critical severity findings"


@text_placeholder()
def security_cvss_high():
    return f"{security_data.count_findings('HIGH')} High severity findings"


@text_placeholder()
def security_acute_findings():
    """The number of open acute security findings, (Critical and High severity findings)."""
    acute_findings_count = security_data.count_findings(
        "CRITICAL"
    ) + security_data.count_findings("HIGH")
    return f"{acute_findings_count} Acute severity findings"


@text_placeholder()
def security_cvss_medium():
    return f"{security_data.count_findings('MEDIUM')} Medium severity findings"


@text_placeholder()
def security_cvss_low():
    return f"{security_data.count_findings('LOW')} Low severity findings"


@text_placeholder()
def security_relative():
    return f"{relative_to_market_average(security_data.security_rating)} market average"


@text_placeholder()
def security_total_cvss_findings_raw():
    """Total number of security findings with a CVSS severity (critical + high + medium + low)."""
    return f"{security_data.count_findings('CRITICAL') + security_data.count_findings('HIGH') + security_data.count_findings('MEDIUM') + security_data.count_findings('LOW')}"


@text_placeholder()
def security_cvss_critical_raw():
    """Number of security findings with CVSS critical severity."""
    return f"{security_data.count_findings('CRITICAL')}"


@text_placeholder()
def security_cvss_high_raw():
    """Number of security findings with CVSS high severity."""
    return f"{security_data.count_findings('HIGH')}"


@text_placeholder()
def security_cvss_medium_raw():
    """Number of security findings with CVSS medium severity."""
    return f"{security_data.count_findings('MEDIUM')}"


@text_placeholder()
def security_cvss_low_raw():
    """Number of security findings with CVSS low severity."""
    return f"{security_data.count_findings('LOW')}"


@text_placeholder()
def security_days_since_mythos_disclosure():
    """Number of days elapsed since Anthropic's initial Mythos disclosure on April 7, 2026."""
    return str((date.today() - date(2026, 4, 7)).days)
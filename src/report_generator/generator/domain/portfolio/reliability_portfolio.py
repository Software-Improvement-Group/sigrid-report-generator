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

from functools import cached_property

from report_generator.generator.domain.portfolio.shared.findings_portfolio_base import (
    FindingsRatingsPortfolioBase,
)

_NPR5333_FUNCTIONAL_SUITABILITY_CWES: frozenset[str] = frozenset(
    [
        "CWE-129",
        "CWE-248",
        "CWE-369",
        "CWE-390",
        "CWE-391",
        "CWE-392",
        "CWE-456",
        "CWE-457",
        "CWE-476",
        "CWE-478",
        "CWE-480",
        "CWE-484",
        "CWE-597",
        "CWE-667",
        "CWE-682",
        "CWE-783",
        "CWE-820",
        "CWE-821",
        "CWE-835",
        "CWE-1041",
        "CWE-1052",
        "CWE-1075",
        "CWE-1095",
        "CWE-1121",
    ]
)


class ReliabilityRatingsPortfolioData(FindingsRatingsPortfolioBase):
    _objective_type = "RELIABILITY_MAX_SEVERITY"
    _portfolio_ratings_api_method = "get_portfolio_reliability_ratings"
    _findings_api_method = "get_reliability_findings"

    @property
    def reliability_findings(self):
        return self._raw_findings

    @cached_property
    def functional_suitability_findings(self):
        return [
            {
                "systemName": entry["systemName"],
                "findings": [
                    f
                    for f in entry["findings"]
                    if f.get("cweId") in _NPR5333_FUNCTIONAL_SUITABILITY_CWES
                ],
            }
            for entry in self._raw_findings
        ]


reliability_ratings_portfolio_data = ReliabilityRatingsPortfolioData()

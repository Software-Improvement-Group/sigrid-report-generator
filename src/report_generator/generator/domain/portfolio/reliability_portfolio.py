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

import logging
from functools import cached_property

from report_generator.generator.context import sigrid_api
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared import utils
from report_generator.generator.domain.portfolio.shared.findings_above_severity import (
    build_objective_index,
    count_for_system,
)
from report_generator.generator.domain.portfolio.shared.rated_mixin import (
    RatedPortfolioMixin,
)
from report_generator.generator.utils.time_series import Period

_OBJECTIVE_TYPE = "RELIABILITY_MAX_SEVERITY"

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


class ReliabilityRatingsPortfolioData(RatedPortfolioMixin):
    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def data(self):
        return sigrid_api.get_portfolio_reliability_ratings()

    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]

    def get_system(self, system):
        return utils.get_system_helper(system, self.data, "systemName")

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data, "systemName")

    def _rated_systems(self):
        return self.data

    def _extract_rating(self, system):
        return system.get("rating")

    def _get_rating_and_volume(self, system):
        return utils.get_rating_and_volume_from_system(
            system, lambda s: s.get("rating"), "systemName"
        )

    @cached_property
    def reliability_findings(self):
        result = []
        for system_name in self.system_names:
            try:
                findings = sigrid_api.get_reliability_findings(system_name)
            except Exception:
                logging.warning(
                    f"Could not retrieve reliability findings for system '{system_name}'"
                )
                findings = []
            result.append({"systemName": system_name, "findings": findings})
        return result

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
            for entry in self.reliability_findings
        ]

    @cached_property
    def findings_above_objective(self):
        period = Period(*sigrid_api.get_period())
        objectives_systems = sigrid_api.get_objectives_evaluation(period)["systems"]
        objective_index = build_objective_index(objectives_systems, _OBJECTIVE_TYPE)
        return [
            {
                "systemName": entry["systemName"],
                "findings_above_objective": count_for_system(
                    entry["findings"],
                    objective_index.get(entry["systemName"]),
                ),
            }
            for entry in self.reliability_findings
        ]


reliability_ratings_portfolio_data = ReliabilityRatingsPortfolioData()

"""Example API response:
[
    {
        "id": "0009b8df-82db-43a9-b216-e2391ae72b54",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/0009b8df-82db-43a9-b216-e2391ae72b54",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-17",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-17",
        "filePath": "x-pack/plugin/esql/src/internalClusterTest/java/org/elasticsearch/xpack/esql/action/FailingPauseFieldPlugin.java",
        "startLine": 43,
        "endLine": 43,
        "component": "x-pack",
        "type": "Method ignores return value",
        "cweId": "CWE-252",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.6,
        "impactScore": 3.3,
        "exploitabilityScore": 3.3,
        "status": "RAW",
        "remark": null,
        "toolName": "SpotBugs",
        "ruleId": "RV_RETURN_VALUE_IGNORED",
        "weaknessIds": [
            "CWE-252"
        ],
        "categories": [
            "8. Error Handling"
        ],
        "fingerprint": "feff53bf794fe32db1ae926ee416765654a881754bff87c4a022ad93d742eb19",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "00191ea2-ca38-4295-b052-fb714c3552a6",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/00191ea2-ca38-4295-b052-fb714c3552a6",
        "firstSeenAnalysisDate": "2022-05-16",
        "lastSeenAnalysisDate": "2026-05-17",
        "firstSeenSnapshotDate": "2022-05-16",
        "lastSeenSnapshotDate": "2026-05-17",
        "filePath": "server/src/internalClusterTest/java/org/elasticsearch/search/aggregations/bucket/IpTermsIT.java",
        "startLine": 75,
        "endLine": 75,
        "component": "server",
        "type": "Using hardcoded IP addresses is security-sensitive",
        "cweId": "CWE-547",
        "severity": "INFORMATION",
        "impact": "INFORMATION",
        "exploitability": "INFORMATION",
        "severityScore": 0.0,
        "impactScore": 0.0,
        "exploitabilityScore": 0.0,
        "status": "RAW",
        "remark": null,
        "toolName": "SonarQube (Java)",
        "ruleId": "S1313",
        "weaknessIds": [
            "CWE-547",
            "SIG-CLOUD-17"
        ],
        "categories": [
            "7. Hard-coded Configuration"
        ],
        "fingerprint": "4d3ce15b3906a69ce39e5326e7a7a53e8663a3641cb7dff2d49d4453de62f464",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "003ec8e8-170f-4926-835a-c63a82bd7e3e",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/003ec8e8-170f-4926-835a-c63a82bd7e3e",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-17",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-17",
        "filePath": "x-pack/plugin/core/src/main/java/org/elasticsearch/xpack/core/ilm/LifecycleOperationMetadata.java",
        "startLine": 100,
        "endLine": 100,
        "component": "x-pack",
        "type": "Method uses immediate execution of a block of code that is often not used",
        "cweId": "CWE-670",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.8,
        "impactScore": 3.3,
        "exploitabilityScore": 3.5,
        "status": "RAW",
        "remark": null,
        "toolName": "FB Contrib",
        "ruleId": "OI_OPTIONAL_ISSUES_USES_IMMEDIATE_EXECUTION",
        "weaknessIds": [
            "CWE-670"
        ],
        "categories": [
            "2. Logic & Data Flow"
        ],
        "fingerprint": "8ed0c71849d10c5f6b85db64fe0d530f80fe34441a7325640d49918273a22656",
        "isManualFinding": false,
        "isSeverityOverridden": false
    }
]
"""

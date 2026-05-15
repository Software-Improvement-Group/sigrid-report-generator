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

_OBJECTIVE_TYPE = "SECURITY_MAX_SEVERITY"


class SecurityRatingsPortfolioData(RatedPortfolioMixin):
    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def data(self):
        return sigrid_api.get_portfolio_security_ratings()

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
    def security_findings(self):
        result = []
        for system_name in self.system_names:
            try:
                findings = sigrid_api.get_security_findings(system_name)
            except Exception:
                logging.warning(
                    f"Could not retrieve security findings for system '{system_name}'"
                )
                findings = []
            result.append({"systemName": system_name, "findings": findings})
        return result

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
            for entry in self.security_findings
        ]


security_ratings_portfolio_data = SecurityRatingsPortfolioData()

"""
Example findings api response:
[
    {
        "id": "0009b8df-82db-43a9-b216-e2391ae72b54",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/0009b8df-82db-43a9-b216-e2391ae72b54",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
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
            "A10:2025 - Mishandling of Exceptional Conditions"
        ],
        "fingerprint": "feff53bf794fe32db1ae926ee416765654a881754bff87c4a022ad93d742eb19",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "00191ea2-ca38-4295-b052-fb714c3552a6",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/00191ea2-ca38-4295-b052-fb714c3552a6",
        "firstSeenAnalysisDate": "2022-05-16",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2022-05-16",
        "lastSeenSnapshotDate": "2026-05-10",
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
            "A02:2025 - Security Misconfiguration"
        ],
        "fingerprint": "4d3ce15b3906a69ce39e5326e7a7a53e8663a3641cb7dff2d49d4453de62f464",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "0105791d-da90-451f-abe4-0bdc917abf7f",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/0105791d-da90-451f-abe4-0bdc917abf7f",
        "firstSeenAnalysisDate": "2026-05-10",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2026-05-10",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "libs/cli-terminal/src/main/java/org/elasticsearch/cli/terminal/internal/EcsJsonUtils.java",
        "startLine": 87,
        "endLine": 87,
        "component": "libs",
        "type": "Information Exposure Through An Error Message",
        "cweId": "CWE-209",
        "severity": "MEDIUM",
        "impact": "LOW",
        "exploitability": "MEDIUM",
        "severityScore": 4.3,
        "impactScore": 1.6,
        "exploitabilityScore": 2.7,
        "status": "RAW",
        "remark": "",
        "toolName": "FindSecBugs",
        "ruleId": "INFORMATION_EXPOSURE_THROUGH_AN_ERROR_MESSAGE",
        "weaknessIds": [
            "CWE-209"
        ],
        "categories": [
            "A10:2025 - Mishandling of Exceptional Conditions"
        ],
        "fingerprint": "e76bcec40ba99350d78ee2b42dd6f43a672f9faba7bf1246682df62c1ef3d5b3",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "011c7ff4-9965-492d-9d18-28dec79d1552",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/011c7ff4-9965-492d-9d18-28dec79d1552",
        "firstSeenAnalysisDate": "2021-11-29",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2021-11-29",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "server/src/internalClusterTest/java/org/elasticsearch/indices/stats/IndexStatsIT.java",
        "startLine": 1295,
        "endLine": 1295,
        "component": "server",
        "type": "\"InterruptedException\" and \"ThreadDeath\" should not be ignored",
        "cweId": "CWE-391",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.9,
        "impactScore": 3.5,
        "exploitabilityScore": 3.4,
        "status": "RAW",
        "remark": "",
        "toolName": "SonarQube (Java)",
        "ruleId": "S2142",
        "weaknessIds": [
            "CWE-391"
        ],
        "categories": [
            "A10:2025 - Mishandling of Exceptional Conditions"
        ],
        "fingerprint": "b9cb30a87177c287eb0e4496bd58236ca7c533239821fec5b8963b51317402fa",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "01375157-b925-4289-9be7-a2aaf62bd116",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/01375157-b925-4289-9be7-a2aaf62bd116",
        "firstSeenAnalysisDate": "2026-02-15",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2026-02-15",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "server/src/main/java/org/elasticsearch/index/codec/vectors/diskbbq/CentroidSupplier.java",
        "startLine": 60,
        "endLine": 60,
        "component": "server",
        "type": "Method calls Array.asList on an array of primitive values",
        "cweId": "CWE-628",
        "severity": "INFORMATION",
        "impact": "INFORMATION",
        "exploitability": "INFORMATION",
        "severityScore": 0.0,
        "impactScore": 0.0,
        "exploitabilityScore": 0.0,
        "status": "RAW",
        "remark": null,
        "toolName": "FB Contrib",
        "ruleId": "CAAL_CONFUSING_ARRAY_AS_LIST",
        "weaknessIds": [
            "CWE-628"
        ],
        "categories": [
            "A06:2025 - Insecure Design"
        ],
        "fingerprint": "59630966113605a08911bf185661e94863659286809dafb8007cacc363134fc7",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "01ee385c-8bce-4d83-a05b-8cda50f68896",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/01ee385c-8bce-4d83-a05b-8cda50f68896",
        "firstSeenAnalysisDate": "2026-02-22",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2026-02-22",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "dev-tools/prometheus-local/docker-compose.yml",
        "startLine": 70,
        "endLine": 0,
        "component": "dev-tools",
        "type": "Passwords And Secrets - Generic Password",
        "cweId": "CWE-522",
        "severity": "HIGH",
        "impact": "HIGH",
        "exploitability": "HIGH",
        "severityScore": 8.2,
        "impactScore": 4.9,
        "exploitabilityScore": 3.3,
        "status": "RAW",
        "remark": null,
        "toolName": "KICS",
        "ruleId": "487f4be7-3fd9-4506-a07a-eae252180c08",
        "weaknessIds": [
            "CWE-522"
        ],
        "categories": [
            "A06:2025 - Insecure Design"
        ],
        "fingerprint": "afb9b077fb38a1ba0dd49dbbfcb7af1b8d8312c61c3d9abec6e71d9c04621820",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "020792c3-f22c-4121-83d3-e229ef46139a",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/020792c3-f22c-4121-83d3-e229ef46139a",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "server/src/internalClusterTest/java/org/elasticsearch/search/fieldcaps/FieldCapabilitiesIT.java",
        "startLine": 1144,
        "endLine": 1144,
        "component": "server",
        "type": "\"InterruptedException\" and \"ThreadDeath\" should not be ignored",
        "cweId": "CWE-391",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.9,
        "impactScore": 3.5,
        "exploitabilityScore": 3.4,
        "status": "RAW",
        "remark": null,
        "toolName": "SonarQube (Java)",
        "ruleId": "S2142",
        "weaknessIds": [
            "CWE-391"
        ],
        "categories": [
            "A10:2025 - Mishandling of Exceptional Conditions"
        ],
        "fingerprint": "c6abc04b3abeb022bf5ebda61a0e047f82815929212e5d98c634e25614ca8541",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "022c5d55-de0d-4d4d-9718-1cdb0c96fb30",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/022c5d55-de0d-4d4d-9718-1cdb0c96fb30",
        "firstSeenAnalysisDate": "2026-05-03",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2026-05-03",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "x-pack/plugin/stateless/src/main/java/org/elasticsearch/xpack/stateless/cache/StatelessOnlinePrewarmingService.java",
        "startLine": 69,
        "endLine": 69,
        "component": "x-pack",
        "type": "\"ThreadLocal\" variables should be cleaned up when no longer used ",
        "cweId": "CWE-459",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.1,
        "impactScore": 3.0,
        "exploitabilityScore": 3.1,
        "status": "RAW",
        "remark": "",
        "toolName": "SonarQube (Java)",
        "ruleId": "S5164",
        "weaknessIds": [
            "CWE-459"
        ],
        "categories": [
            "Other"
        ],
        "fingerprint": "6951881cbcd9f24839d6472b2694600f9fe17f6651e46baea13cebc7c7ca919a",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "02ab8eb1-f05f-45ee-9481-ee9296e36714",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/02ab8eb1-f05f-45ee-9481-ee9296e36714",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "modules/percolator/src/internalClusterTest/java/org/elasticsearch/percolator/PercolatorQuerySearchIT.java",
        "startLine": 268,
        "endLine": 268,
        "component": "modules",
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
            "A02:2025 - Security Misconfiguration"
        ],
        "fingerprint": "b3b6a461f735838c033cb8b822c9e4fc442c2cee79df7a50fee52020ba4b223a",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "02c34f63-91d5-49bb-a82d-8e2a8104429a",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/02c34f63-91d5-49bb-a82d-8e2a8104429a",
        "firstSeenAnalysisDate": "2022-05-16",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2022-05-16",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "x-pack/plugin/core/src/main/java/org/elasticsearch/xpack/core/ml/inference/trainedmodel/PredictionFieldType.java",
        "startLine": 73,
        "endLine": 73,
        "component": "x-pack",
        "type": "Method converts String to boxed primitive using excessive boxing",
        "cweId": "CWE-1235",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.2,
        "impactScore": 3.0,
        "exploitabilityScore": 3.2,
        "status": "RAW",
        "remark": null,
        "toolName": "FB Contrib",
        "ruleId": "NAB_NEEDLESS_BOXING_VALUEOF",
        "weaknessIds": [
            "CWE-1235"
        ],
        "categories": [
            "Other"
        ],
        "fingerprint": "48918115629b16cb043167d378beb0a2faebba8641977f7e57a06182d9c97982",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "02e6237a-947a-435b-9025-62de4bcfb0ce",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/02e6237a-947a-435b-9025-62de4bcfb0ce",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "x-pack/plugin/esql/src/internalClusterTest/java/org/elasticsearch/xpack/esql/action/AbstractEnrichBasedCrossClusterTestCase.java",
        "startLine": 178,
        "endLine": 178,
        "component": "x-pack",
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
            "A02:2025 - Security Misconfiguration"
        ],
        "fingerprint": "119be7a7bbe66ee51ac2c71514b8a59a81e547694ca983d14746ff39273e0de4",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "02f6b11d-006e-4900-8299-7f903b391204",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/02f6b11d-006e-4900-8299-7f903b391204",
        "firstSeenAnalysisDate": "2022-05-16",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2022-05-16",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "qa/remote-clusters/docker-compose-oss.yml",
        "startLine": 4,
        "endLine": 0,
        "component": "qa",
        "type": "Cpus Not Limited",
        "cweId": "CWE-400",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.2,
        "impactScore": 3.0,
        "exploitabilityScore": 3.2,
        "status": "RAW",
        "remark": null,
        "toolName": "KICS",
        "ruleId": "6b610c50-99fb-4ef0-a5f3-e312fd945bc3",
        "weaknessIds": [
            "CWE-400"
        ],
        "categories": [
            "Other"
        ],
        "fingerprint": "582c753b10ba2147194547314c178be61e5a0211ef80517bb9d9b182f51fb35f",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "0345fd41-5334-409f-b186-4e8fd5b834ef",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/0345fd41-5334-409f-b186-4e8fd5b834ef",
        "firstSeenAnalysisDate": "2021-11-29",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2021-11-29",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "libs/ssl-config/src/main/java/org/elasticsearch/common/ssl/TrustEverythingConfig.java",
        "startLine": 46,
        "endLine": 46,
        "component": "libs",
        "type": "Server certificates should be verified during SSL/TLS connections",
        "cweId": "CWE-295",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "MEDIUM",
        "severityScore": 6.3,
        "impactScore": 3.6,
        "exploitabilityScore": 2.7,
        "status": "RAW",
        "remark": "SonarQube (Java): Reference: https://rules.sonarsource.com/java/RSPEC-4830",
        "toolName": "SonarQube (Java)",
        "ruleId": "S4830",
        "weaknessIds": [
            "CWE-295"
        ],
        "categories": [
            "A07:2025 - Authentication Failures"
        ],
        "fingerprint": "bed1b62e9ec68df4eaa2f7679531c835021ef91307d78da4eafa648c8b47420e",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "037d6258-6090-4e58-9d68-35555c1aa832",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/037d6258-6090-4e58-9d68-35555c1aa832",
        "firstSeenAnalysisDate": "2022-04-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2022-04-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "plugins/examples/security-authorization-engine/build.gradle",
        "startLine": 1,
        "endLine": 0,
        "component": "plugins",
        "type": "Gradle dependency com.fasterxml.jackson.core:jackson-databind contains 4 vulnerabilities",
        "cweId": "CWE-400",
        "severity": "HIGH",
        "impact": "MEDIUM",
        "exploitability": "CRITICAL",
        "severityScore": 7.5,
        "impactScore": 3.6,
        "exploitabilityScore": 3.9,
        "status": "RAW",
        "remark": "SIG Open Source Health: This dependency contains the following vulnerabilities:\n\nCVE-2020-36518 (7.5)\n\nFor further details, please visit Sigrid's Open-source health page.",
        "toolName": "SIG Open Source Health",
        "ruleId": "OSH",
        "weaknessIds": [
            "CWE-400",
            "CWE-502",
            "CWE-770",
            "CWE-787",
            "CWE-1035"
        ],
        "categories": [
            "A08:2025 - Software or Data Integrity Failures",
            "Other",
            "A05:2025 - Injection",
            "Other",
            "A03:2025 - Software Supply Chain Failures"
        ],
        "fingerprint": "6c9bb4e4b2002c130d0db97d78f8c95a912f0faa0cd66d60d7503572eb1caa5a",
        "isManualFinding": false,
        "isSeverityOverridden": true
    },
    {
        "id": "03daf072-71b6-4f49-b165-3fdd25a600cb",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/03daf072-71b6-4f49-b165-3fdd25a600cb",
        "firstSeenAnalysisDate": "2026-02-15",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2026-02-15",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "x-pack/plugin/ql/src/main/java/org/elasticsearch/xpack/ql/querydsl/query/MatchQuery.java",
        "startLine": 40,
        "endLine": 40,
        "component": "x-pack",
        "type": "Boxing/unboxing to parse a primitive",
        "cweId": "CWE-1235",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.2,
        "impactScore": 3.0,
        "exploitabilityScore": 3.2,
        "status": "RAW",
        "remark": null,
        "toolName": "SpotBugs",
        "ruleId": "DM_BOXED_PRIMITIVE_FOR_PARSING",
        "weaknessIds": [
            "CWE-1235"
        ],
        "categories": [
            "Other"
        ],
        "fingerprint": "6d2c71444ca95da84100c54561273f91540920f4d0ad458a939b43d2d9115a7f",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "04624a2f-f98e-4ae8-a7b4-7f4c8c4637bb",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/04624a2f-f98e-4ae8-a7b4-7f4c8c4637bb",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "x-pack/plugin/security/src/internalClusterTest/java/org/elasticsearch/integration/FieldLevelSecurityTests.java",
        "startLine": 2285,
        "endLine": 2285,
        "component": "x-pack",
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
            "A02:2025 - Security Misconfiguration"
        ],
        "fingerprint": "0ee61c13742ce2be0c0b0fa3620240f1bb53ea5ebe75fa6bdd94a086e83ec3fd",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "04b72ff5-ef5f-45ea-9d5a-4c0b9bab77ba",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/04b72ff5-ef5f-45ea-9d5a-4c0b9bab77ba",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "server/src/internalClusterTest/java/org/elasticsearch/search/aggregations/bucket/IpRangeIT.java",
        "startLine": 200,
        "endLine": 200,
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
            "A02:2025 - Security Misconfiguration"
        ],
        "fingerprint": "ebfeb9454db9d4c26679639a77b4991853693ca6eed6b6c72e45bff2a332665c",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "056d4e71-3986-445b-aebe-b358b4884b7f",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/056d4e71-3986-445b-aebe-b358b4884b7f",
        "firstSeenAnalysisDate": "2025-12-07",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-12-07",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "test/fixtures/hdfs-fixture/build.gradle",
        "startLine": 1,
        "endLine": 0,
        "component": "test",
        "type": "Gradle dependency org.eclipse.jetty:jetty-xml contains 1 vulnerability",
        "cweId": "CWE-611",
        "severity": "LOW",
        "impact": "MEDIUM",
        "exploitability": "LOW",
        "severityScore": 3.9,
        "impactScore": 3.4,
        "exploitabilityScore": 0.5,
        "status": "RAW",
        "remark": "SIG Open Source Health: This dependency contains the following vulnerabilities:\n\nGHSA-58qw-p7qm-5rvh (3.9)\n\nFor further details, please visit Sigrid's Open-source health page.",
        "toolName": "SIG Open Source Health",
        "ruleId": "OSH",
        "weaknessIds": [
            "CWE-611",
            "CWE-1035"
        ],
        "categories": [
            "A02:2025 - Security Misconfiguration",
            "A03:2025 - Software Supply Chain Failures"
        ],
        "fingerprint": "146a096ecae6fe2a8217ceb84bba8b52fa6900d73ea66a5b24cd7bf06b1f0f8d",
        "isManualFinding": false,
        "isSeverityOverridden": true
    },
    {
        "id": "05a553f3-6729-49bc-9fe0-527c50a8296d",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/05a553f3-6729-49bc-9fe0-527c50a8296d",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "server/src/main/java/org/elasticsearch/script/StatsSummary.java",
        "startLine": 43,
        "endLine": 43,
        "component": "server",
        "type": "Boxed value is unboxed and then immediately reboxed",
        "cweId": "CWE-1235",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.2,
        "impactScore": 3.0,
        "exploitabilityScore": 3.2,
        "status": "RAW",
        "remark": null,
        "toolName": "SpotBugs",
        "ruleId": "BX_UNBOXING_IMMEDIATELY_REBOXED",
        "weaknessIds": [
            "CWE-1235"
        ],
        "categories": [
            "Other"
        ],
        "fingerprint": "876e4816639cc0d553a662637a746fd61708f6906853cfdfa11a05827d6d0a75",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "06933a99-9ab0-4f0a-8ccd-d7146558149e",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/06933a99-9ab0-4f0a-8ccd-d7146558149e",
        "firstSeenAnalysisDate": "2025-11-11",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2025-11-11",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "server/src/main/java/org/elasticsearch/index/codec/ForUtil.java",
        "startLine": 865,
        "endLine": 865,
        "component": "server",
        "type": "Ints and longs should not be shifted by zero or more than their number of bits-1",
        "cweId": "CWE-1335",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.8,
        "impactScore": 3.6,
        "exploitabilityScore": 3.2,
        "status": "RAW",
        "remark": null,
        "toolName": "SonarQube (Java)",
        "ruleId": "S2183",
        "weaknessIds": [
            "CWE-1335"
        ],
        "categories": [
            "Other"
        ],
        "fingerprint": "8506e7c18ff83fd7a2c3de46646b524ccdfd519673b9bfb6996b9108b8027334",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "06983728-df3b-47e9-aa5d-ce325fa3f5c1",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/06983728-df3b-47e9-aa5d-ce325fa3f5c1",
        "firstSeenAnalysisDate": "2021-11-29",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2021-11-29",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "x-pack/plugin/ccr/src/internalClusterTest/java/org/elasticsearch/xpack/ccr/AutoFollowIT.java",
        "startLine": 553,
        "endLine": 553,
        "component": "x-pack",
        "type": "Return values should not be ignored when they contain the operation status code",
        "cweId": "CWE-754",
        "severity": "MEDIUM",
        "impact": "MEDIUM",
        "exploitability": "HIGH",
        "severityScore": 6.9,
        "impactScore": 3.5,
        "exploitabilityScore": 3.4,
        "status": "RAW",
        "remark": "SonarQube (Java): Reference: https://rules.sonarsource.com/java/RSPEC-899",
        "toolName": "SonarQube (Java)",
        "ruleId": "S899",
        "weaknessIds": [
            "CWE-754"
        ],
        "categories": [
            "A10:2025 - Mishandling of Exceptional Conditions"
        ],
        "fingerprint": "33a8a82fa9bfb18440746ac0f523d75872dd700d92bd8a91c53ed27232395c89",
        "isManualFinding": false,
        "isSeverityOverridden": false
    },
    {
        "id": "07020809-d782-43b6-b0dd-707f7017ff58",
        "href": "https://sigrid-says.com/opendemo/elasticsearch/-/security/07020809-d782-43b6-b0dd-707f7017ff58",
        "firstSeenAnalysisDate": "2022-05-16",
        "lastSeenAnalysisDate": "2026-05-10",
        "firstSeenSnapshotDate": "2022-05-16",
        "lastSeenSnapshotDate": "2026-05-10",
        "filePath": "modules/percolator/src/internalClusterTest/java/org/elasticsearch/percolator/PercolatorQuerySearchIT.java",
        "startLine": 220,
        "endLine": 220,
        "component": "modules",
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
            "A02:2025 - Security Misconfiguration"
        ],
        "fingerprint": "61e24cc58cec4c52b2a24c6b27c0dd182941d1c56ac7d568dfb1e34962af9c89",
        "isManualFinding": false,
        "isSeverityOverridden": false
    }
]
"""

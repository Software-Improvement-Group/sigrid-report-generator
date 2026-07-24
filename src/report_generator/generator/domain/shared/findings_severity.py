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

from report_generator.generator.utils.constants.severity import SEVERITY_ORDER

FALLBACK_SEVERITY_THRESHOLD = "MEDIUM"


def count_findings_above_severity(findings: list, target_severity: str) -> int:
    target_rank = SEVERITY_ORDER.get(target_severity)
    if target_rank is None:
        logging.warning(f"Unknown target severity '{target_severity}', defaulting to 0")
        return 0
    count = 0
    for finding in findings:
        rank = SEVERITY_ORDER.get(finding.get("severity", ""))
        if rank is None:
            logging.warning(
                f"Unknown finding severity '{finding.get('severity')}', skipping"
            )
            continue
        if rank > target_rank:
            count += 1
    return count


def count_findings_above_objective(findings: list, objective: dict | None) -> int:
    if objective is None:
        return count_findings_above_severity(findings, FALLBACK_SEVERITY_THRESHOLD)
    if objective["targetMetAtEnd"] == "MET":
        return 0
    return count_findings_above_severity(findings, objective["target"])

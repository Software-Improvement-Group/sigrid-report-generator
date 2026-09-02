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

from report_generator.generator.context import config, sigrid_api
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.context.sigrid_api import (
    SigridAccessDeniedError,
    SigridAPIRequestFailedError,
)
from report_generator.generator.domain.portfolio.maintainability_portfolio import (
    maintainability_portfolio_data,
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


def _fetch_findings(method_name: str, system_name: str) -> list:
    try:
        return getattr(sigrid_api, method_name)(system_name)
    except (SigridAPIRequestFailedError, SigridAccessDeniedError):
        logging.warning(
            f"Could not retrieve {method_name} for system '{system_name}'",
            exc_info=True,
        )
        return []


def _merge_and_deduplicate(reliability: list, security: list) -> list:
    seen_ids: set = set()
    result = []
    for finding in reliability + security:
        finding_id = finding.get("id")
        if finding_id is None or finding_id not in seen_ids:
            result.append(finding)
            if finding_id is not None:
                seen_ids.add(finding_id)
    return result


class Npr5333FunctionalSuitabilityPortfolioData:
    @property
    def customer(self) -> str:
        return config.get_customer()

    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def _reliability_ratings(self):
        return sorted(
            sigrid_api.get_portfolio_reliability_ratings(),
            key=lambda s: s["systemName"],
        )

    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def _security_ratings(self):
        return sorted(
            sigrid_api.get_portfolio_security_ratings(),
            key=lambda s: s["systemName"],
        )

    @cached_property
    def system_names(self):
        reliability_names = {s["systemName"] for s in self._reliability_ratings}
        security_names = {s["systemName"] for s in self._security_ratings}
        return sorted(reliability_names | security_names)

    @cached_property
    def findings(self):
        result = []
        for system_name in self.system_names:
            reliability = _fetch_findings("get_reliability_findings", system_name)
            security = _fetch_findings("get_security_findings", system_name)
            merged = _merge_and_deduplicate(reliability, security)
            filtered = [
                f
                for f in merged
                if f.get("cweId") in _NPR5333_FUNCTIONAL_SUITABILITY_CWES
            ]
            result.append({"systemName": system_name, "findings": filtered})
        return result

    def _enrich_with_maintainability(self, entry: dict) -> dict:
        system_name = entry["systemName"]
        snapshot = maintainability_portfolio_data.end_snapshot(system_name)
        return {
            "systemName": system_name,
            "display_name": maintainability_portfolio_data.get_system_display_name(
                system_name
            ),
            "finding_count": len(entry["findings"]),
            "test_code_ratio": snapshot.get("testCodeRatio") if snapshot else None,
        }

    @cached_property
    def top_systems_by_finding_count(self) -> list[dict]:
        ranked = sorted(self.findings, key=lambda e: len(e["findings"]), reverse=True)
        return [self._enrich_with_maintainability(entry) for entry in ranked]


npr_5333_functional_suitability_portfolio_data = (
    Npr5333FunctionalSuitabilityPortfolioData()
)

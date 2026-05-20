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

from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date
from functools import cached_property

from report_generator.generator.domain.external.epss import epss_data

_RISK_LABEL = {0: "critical", 1: "high", 2: "medium", 3: "low", 4: "no_risk"}
_RISK_PROPERTY_NAMES = [
    "sigrid:risk:vulnerability",
    "sigrid:risk:legal",
    "sigrid:risk:freshness",
    "sigrid:risk:stability",
    "sigrid:risk:management",
    "sigrid:risk:activity",
]

_SEVERITY_LEVELS = ("critical", "high", "medium", "low")


def vulnerability_severity_counts(vulnerabilities: list[dict]) -> dict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    counts["total"] = len(vulnerabilities)
    for vuln in vulnerabilities:
        severities = {r["severity"].lower() for r in vuln.get("ratings", [])}
        for level in _SEVERITY_LEVELS:
            if level in severities:
                counts[level] += 1
                break
        else:
            counts["unknown"] += 1
    return counts


def map_cves_to_affected_libraries(
    components: list[dict], vulnerabilities: list[dict]
) -> dict[str, dict]:
    components_by_ref = {c["bom-ref"]: c for c in components}
    result = {}
    for vuln in vulnerabilities:
        affected = [
            {"name": c.get("name"), "version": c.get("version"), "purl": c.get("purl")}
            for ref in vuln.get("affects", [])
            if (c := components_by_ref.get(ref["ref"]))
        ]
        result[vuln["id"]] = {"count": len(affected), "libraries": affected}
    return result


def _find_cyclonedx_property_value(properties: list[dict], key: str) -> str | None:
    for prop in properties:
        if prop.get("name") == key:
            return prop.get("value")
    return None


def component_version_staleness_days(components: list[dict]) -> list[int]:
    result = []
    today = date.today()
    for component in components:
        properties = component.get("properties")
        if not properties:
            continue
        next_release_date = _find_cyclonedx_property_value(
            properties, "sigrid:next:releaseDate"
        )
        if next_release_date:
            try:
                result.append((today - date.fromisoformat(next_release_date)).days)
            except ValueError:
                continue
    return result


class OSHMetricsBase(ABC):
    """Base class for OSH (Open Source Health) metrics.

    Provides common metrics calculations for both system-level and portfolio-level OSH data.
    Subclasses must provide risk distribution properties and dependencies_count.
    """

    @cached_property
    def vulnerabilities_count(self) -> int:
        """Number of dependencies with vulnerabilities (critical to low)."""
        return sum(self.vulnerability_risk_distribution[0:4])

    @cached_property
    def vulnerabilities_fraction(self) -> float:
        if not self.vulnerabilities_count or not self.dependencies_count:
            return 0.0
        return max(self.vulnerabilities_count / self.dependencies_count, 0.01)

    @cached_property
    def outdated_count(self) -> int:
        """Number of outdated dependencies (critical to medium freshness risk)."""
        return sum(self.freshness_risk_distribution[0:3])

    @cached_property
    def outdated_fraction(self) -> float:
        if not self.outdated_count or not self.dependencies_count:
            return 0.0
        return max(self.outdated_count / self.dependencies_count, 0.01)

    @cached_property
    def legal_risk_count(self) -> int:
        """Number of dependencies with restrictive licenses (critical to medium)."""
        return sum(self.legal_risk_distribution[0:3])

    @cached_property
    def legal_risk_fraction(self) -> float:
        if not self.legal_risk_count or not self.dependencies_count:
            return 0.0
        return max(self.legal_risk_count / self.dependencies_count, 0.01)

    @cached_property
    def unmanaged_count(self) -> int:
        """Number of unmanaged dependencies (all risk levels)."""
        return sum(self.management_risk_distribution[0:4])

    @cached_property
    def unmanaged_fraction(self) -> float:
        if not self.unmanaged_count or not self.dependencies_count:
            return 0.0
        return max(self.unmanaged_count / self.dependencies_count, 0.01)

    @cached_property
    def activity_risk_count(self) -> int:
        """Number of dependencies with activity risks."""
        return sum(self.activity_risk_distribution[0:4])

    @cached_property
    def activity_risk_fraction(self) -> float:
        if not self.activity_risk_count or not self.dependencies_count:
            return 0.0
        return max(self.activity_risk_count / self.dependencies_count, 0.01)

    @cached_property
    def risk_distributions(self) -> dict[str, list[int]]:
        """Dictionary of all risk distributions for chart rendering."""
        return {
            "vulnerability": self.vulnerability_risk_distribution,
            "legal": self.legal_risk_distribution,
            "freshness": self.freshness_risk_distribution,
            "stability": self.stability_risk_distribution,
            "management": self.management_risk_distribution,
            "activity": self.activity_risk_distribution,
        }

    def _get_risk_value(self, properties: list, risk_name: str) -> int:
        """Return integer risk level (0=critical … 4=no_risk) for a single property name."""
        risk_mapping = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        for prop in properties:
            if prop.get("name") == risk_name:
                return risk_mapping.get(prop.get("value"), 4)
        return 4

    def _categorize_risk_level(self, risk_level: int, risk_counts: dict) -> None:
        """Increment the appropriate risk count based on the risk level."""
        risk_counts[_RISK_LABEL.get(risk_level, "no_risk")] += 1

    def _highest_risk_for_component(self, component: dict) -> int:
        """Return the highest (lowest integer) risk level across all OSH categories for a component."""
        props = component.get("properties", [])
        return min(self._get_risk_value(props, name) for name in _RISK_PROPERTY_NAMES)

    @property
    @abstractmethod
    def vulnerability_distribution(self) -> dict[str, int]: ...

    @property
    @abstractmethod
    def cves_mapped_to_libraries(self) -> dict[str, dict]: ...

    @property
    @abstractmethod
    def age_distribution(self) -> list[int]: ...

    @cached_property
    def exploit_probability(self) -> float:
        cves = self.cves_with_epss_scores
        product = 1.0
        for data in cves.values():
            if data["epss-score"] is not None:
                product *= (1 - data["epss-score"]) ** data["count"]
        return min(1 - product, 0.9999)

    @cached_property
    def cves_with_epss_scores(self) -> dict[str, dict]:
        cves = self.cves_mapped_to_libraries
        epss_scores = epss_data.epss_scores
        for cve_id, data in cves.items():
            data["epss-score"] = epss_scores.get(cve_id)
        return cves

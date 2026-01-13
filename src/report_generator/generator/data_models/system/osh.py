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
from datetime import datetime
from functools import cached_property, lru_cache
from typing import Union

from report_generator.generator import sigrid_api
from report_generator.generator.constants import MetricEnum, OSHMetric


class _AnonDataClass:
    def __init__(self):
        self.total_deps = 0

        self.date_day = ""
        self.date_month = ""
        self.date_year = ""

        self.ratings = {}

        # critical, high, medium, low, no risk
        self.vuln_risks = [0, 0, 0, 0, 0]
        self.license_risks = [0, 0, 0, 0, 0]
        self.freshness_risks = [0, 0, 0, 0, 0]
        self.stability_risks = [0, 0, 0, 0, 0]
        self.mgmt_risks = [0, 0, 0, 0, 0]
        self.activity_risks = [0, 0, 0, 0, 0]

        self.vulns = []

    @property
    def total_vulnerable(self):
        return sum(self.vuln_risks[0:4])

def _find_cyclonedx_property_value(properties, key):
    for prop in properties:
        if prop["name"] == key:
            return prop["value"]
    return None

class OSHData:

    @cached_property
    def raw_data(self):
        return sigrid_api.get_osh_findings()

    def _process_osh_data(self, raw_data):
        data = _AnonDataClass()

    @cached_property
    def system_rating(self) -> float:
        return self.get_rating_for_metric(_SystemMetric.SYSTEM)

            if data.date_year == "":
                (data.date_year, data.date_month, data.date_day) = self._format_date(raw_data["metadata"]["timestamp"])

            self._assign_risk(data.vuln_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:vulnerability"))
            self._assign_risk(data.license_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:legal"))
            self._assign_risk(data.freshness_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:freshness"))
            self._assign_risk(data.stability_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:stability"))
            self._assign_risk(data.mgmt_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:management"))
            self._assign_risk(data.activity_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:activity"))

        try:
            for prop in OSHMetric:
                data.ratings[prop.value.lower()] = self.get_rating_from_data(raw_data, prop.to_json_name())
        except KeyError:
            logging.warning("No OSH ratings found in API response. Not populating OSH ratings slide")

        return data

    @cached_property
    def data(self):
        return self._process_osh_data(self.raw_data)

    @staticmethod
    def get_rating_from_data(raw_data, rating_name):
        for prop in raw_data['metadata']['properties']:
            if prop["name"] == f"sigrid:ratings:{rating_name}":
                return float(prop["value"])

        logging.warning(f"OSH rating not found for property {metric.to_json_name()}")
        return 0.0

    @lru_cache
    def _get_risk_distribution_for_metric(self, metric: OSHMetric) -> list[int]:
        """Returns risk distribution as [critical, high, medium, low, no_risk] counts."""
        metric_key = metric.to_json_name()
        metric_key = "legal" if metric_key == "licenses" else metric_key  # Sigrid API uses "legal" only in risk context
        property_name = f"sigrid:risk:{metric_key}"

        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, None: 0}

        for component in self.raw_data.get("components", []):
            risk = _find_cyclonedx_property_value(component["properties"], property_name)
            risk_counts[risk if risk in risk_counts else None] += 1

        return [risk_counts["CRITICAL"], risk_counts["HIGH"], risk_counts["MEDIUM"], risk_counts["LOW"],
                risk_counts[None]]

    @cached_property
    def risk_distributions(self) -> dict[str, list[int]]:
        return {
            "vulnerability": self.vulnerability_risk_distribution,
            "legal"        : self.legal_risk_distribution,
            "freshness"    : self.freshness_risk_distribution,
            "stability"    : self.stability_risk_distribution,
            "management"   : self.management_risk_distribution,
            "activity"     : self.activity_risk_distribution,
        }

    @cached_property
    def vulnerability_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric(OSHMetric.VULNERABILITY)

    @cached_property
    def freshness_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric(OSHMetric.FRESHNESS)

    @cached_property
    def legal_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric(OSHMetric.LICENSES)

    @cached_property
    def stability_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric(OSHMetric.STABILITY)

    @cached_property
    def management_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric(OSHMetric.MANAGEMENT)

    @cached_property
    def activity_risk_distribution(self) -> list[int]:
        return self._get_risk_distribution_for_metric(OSHMetric.ACTIVITY)

    @cached_property
    def dependencies_count(self) -> int:
        return len(self.raw_data["components"])

    @cached_property
    def vulnerabilities_count(self) -> int:
        return sum(self.vulnerability_risk_distribution[0:4])

    @cached_property
    def vulnerabilities_fraction(self) -> float:
        if not self.vulnerabilities_count:
            return 0.0

        return max(self.vulnerabilities_count / self.dependencies_count, 0.01)

    @cached_property
    def outdated_count(self) -> int:
        return sum(
            self.freshness_risk_distribution[
                0:3])  # Only count critical to medium. Low is fresh enough to not report on

    @cached_property
    def outdated_fraction(self) -> float:
        if not self.outdated_count:
            return 0.0

        return max(self.outdated_count / self.dependencies_count, 0.01)

    @cached_property
    def legal_risk_count(self) -> int:
        return sum(self.legal_risk_distribution[
                       0:3])  # Only count critical to medium. Low license risk is typically not restrictive, so not interesting to report on

    @cached_property
    def legal_risk_fraction(self) -> float:
        if not self.legal_risk_count:
            return 0.0

        return max(self.legal_risk_count / self.dependencies_count, 0.01)

    @cached_property
    def unmanaged_count(self) -> int:
        return sum(self.management_risk_distribution[0:4])

    @cached_property
    def unmanaged_fraction(self) -> float:
        if not self.unmanaged_count:
            return 0.0

        return max(self.unmanaged_count / self.dependencies_count, 0.01)

    @cached_property
    def activity_risk_count(self) -> int:
        return sum(self.activity_risk_distribution[0:4])

    @cached_property
    def activity_risk_fraction(self) -> float:
        if not self.activity_risk_count:
            return 0.0

        return max(self.activity_risk_count / self.dependencies_count, 0.01)


osh_data = OSHData()

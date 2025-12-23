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
    total_deps = 0

    # critical, high, medium, low, no risk
    vuln_risks = [0, 0, 0, 0, 0]
    license_risks = [0, 0, 0, 0, 0]
    freshness_risks = [0, 0, 0, 0, 0]
    stability_risks = [0, 0, 0, 0, 0]
    mgmt_risks = [0, 0, 0, 0, 0]
    activity_risks = [0, 0, 0, 0, 0]


class _SystemMetric(MetricEnum):
    SYSTEM = "SYSTEM"


type OSHMetricOrSystem = Union[OSHMetric, _SystemMetric]

class OSHData:

    @cached_property
    def raw_data(self):
        return sigrid_api.get_osh_findings()

    @cached_property
    def data(self) -> _AnonDataClass:
        raw_data = self.raw_data
        data = _AnonDataClass()

        for component in raw_data.get("components", []):
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

        return data

    @cached_property
    def date(self) -> datetime:
        return datetime.strptime(self.raw_data["metadata"]["timestamp"], "%Y-%m-%dT%H:%M:%SZ")

    @cached_property
    def system_rating(self):
        return self.get_rating_for_metric(_SystemMetric.SYSTEM)

    @lru_cache
    def get_rating_for_metric(self, metric: OSHMetricOrSystem) -> float:
        for prop in self.raw_data['metadata']['properties']:
            if prop['name'] == f"sigrid:ratings:{metric.to_json_name()}":
                return float(prop["value"])

        logging.warning(f"OSH rating not found for property {metric.to_json_name()}")
        return 0.0

    @cached_property
    def dependencies_count(self):
        return len(self.raw_data["components"])

    @cached_property
    def vulnerabilities_count(self) -> int:
        return sum(self.data.vuln_risks[0:4])

    @cached_property
    def vulnerabilities_fraction(self) -> float:
        if not self.vulnerabilities_count:
            return 0.0

        return max(self.vulnerabilities_count / self.dependencies_count, 0.01)

    @cached_property
    def outdated_count(self) -> int:
        return sum(
            self.data.freshness_risks[0:3])  # Only count critical to medium. Low is fresh enough to not report on

    @cached_property
    def outdated_fraction(self) -> float:
        if not self.outdated_count:
            return 0.0

        return max(self.outdated_count / self.dependencies_count, 0.01)

    @cached_property
    def legal_risk_count(self) -> int:
        return sum(self.data.license_risks[
                       0:3])  # Only count critical to medium. Low license risk is typically not restrictive, so not interesting to report on

    @cached_property
    def legal_risk_fraction(self) -> float:
        if not self.legal_risk_count:
            return 0.0

        return max(self.legal_risk_count / self.dependencies_count, 0.01)

    @cached_property
    def unmanaged_count(self) -> int:
        return sum(self.data.mgmt_risks[0:4])

    @cached_property
    def unmanaged_fraction(self) -> float:
        if not self.unmanaged_count:
            return 0.0

        return max(self.unmanaged_count / self.dependencies_count, 0.01)

    @staticmethod
    def _assign_risk(values, risk):
        if risk == "CRITICAL":
            values[0] += 1
        elif risk == "HIGH":
            values[1] += 1
        elif risk == "MEDIUM":
            values[2] += 1
        elif risk == "LOW":
            values[3] += 1
        else:
            values[4] += 1

    @staticmethod
    def _find_cyclonedx_property_value(properties, key):
        for prop in properties:
            if prop["name"] == key:
                return prop["value"]
        return None


osh_data = OSHData()

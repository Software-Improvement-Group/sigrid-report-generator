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
from report_generator.generator.data_models.osh_base import OSHMetricsBase

OSH_DATA_NOT_FOUND_MSG = "Open Source Health not found for this system, skipping..."


class _SystemMetric(MetricEnum):
    SYSTEM = "SYSTEM"


OSHMetricOrSystem = Union[OSHMetric, _SystemMetric]


def _find_cyclonedx_property_value(properties, key):
    for prop in properties:
        if prop["name"] == key:
            return prop["value"]
    return None

class OSHData(OSHMetricsBase):

    def __init__(self):
        self._osh_warning_logged = False

    def _log_osh_warning_once(self):
        if not self._osh_warning_logged:
            logging.warning(OSH_DATA_NOT_FOUND_MSG)
            self._osh_warning_logged = True

    @cached_property
    def raw_data(self):
        return sigrid_api.get_osh_findings()

    @cached_property
    def date(self) -> datetime:
        try:
            return datetime.strptime(self.raw_data["metadata"]["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        except (KeyError, TypeError):
            self._log_osh_warning_once()
            return datetime.now()

    @cached_property
    def system_rating(self) -> float:
        return self.get_rating_for_metric(_SystemMetric.SYSTEM)

    @lru_cache
    def get_rating_for_metric(self, metric: OSHMetricOrSystem) -> float:
        try:
            for prop in self.raw_data['metadata']['properties']:
                if prop['name'] == f"sigrid:ratings:{metric.to_json_name()}":
                    return float(prop["value"])

            logging.warning(f"OSH rating not found for property {metric.to_json_name()}")
            return 0.0
        except KeyError:
            self._log_osh_warning_once()
            return 0.0

    @lru_cache
    def _get_risk_distribution_for_metric(self, metric: OSHMetric) -> list[int]:
        """Returns risk distribution as [critical, high, medium, low, no_risk] counts."""
        try:
            metric_key = metric.to_json_name()
            metric_key = "legal" if metric_key == "licenses" else metric_key  # Sigrid API uses "legal" only in risk context
            property_name = f"sigrid:risk:{metric_key}"

            risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, None: 0}

            for component in self.raw_data.get("components", []):
                risk = _find_cyclonedx_property_value(component["properties"], property_name)
                risk_counts[risk if risk in risk_counts else None] += 1

            return [risk_counts["CRITICAL"], risk_counts["HIGH"], risk_counts["MEDIUM"], risk_counts["LOW"],
                    risk_counts[None]]
        except (KeyError, TypeError):
            self._log_osh_warning_once()
            return [0, 0, 0, 0, 0]

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
        try:
            return len(self.raw_data["components"])
        except (KeyError, TypeError):
            self._log_osh_warning_once()
            return 0


osh_data = OSHData()
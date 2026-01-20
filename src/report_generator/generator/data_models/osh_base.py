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


class OSHMetricsBase:
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
        if not self.vulnerabilities_count:
            return 0.0
        return max(self.vulnerabilities_count / self.dependencies_count, 0.01)

    @cached_property
    def outdated_count(self) -> int:
        """Number of outdated dependencies (critical to medium freshness risk)."""
        return sum(self.freshness_risk_distribution[0:3])

    @cached_property
    def outdated_fraction(self) -> float:
        if not self.outdated_count:
            return 0.0
        return max(self.outdated_count / self.dependencies_count, 0.01)

    @cached_property
    def legal_risk_count(self) -> int:
        """Number of dependencies with restrictive licenses (critical to medium)."""
        return sum(self.legal_risk_distribution[0:3])

    @cached_property
    def legal_risk_fraction(self) -> float:
        if not self.legal_risk_count:
            return 0.0
        return max(self.legal_risk_count / self.dependencies_count, 0.01)

    @cached_property
    def unmanaged_count(self) -> int:
        """Number of unmanaged dependencies (all risk levels)."""
        return sum(self.management_risk_distribution[0:4])

    @cached_property
    def unmanaged_fraction(self) -> float:
        if not self.unmanaged_count:
            return 0.0
        return max(self.unmanaged_count / self.dependencies_count, 0.01)

    @cached_property
    def activity_risk_count(self) -> int:
        """Number of dependencies with activity risks."""
        return sum(self.activity_risk_distribution[0:4])

    @cached_property
    def activity_risk_fraction(self) -> float:
        if not self.activity_risk_count:
            return 0.0
        return max(self.activity_risk_count / self.dependencies_count, 0.01)

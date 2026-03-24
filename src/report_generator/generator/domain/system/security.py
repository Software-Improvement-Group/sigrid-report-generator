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

from report_generator.generator.context import sigrid_api


class SecurityData:
    @cached_property
    def findings(self) -> list:
        return sigrid_api.get_security_findings()

    def count_findings(self, severity) -> int:
        return sum(1 for finding in self.findings if finding["severity"] == severity)

    @cached_property
    def security_rating(self) -> float:
        ratings = sigrid_api.get_security_ratings()
        return ratings.get("rating")


security_data = SecurityData()

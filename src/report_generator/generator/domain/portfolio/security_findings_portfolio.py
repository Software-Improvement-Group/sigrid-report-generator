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

from functools import cached_property, lru_cache
from itertools import chain

from report_generator.generator.context import sigrid_api
from report_generator.generator.context.portfolio_metadata import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.maintainability_portfolio import (
    maintainability_portfolio_data,
)


class SecurityPortfolioFindings:
    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def data(self):
        return [
            {
                "systemName": system_name,
                "findings": sigrid_api.get_security_findings(system_name),
            }
            for system_name in maintainability_portfolio_data.system_names
        ]

    @cached_property
    def findings(self):
        return list(chain.from_iterable(entry["findings"] for entry in self.data))

    @lru_cache  # noqa: B019
    def count_findings(self, severity: str) -> int:
        return sum(1 for finding in self.findings if finding["severity"] == severity)


security_findings_portfolio_data = SecurityPortfolioFindings()

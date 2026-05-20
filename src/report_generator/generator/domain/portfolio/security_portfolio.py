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

from report_generator.generator.domain.portfolio.shared.findings_portfolio_base import (
    FindingsRatingsPortfolioBase,
)


class SecurityRatingsPortfolioData(FindingsRatingsPortfolioBase):
    _objective_type = "SECURITY_MAX_SEVERITY"
    _portfolio_ratings_api_method = "get_portfolio_security_ratings"
    _findings_api_method = "get_security_findings"

    @property
    def security_findings(self):
        return self._raw_findings


security_ratings_portfolio_data = SecurityRatingsPortfolioData()

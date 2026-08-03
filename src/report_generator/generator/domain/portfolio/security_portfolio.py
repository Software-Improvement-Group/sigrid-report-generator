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
from report_generator.generator.domain.portfolio.shared.ratings_change_base import (
    RatingsChangePortfolioBase,
)


class SecurityRatingsPortfolioData(
    FindingsRatingsPortfolioBase, RatingsChangePortfolioBase
):
    """Portfolio security ratings, both as-of the end of the reporting period (current state)
    and the per-system change over the period.

    The security ``model-ratings`` endpoint is point-in-time, so the change is obtained by also
    requesting the ratings at the start of the period (via the ``endDate`` parameter) and
    subtracting from the end-of-period ratings (``data``).
    """

    _objective_type = "SECURITY_MAX_SEVERITY"
    _portfolio_ratings_api_method = "get_portfolio_security_ratings"
    _findings_api_method = "get_security_findings"

    @property
    def security_findings(self):
        return self._raw_findings


security_ratings_portfolio_data = SecurityRatingsPortfolioData()

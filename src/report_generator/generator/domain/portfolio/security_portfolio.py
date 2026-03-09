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
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared import utils
from report_generator.generator.domain.portfolio.shared.rated_mixin import (
    RatedPortfolioMixin,
)


class SecurityRatingsPortfolioData(RatedPortfolioMixin):
    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="systemName")
    def data(self):
        return sigrid_api.get_portfolio_security_ratings()

    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]

    def get_system(self, system):
        return utils.get_system_helper(system, self.data, "systemName")

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data, "systemName")

    def _rated_systems(self):
        return self.data

    def _extract_rating(self, system):
        return system.get("rating")

    def _get_rating_and_volume(self, system):
        return utils.get_rating_and_volume_from_system(
            system, lambda s: s.get("rating"), "systemName"
        )


security_ratings_portfolio_data = SecurityRatingsPortfolioData()

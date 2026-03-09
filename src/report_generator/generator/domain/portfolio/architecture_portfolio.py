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


class ArchitecturePortfolioData(RatedPortfolioMixin):
    @cached_property
    @filter_data_on_portfolio_arguments(system_tag="system")
    def data(self):
        return sigrid_api.get_portfolio_architecture_findings()

    @cached_property
    def period(self):
        return None, sigrid_api.get_period()[1]

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data, "system")

    def get_system(self, system):
        return utils.get_system_helper(system, self.data, "system")

    def _rated_systems(self):
        return self.data

    def _extract_rating(self, system):
        if "ratings" not in system or "architecture" not in system["ratings"]:
            return None
        return system["ratings"]["architecture"]

    def _get_rating_and_volume(self, system):
        return utils.get_rating_and_volume_from_system(
            system, self._extract_rating, "system"
        )


architecture_portfolio_data = ArchitecturePortfolioData()

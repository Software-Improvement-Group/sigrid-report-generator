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
from typing import Optional

from report_generator.generator.domain.portfolio.shared import utils


class RatedPortfolioMixin:
    def _rated_systems(self):
        raise NotImplementedError

    def _extract_rating(self, item) -> Optional[float]:
        raise NotImplementedError

    def _get_rating_and_volume(self, item) -> tuple[Optional[float], float]:
        raise NotImplementedError

    @cached_property
    def weighted_average_rating(self) -> float:
        return utils.calculate_weighted_average_rating(
            self._rated_systems(), self._get_rating_and_volume
        )

    @cached_property
    def rating_distribution_percentages(self) -> dict:
        return utils.get_rating_distribution_percentages(
            self._rated_systems(), self._extract_rating
        )

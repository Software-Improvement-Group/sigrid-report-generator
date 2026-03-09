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
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Optional

from report_generator.generator.context import sigrid_api
from report_generator.generator.domain.portfolio.base import AbstractPortfolioModel
from report_generator.generator.domain.portfolio.maintainability_portfolio import (
    maintainability_portfolio_data,
)


def _finalize_change_statistics(statistics, lowest_system, highest_system):
    if lowest_system[0] is not None and lowest_system[1] < 0:
        statistics["lowest-system"] = {
            lowest_system[0]: int(lowest_system[1] * 10) / 10
        }
    if highest_system[0] is not None and highest_system[1] > 0:
        statistics["highest-system"] = {
            highest_system[0]: int(highest_system[1] * 10) / 10
        }


class _AbstractMaintainabilityDeltaQualityPortfolioData(AbstractPortfolioModel, ABC):
    @cached_property
    def data(self):
        result = {}
        t = self.get_type()
        for system in maintainability_portfolio_data.system_names:
            try:
                temp = sigrid_api.get_maintainability_delta_quality(system, t)
            except sigrid_api.SigridAPIRequestFailedError:
                temp = None
            except Exception as e:
                logging.error("Unexpected error in get_maintainability_delta_quality.")
                raise e
            result[system] = temp
        return result

    @abstractmethod
    def get_type(self):
        pass

    def get_system(self, system):
        return self.data.get(system)

    @cached_property
    def system_names(self):
        return list(self.data.keys())

    def _process_system_data(self, system_data, stats, lowest_system, highest_system):
        """Process a single system's data and update statistics."""
        rating = system_data.get("filesRatingAtEnd")
        if rating is not None:
            stats["total_rating"] += rating
            stats["count"] += 1
            return self._update_extremes(
                rating, stats["system_name"], lowest_system, highest_system
            )
        return lowest_system, highest_system

    def _update_extremes(self, rating, system_name, lowest_system, highest_system):
        """Update lowest and highest rating tracking."""
        if rating < lowest_system[1]:
            lowest_system = (system_name, rating)

        if rating > highest_system[1]:
            highest_system = (system_name, rating)

        return lowest_system, highest_system

    @cached_property
    def statistics(self):
        # TODO: expand average star rating when volume of new code is available
        """Calculate statistics for delta quality metrics.

        Returns:
            dict: Dictionary containing:
                - 'avg_stars': Average star rating (simple average for now)
                - 'lowest_system': Tuple of (system_name, rating) or None
                - 'highest_system': Tuple of (system_name, rating) or None
        """
        lowest_system: tuple[Optional[str], float] = (None, float("inf"))
        highest_system: tuple[Optional[str], float] = (None, float("-inf"))
        stats = {"total_rating": 0, "count": 0}

        for system_name in self.system_names:
            system_data = self.data.get(system_name)
            if system_data:
                stats["system_name"] = system_name
                lowest_system, highest_system = self._process_system_data(
                    system_data, stats, lowest_system, highest_system
                )

        if stats["count"] > 0:
            stats["avg_stars"] = stats["total_rating"] / stats["count"]
        else:
            stats["avg_stars"] = 0

        # Add lowest and highest systems to stats
        stats["lowest_system"] = lowest_system if lowest_system[0] is not None else None
        stats["highest_system"] = (
            highest_system if highest_system[0] is not None else None
        )

        logging.debug(
            f"Delta quality statistics: avg_stars={stats['avg_stars']}, count={stats['count']}, systems_processed={len([s for s in self.system_names if self.data.get(s)])}"
        )

        return stats


class MaintainabilityDeltaQualityNewCodePortfolioData(
    _AbstractMaintainabilityDeltaQualityPortfolioData
):
    def get_type(self):
        return "NEW_CODE"


class MaintainabilityDeltaQualityChangedCodePortfolioData(
    _AbstractMaintainabilityDeltaQualityPortfolioData
):
    def get_type(self):
        return "CHANGED_CODE"


class MaintainabilityDeltaQualityNewAndChangedCodePortfolioData(
    _AbstractMaintainabilityDeltaQualityPortfolioData
):
    def get_type(self):
        return "NEW_AND_CHANGED_CODE"


maintainability_delta_quality_new_code = (
    MaintainabilityDeltaQualityNewCodePortfolioData()
)
maintainability_delta_quality_changed_code = (
    MaintainabilityDeltaQualityChangedCodePortfolioData()
)
maintainability_delta_quality_new_and_changed_code = (
    MaintainabilityDeltaQualityNewAndChangedCodePortfolioData()
)

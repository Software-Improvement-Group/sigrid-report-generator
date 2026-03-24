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

from datetime import datetime
from functools import cached_property

from report_generator.generator.context import sigrid_api
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared import utils
from report_generator.generator.domain.portfolio.shared.rated_mixin import (
    RatedPortfolioMixin,
)


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def is_system_active(metadata):
    return metadata["active"] and not metadata["isDevelopmentOnly"]


class MaintainabilityPortfolioData(RatedPortfolioMixin):
    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()

    @property
    def period(self):
        return sigrid_api.get_period()

    @cached_property
    @filter_data_on_portfolio_arguments(data_tag="systems", system_tag="system")
    def data(self):
        data = sigrid_api.get_portfolio_maintainability()
        filtered_data = dict(data)
        filtered_data["systems"] = [
            system for system in data["systems"] if "maintainability" in system
        ]
        return filtered_data

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data["systems"], "system")

    def get_system(self, system):
        return utils.get_system_helper(system, self.data["systems"], "system")

    def get_system_metadata(self, system_name):
        return utils.get_system_metadata(self.metadata, system_name)

    @staticmethod
    def _get_head_entry(system):
        return {
            "maintainability": system["maintainability"],
            "componentBalance": system["componentBalance"],
            "componentIndependence": system["componentIndependence"],
            "componentEntanglement": system["componentEntanglement"],
            "duplication": system["duplication"],
            "moduleCoupling": system["moduleCoupling"],
            "testCodeRatio": system["testCodeRatio"],
            "unitComplexity": system["unitComplexity"],
            "unitInterfacing": system["unitInterfacing"],
            "unitSize": system["unitSize"],
            "volume": system["volume"],
            "volumeInPersonMonths": system["volumeInPersonMonths"],
            "volumeInLoc": system["volumeInLoc"],
            "maintainabilityDate": system["maintainabilityDate"],
        }

    @staticmethod
    def _get_snapshot_closest_to_date(date, snapshots):
        input_dt = datetime.strptime(date, "%Y-%m-%d")
        return min(
            snapshots,
            key=lambda x: abs(
                datetime.strptime(x["maintainabilityDate"], "%Y-%m-%d") - input_dt
            ),
        )

    @staticmethod
    def _return_closest_date(prime_date, date1, date2):
        input_dt = datetime.strptime(prime_date, "%Y-%m-%d")
        abs_date_1 = abs(
            datetime.strptime(date1["maintainabilityDate"], "%Y-%m-%d") - input_dt
        )
        abs_date_2 = abs(
            datetime.strptime(date2["maintainabilityDate"], "%Y-%m-%d") - input_dt
        )
        if abs_date_1 < abs_date_2:
            return date1
        else:
            return date2

    def get_closest_snapshot(self, system, snapshot_date, ignore_head_entry=False):
        s = self.get_system(system)
        head_entry = MaintainabilityPortfolioData._get_head_entry(s)
        if not s["allRatings"]:
            return head_entry
        snapshot = MaintainabilityPortfolioData._get_snapshot_closest_to_date(
            snapshot_date, s["allRatings"]
        )
        if ignore_head_entry:
            return snapshot
        snapshot = MaintainabilityPortfolioData._return_closest_date(
            snapshot_date, snapshot, head_entry
        )
        return snapshot

    def start_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[0], ignore_head_entry=True)

    def end_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[1])

    def _rated_systems(self):
        return self.system_names

    def _extract_rating(self, system_name):
        md = utils.get_system_metadata(self.metadata, system_name)
        if not is_system_active(md):
            return None
        end_snapshot = self.end_snapshot(system_name)
        return end_snapshot["maintainability"]

    def _get_rating_and_volume(self, system_name):
        md = utils.get_system_metadata(self.metadata, system_name)
        if not is_system_active(md):
            return None, 0

        end_snapshot = self.end_snapshot(system_name)
        rating = end_snapshot["maintainability"]
        volume = end_snapshot.get("volumeInPersonMonths", 0)
        return rating, volume

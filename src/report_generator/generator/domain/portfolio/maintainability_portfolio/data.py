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

from report_generator.generator.context import config, sigrid_api
from report_generator.generator.context.portfolio_metadata import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared import utils
from report_generator.generator.domain.portfolio.shared.rated_mixin import (
    RatedPortfolioMixin,
)


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def existed_at_end_date(system, end_date):
    end_dt = parse_date(end_date)
    dates = [r["maintainabilityDate"] for r in system.get("allRatings", [])]
    dates.append(system["maintainabilityDate"])  # head entry date
    return any(parse_date(d) <= end_dt for d in dates)


class MaintainabilityPortfolioData(RatedPortfolioMixin):
    @property
    def customer(self) -> str:
        return config.get_customer()

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
        end_date = self.period[1]
        filtered_data = dict(data)
        filtered_data["systems"] = [
            system
            for system in data["systems"]
            if "maintainability" in system and existed_at_end_date(system, end_date)
        ]
        return filtered_data

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data["systems"], "system")

    def get_system(self, system):
        return utils.get_system_helper(system, self.data["systems"], "system")

    def get_system_metadata(self, system_name):
        return utils.get_system_metadata(self.metadata, system_name)

    def get_system_display_name(self, system_name: str) -> str:
        md = self.get_system_metadata(system_name)
        if md is None:
            return system_name
        return md.get("displayName") or system_name

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
            "volume": system.get("volume"),
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
        if s is None:
            return None
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

    def get_property_rating(self, system_name: str, metric_key: str):
        snapshot = self.end_snapshot(system_name)
        return snapshot.get(metric_key) if snapshot else None

    def _rating_for_metric(self, system_name, metric_key):
        return self.get_property_rating(system_name, metric_key)

    def _rating_and_volume_for_metric(self, system_name, metric_key):
        end_snapshot = self.end_snapshot(system_name)
        return end_snapshot.get(metric_key), end_snapshot.get("volumeInPersonMonths", 0)

    def _extract_rating(self, system_name):
        return self._rating_for_metric(system_name, "maintainability")

    def _get_rating_and_volume(self, system_name):
        return self._rating_and_volume_for_metric(system_name, "maintainability")

    def weighted_average_rating_for_metric(self, metric_key: str) -> float:
        return utils.calculate_weighted_average_rating(
            self._rated_systems(),
            lambda system_name: self._rating_and_volume_for_metric(
                system_name, metric_key
            ),
        )

    def rating_distribution_percentages_for_metric(self, metric_key: str) -> dict:
        return utils.get_rating_distribution_percentages(
            self._rated_systems(),
            lambda system_name: self._rating_for_metric(system_name, metric_key),
        )

    def _build_rating_entry(self, system_name: str) -> dict | None:
        snapshot = self.end_snapshot(system_name)
        if snapshot is None:
            return None
        return {
            "systemName": system_name,
            "displayName": self.get_system_display_name(system_name),
            "rating": snapshot["maintainability"],
            "volume_py": round(snapshot.get("volumeInPersonMonths", 0) / 12.0, 1),
        }

    @cached_property
    def bottom_systems_by_maintainability_rating(self) -> list[dict]:
        entries = [
            entry
            for system_name in self.system_names
            if (entry := self._build_rating_entry(system_name)) is not None
        ]
        entries.sort(key=lambda e: e["rating"])
        return entries

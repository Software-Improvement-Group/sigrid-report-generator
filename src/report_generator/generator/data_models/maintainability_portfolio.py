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
from typing import Tuple, Optional

from report_generator.generator import sigrid_api
from report_generator.generator.formatters.formatters import calculate_star_rating_integer

from .base import BasePortfolioModel

class MaintainabilityPortfolioData(BasePortfolioModel):
    @cached_property
    def data(self):
        data = sigrid_api.get_portfolio_maintainability()
        filtered_data = data
        filtered_data['systems'] = [system for system in data['systems'] if 'maintainability' in system]
        return filtered_data
    
    @cached_property
    def system_names(self):
        return BasePortfolioModel._system_names_helper(self.data['systems'], 'system')
    
    def _find_system(self, system):
        return BasePortfolioModel._find_system_helper(system, self.data['systems'], 'system')
    
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
                "maintainabilityDate": system["maintainabilityDate"]
            }
    
    @staticmethod
    def _get_snapshot_closest_to_date(date, snapshots):
        input_dt = datetime.strptime(date, "%Y-%m-%d")
        return min(
            snapshots,
            key=lambda x: abs(datetime.strptime(x["maintainabilityDate"], "%Y-%m-%d") - input_dt)
        )
    
    @staticmethod
    def _return_closest_date(prime_date, date1, date2):
        input_dt = datetime.strptime(prime_date, "%Y-%m-%d")
        abs_date_1 = abs(datetime.strptime(date1["maintainabilityDate"], "%Y-%m-%d") - input_dt)
        abs_date_2 = abs(datetime.strptime(date2["maintainabilityDate"], "%Y-%m-%d") - input_dt)
        if abs_date_1 < abs_date_2:
            return date1
        else:
            return date2

    def get_closest_snapshot(self, system, snapshot_date, ignore_head_entry=False):
        s = self._find_system(system)
        head_entry = MaintainabilityPortfolioData._get_head_entry(s)
        if not s['allRatings']:
            return head_entry
        snapshot = MaintainabilityPortfolioData._get_snapshot_closest_to_date(snapshot_date, s['allRatings'])
        if ignore_head_entry:
            return snapshot
        snapshot = MaintainabilityPortfolioData._return_closest_date(snapshot_date, snapshot, head_entry)
        return snapshot

    def start_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[0], ignore_head_entry=True)

    def end_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[1])
    
    def get_statistics(self):
        statistics = {
            'maintainability' : {'1-star' : 0, '2-star' : 0, '3-star' : 0, '4-star' : 0, '5-star' : 0, 'number-of-systems' : 0},
            'maintainability-change' : {'increase' : {}, 'decrease' : {}}
        }
        period_start = MaintainabilityPortfolioData._parse_date(maintainability_portfolio_data.period[0])
        best_inc: Tuple[Optional[str], float] = (None, float("-inf"))
        best_dec: Tuple[Optional[str], float] = (None, float("inf"))
        start_maintainability_ratings, end_maintainability_ratings = [], []
        start_volumes, end_volumes = [], []

        for system_name in self.system_names:
            md = self.find_system_metadata(system_name)
            if not md['active'] or md['isDevelopmentOnly']:
                continue
            start_snapshot = maintainability_portfolio_data.start_snapshot(system_name)
            end_snapshot = maintainability_portfolio_data.end_snapshot(system_name)
            start_date = MaintainabilityPortfolioData._parse_date(start_snapshot["maintainabilityDate"])
            end_date = MaintainabilityPortfolioData._parse_date(end_snapshot["maintainabilityDate"])

            # Star-related statistics
            star_rating_integer = calculate_star_rating_integer(end_snapshot['maintainability'])
            statistics['maintainability'][f"{star_rating_integer}-star"] += 1
            statistics['maintainability']['number-of-systems'] += 1
            
            # Change in maintainability
            if start_date != end_date and start_date >= period_start:
                diff = end_snapshot["maintainability"] - start_snapshot["maintainability"]
                if diff > best_inc[1]:
                    best_inc = (system_name, diff)
                if diff < best_dec[1]:
                    best_dec = (system_name, diff)
            
            # Averages
            if start_date < period_start:
                start_maintainability_ratings.append(start_snapshot['maintainability'])
                start_volumes.append(start_snapshot['volumeInPersonMonths'])
            end_maintainability_ratings.append(end_snapshot['maintainability'])
            end_volumes.append(end_snapshot['volumeInPersonMonths'])

        # Largest increase/decrease
        if best_dec[0] is not None and best_dec[1] < 0:
            # noinspection PyTypeChecker - Weirdness
            statistics["maintainability-change"]["decrease"] = {best_dec[0]: best_dec[1]}
        if best_inc[0] is not None and best_inc[1] > 0:
            # noinspection PyTypeChecker - Weirdness
            statistics["maintainability-change"]["increase"] = {best_inc[0]: best_inc[1]}
        
        statistics['maintainability']['start-average'] = MaintainabilityPortfolioData._weighted_avg(start_maintainability_ratings, start_volumes)
        statistics['maintainability']['end-average'] = MaintainabilityPortfolioData._weighted_avg(end_maintainability_ratings, end_volumes)
        return statistics

    @staticmethod
    def _parse_date(s):
        return datetime.strptime(s, "%Y-%m-%d")

    @staticmethod
    def _weighted_avg(values, weights):
        tw = sum(weights)
        return (sum(v * w for v, w in zip(values, weights)) / tw) if tw else 0.000001

maintainability_portfolio_data = MaintainabilityPortfolioData()
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

from report_generator.generator import sigrid_api
from .security_dashboard_findings_portfolio import _filter_systems_based_on_metadata

class MaintainabilityPortfolioData:
    @cached_property
    def data(self):
        data = sigrid_api.get_portfolio_maintainability()
        filtered_data = data
        filtered_data['systems'] = [system for system in data['systems'] if 'maintainability' in system]
        return _filter_systems_based_on_metadata(filtered_data)
    
    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()
    
    @cached_property
    def period(self):
        return sigrid_api.get_period()

    @cached_property
    def system_names(self):
        return [x['system'] for x in self.data['systems']]
    
    def _find_system(self, system):
        for s in self.data['systems']:
            if s['system'] == system:
                return s
        return None
    
    def find_system_metadata(self, system):
        for s in self.metadata:
            if s['systemName'] == system:
                return s
        return None

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
    
maintainability_portfolio_data = MaintainabilityPortfolioData()
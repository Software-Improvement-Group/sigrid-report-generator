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


def _sort_and_aggregate_technology_data(tech_data):
    sorted_tech_data = sorted(tech_data, key=lambda d: d['volumeInPersonMonths'], reverse=True)
    sorted_and_filtered_tech_data = list(filter(lambda d: d['volumeInPersonMonths'] > 0.0, sorted_tech_data))

    if (len(sorted_and_filtered_tech_data)) > 5:
        pm_sum = sum([d['volumeInPersonMonths'] for d in sorted_and_filtered_tech_data[4:]])
        loc_sum = sum([d['volumeInLoc'] for d in sorted_and_filtered_tech_data[4:]])
        # Maintainability and test code ratio are weighted by volume in person month
        maint_aggregate = sum([d['maintainability'] * (d['volumeInPersonMonths'] / pm_sum) for d in
                               sorted_and_filtered_tech_data[4:]])
        test_code_aggregate = sum([d['testCodeRatio'] * (d['volumeInPersonMonths'] / pm_sum) for d in
                                   sorted_and_filtered_tech_data[4:]])
        # technology risk aggregate is the worst individual rating
        tech_risk_aggregate = _worst_tech_risk([d['technologyRisk'] for d in sorted_and_filtered_tech_data[4:]])
        small_technologies_aggregate = {"name"                : "others", "displayName": "Others",
                                        "volumeInPersonMonths": pm_sum,
                                        "volumeInLoc"         : loc_sum, "maintainability": maint_aggregate,
                                        "testCodeRatio"       : test_code_aggregate,
                                        "technologyRisk"      : tech_risk_aggregate}
        sorted_and_filtered_tech_data = sorted_and_filtered_tech_data[0:4] + [small_technologies_aggregate]
    return sorted_and_filtered_tech_data


def _worst_tech_risk(risks):
    if "PHASEOUT" in risks:
        return "PHASEOUT"
    elif "TOLERATE" in risks:
        return "TOLERATE"
    else:
        return "TARGET"


class MaintainabilityData:
    @cached_property
    def data(self):
        return sigrid_api.get_maintainability_ratings()

    @cached_property
    def period(self):
        return sigrid_api.get_period()

    @cached_property
    def maintainability_rating(self):
        return self.data['maintainability']

    @cached_property
    def date(self):
        return datetime.strptime(self.data["maintainabilityDate"], '%Y-%m-%d')

    @cached_property
    def tech(self):
        return self.data['technologies']

    @cached_property
    def sorted_tech(self):
        return _sort_and_aggregate_technology_data(self.tech)

    def sorted_tech_get_key(self, index, key, default=""):
        if index >= len(self.sorted_tech):
            return default

        return self.sorted_tech[index].get(key, default)

    @cached_property
    def tech_total_volume_pm(self):
        return sum([d["volumeInPersonMonths"] for d in self.sorted_tech])

    @cached_property
    def tech_target_ratio(self):
        def target_ratio_for_technology(risk_level, volume_percentage):
            if risk_level == "TARGET":
                return volume_percentage
            elif risk_level == "TOLERATE":
                return 0.5 * volume_percentage
            else:
                return 0

        return sum(
            [target_ratio_for_technology(d['technologyRisk'], d["volumeInPersonMonths"] / self.tech_total_volume_pm) for
             d in self.tech])

    @cached_property
    def tech_phaseout_ratio(self):
        return sum([d["volumeInPersonMonths"] for d in self.tech if
                    d["technologyRisk"] == "PHASEOUT"]) / self.tech_total_volume_pm

    @cached_property
    def tech_phaseout_technologies(self):
        return [d["displayName"] for d in self.tech if d["technologyRisk"] == "PHASEOUT"]

    @cached_property
    def system_py(self):
        return round(self.data["volumeInPersonMonths"] / 12.0, 1)

    @cached_property
    def system_pm(self):
        return round(self.maintainability_rating["volumeInPersonMonths"], 1)

    @cached_property
    def system_loc(self):
        return self.data.get("volumeInLoc", None)

    @cached_property
    def system_name(self):
        name = self.data["system"]
        return name.upper() if len(name) <= 3 else name.capitalize()

    @cached_property
    def customer_name(self):
        return self.data['customer'].capitalize()

    @cached_property
    def start_snapshot(self):
        snapshots = list(self.snapshots_in_period)
        if len(snapshots) == 0:
            raise Exception(f"There is no usable start snapshot in the reporting period: {self.period}")
        return snapshots[0]

    @cached_property
    def snapshots_in_period(self):
        period_start_date = datetime.strptime(self.period[0], "%Y-%m-%d")
        period_end_date = datetime.strptime(self.period[1], "%Y-%m-%d")

        for snapshot in reversed(self.data["allRatings"]):
            snapshot_date = datetime.strptime(snapshot["maintainabilityDate"], "%Y-%m-%d")
            if snapshot_date >= period_start_date and snapshot_date <= period_end_date:
                yield snapshot


maintainability_data = MaintainabilityData()

class MaintainabilityPortfolioData:
    @cached_property
    def data(self):
        return sigrid_api.get_portfolio_maintainability()
    
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
    
    def find_system_metadata(self, system):
        for s in self.metadata:
            if s['systemName'] == system:
                return s

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
    
    def _get_snapshot_closest_to_date(date, snapshots):
        input_dt = datetime.strptime(date, "%Y-%m-%d")
        return min(
            snapshots,
            key=lambda x: abs(datetime.strptime(x["maintainabilityDate"], "%Y-%m-%d") - input_dt)
        )
    
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
        snapshot = MaintainabilityPortfolioData._get_snapshot_closest_to_date(snapshot_date, s['allRatings'])
        if ignore_head_entry:
            return snapshot
        head_entry = MaintainabilityPortfolioData._get_head_entry(s)
        snapshot = MaintainabilityPortfolioData._return_closest_date(snapshot_date, snapshot, head_entry)
        return snapshot

    def start_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[0], ignore_head_entry=True)

    def end_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[1])
    
maintainability_portfolio_data = MaintainabilityPortfolioData()
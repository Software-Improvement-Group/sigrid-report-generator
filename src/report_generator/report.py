# Copyright Software Improvement Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import ABC, abstractmethod
import math, logging
from datetime import datetime

from .sigrid_api import SigridAPI
from .smart_remarks import SmartRemarks
from .static_data import StaticData
from .generic_utils import GenericUtils
from .osh_report import OSHReport, OSHData

# The Report class defines an interface for, and contains generic logic intended to be used by all/most specific report types
class Report(ABC):
    
    def __init__(self, customer, system, token):
        self.customer = customer
        self.system = system
        self.token = token
        self.sigridAPI = SigridAPI(self.token)

    def create(self):
        self.generate_date()
        logging.info("Fetching maintainability data from API")
        self.create_maintainability()
        logging.info("Done generating maintainability section of report")

        logging.info("Fetching architecture quality data from API")
        self.create_architecture_quality()
        logging.info("Done generating architecture quality section of report")

        logging.info("Fetching OSH data from API")
        self.create_osh()
        logging.info("Done generating OSH section of report")

        self.save_file()

    
    def generate_date(self):
        self.update_placeholder("REPORT_DATE", datetime.now().strftime("%B %d, %Y"))

    @abstractmethod
    def create_maintainability_report_specific(self, data):
        pass

    @abstractmethod
    def create_architecture_quality_report_specific(self, data):
        pass

    @abstractmethod
    def create_osh_report_specific(self, data: OSHData, report: OSHReport):
        pass

    @abstractmethod
    def create_technology_report_specific(self, tech_data, sorted_tech_data):
        pass

    @abstractmethod
    def update_placeholder(self, placeholder, replacement_text):
        pass

    @abstractmethod
    def save_file(self):
        pass


    @abstractmethod
    def fill_metric_report_specific(self, model, metric, rating):
        pass

    def fill_metric(self, model, metric, rating):
        logging.debug(f"filling metric {metric} with {rating}")
        
        self.fill_metric_report_specific(model, metric, rating)
        
        self.update_placeholder("COLOR_" + model + "_RATING_" + metric, Report.maintainability_round(rating))

        self.update_placeholder(model + "_RATING_" + metric, Report.maintainability_round(rating))
        self.update_placeholder("STARS_" + metric, Report.calculate_stars(rating))

    def create_maintainability(self):
        maint_data = self.sigridAPI.get_maintainability_ratings_for_customer_system(self.customer, self.system, True)

        self.create_maintainability_report_specific(maint_data)
        for metric in StaticData.maint_metrics:
            self.fill_metric("MAINT", metric, maint_data[GenericUtils.to_json_name(metric)])

        self.update_placeholder("MAINT_RATING", Report.maintainability_round(maint_data["maintainability"]))
        self.update_placeholder("MAINT_STARS", Report.calculate_stars(maint_data["maintainability"]))
        self.update_placeholder("MAINT_RELATIVE", SmartRemarks.relative_to_market_average(maint_data["maintainability"]))
        self.update_placeholder("MAINT_INDICATION", SmartRemarks.relative_cost(maint_data["maintainability"]))
        self.update_placeholder("MAINT_OBSERVATION", SmartRemarks.maint_observation(maint_data))
        self.update_placeholder("MAINT_MULTIPLE_OBSERVATIONS", SmartRemarks.maint_observations(maint_data))

        self.update_placeholder("SYSTEM_NAME", maint_data["system"].capitalize())
        self.update_placeholder("CUSTOMER_NAME", maint_data["customer"].capitalize())

        date = datetime.strptime(maint_data["maintainabilityDate"], '%Y-%m-%d')
        self.update_placeholder("MAINT_DATE_DAY", date.strftime("%d"))
        self.update_placeholder("MAINT_DATE_MONTH", date.strftime("%b"))
        self.update_placeholder("MAINT_DATE_YEAR", date.strftime("%Y"))
        self.update_placeholder("MAINT_SIZE", Report.calculate_volume_indicator(maint_data["volume"]))
        self.update_placeholder("TEST_CODE_RATIO", format(maint_data["testCodeRatio"], ".0%"))
        self.update_placeholder("TEST_CODE_RELATIVE", SmartRemarks.test_code_relative(maint_data["testCodeRatio"]));
        self.update_placeholder("TEST_CODE_SUMMARY", SmartRemarks.test_code_summary(maint_data["testCodeRatio"]));

        self.update_placeholder("SYSTEM_PM", round(maint_data["volumeInPersonMonths"], 1))
        self.update_placeholder("SYSTEM_PY", round(maint_data["volumeInPersonMonths"] / 12.0, 1))
        self.update_placeholder("SYSTEM_LOC", maint_data["volumeInLoc"])
        self.update_placeholder("SYSTEM_LOC_FORMAT_LOCALE", f"{maint_data['volumeInLoc']:n}")
        self.update_placeholder("SYSTEM_LOC_FORMAT_COMMA", f"{maint_data['volumeInLoc']:,}")
        self.update_placeholder("SYSTEM_LOC_FORMAT_DOT", f"{maint_data['volumeInLoc']:,}".replace(",", "."))

        self.update_placeholder("VOLUME_RELATIVE", SmartRemarks.relative_volume(maint_data["volume"]))
        self.fill_technologies(maint_data["technologies"])

    def fill_technologies(self, tech_data):
        sorted_tech_data = Report.sort_and_aggregate_technology_data(tech_data)
        self.create_technology_report_specific(tech_data, sorted_tech_data)
        total_volume_pm = sum([data["volumeInPersonMonths"] for data in sorted_tech_data])

        # Note that target_ratio uses tech_data and not sorted_tech_data because during sorting we lose 
        # some information on technology risk
        target_ratio = sum([Report.target_ratio_for_technology(data['technologyRisk'], data["volumeInPersonMonths"] / total_volume_pm) for data in tech_data])
        phaseout_ratio = sum([data["volumeInPersonMonths"] for data in tech_data if data["technologyRisk"] == "PHASEOUT"])  / total_volume_pm
        phaseout_technologies = [data["displayName"] for data in tech_data if data["technologyRisk"] == "PHASEOUT"]
        self.update_placeholder("TECH_COMMON_SUMMARY", SmartRemarks.technology_summary(target_ratio, phaseout_ratio, phaseout_technologies))
        self.update_placeholder("TECH_VARIANCE", SmartRemarks.tech_variance_remark(sorted_tech_data, total_volume_pm))
        self.update_placeholder("TECH_SUMMARY", SmartRemarks.technology_summary(target_ratio, phaseout_ratio, phaseout_technologies))
        
        i = 1
        for tech in sorted_tech_data:
            self.update_placeholder(f"TECH_{i}_NAME", tech['displayName'])
            self.update_placeholder(f"TECH_{i}_PY", round(tech['volumeInPersonMonths'] / 12, 1))
            self.update_placeholder(f"TECH_{i}_PY", round(tech['volumeInPersonMonths'], 1))
            self.update_placeholder(f"TECH_{i}_LOC", tech['volumeInLoc'])
            self.update_placeholder(f"TECH_{i}_MAINT_RATING", tech['maintainability'])
            self.update_placeholder(f"TECH_{i}_TEST_RATIO", tech['testCodeRatio'])
            self.update_placeholder(f"TECH_{i}_TECH_RISK", tech['technologyRisk'])
            i +=1
        if i < 6:
            for j in range(i, 6):
                self.update_placeholder(f"TECH_{j}_NAME", "")
                self.update_placeholder(f"TECH_{j}_PY", "")
                self.update_placeholder(f"TECH_{j}_LOC", "")
                self.update_placeholder(f"TECH_{j}_MAINT_RATING", "")
                self.update_placeholder(f"TECH_{j}_TEST_RATIO", "")
                self.update_placeholder(f"TECH_{j}_TECH_RISK", "")
    
    def target_ratio_for_technology(risk_level, volume_percentage):
        if risk_level == "TARGET":
            return volume_percentage
        elif risk_level == "TOLERATE":
            return 0.5 * volume_percentage
        else:
            return 0
        
    def create_architecture_quality(self):
        architecture_data = self.sigridAPI.get_architecture_findings_for_customer_system(self.customer, self.system)
        self.create_architecture_quality_report_specific(architecture_data)

        date = datetime.strptime(architecture_data["analysisDate"], '%Y-%m-%d')
        self.update_placeholder("ARCH_DATE_DAY", date.strftime("%d"))
        self.update_placeholder("ARCH_DATE_MONTH", date.strftime("%b"))
        self.update_placeholder("ARCH_DATE_YEAR", date.strftime("%Y"))

        for metric in StaticData.arch_metrics:
            self.fill_metric("ARCH", metric, architecture_data["ratings"]["systemProperties"][GenericUtils.to_json_name(metric)])
        
        for metric in StaticData.arch_subcharacteristics:
            self.fill_metric("ARCH", metric, architecture_data["ratings"]["subcharacteristics"][GenericUtils.to_json_name(metric)])


        self.update_placeholder("ARCH_RATING", Report.maintainability_round(architecture_data["ratings"]["architecture"]))
        self.update_placeholder("ARCH_MODEL_VERSION", architecture_data["modelVersion"])
        self.update_placeholder("ARCH_STARS", Report.calculate_stars(architecture_data["ratings"]["architecture"]))
        self.update_placeholder("ARCH_AT_BELOW", SmartRemarks.relative_to_market_average(architecture_data["ratings"]["architecture"]))
        self.update_placeholder("ARCH_OBSERVATION", SmartRemarks.arch_observation(architecture_data["ratings"]["architecture"]))
        self.update_placeholder("ARCH_WORST_METRIC_REMARK", SmartRemarks.arch_worst_metric_remark(architecture_data["ratings"]["systemProperties"]))
        self.update_placeholder("ARCH_BEST_METRIC_REMARK", SmartRemarks.arch_best_metric_remark(architecture_data["ratings"]["systemProperties"]))

    def create_osh(self):
        osh_json_data = self.sigridAPI.get_osh_findings_for_customer_system(self.customer, self.system)
        osh_report = OSHReport()
        osh_data = osh_report.aggregate_data(osh_json_data)


        self.update_placeholder("OSH_RISK_SUMMARY", SmartRemarks.osh_remark(osh_json_data))
        self.update_placeholder("OSH_TOTAL_DEPS", osh_data.total_deps)
        self.update_placeholder("OSH_TOTAL_VULN", osh_data.total_vulnerable())
        self.update_placeholder("OSH_DATE_DAY", osh_data.date_day)
        self.update_placeholder("OSH_DATE_MONTH", osh_data.date_month)
        self.update_placeholder("OSH_DATE_YEAR", osh_data.date_year)
        self.update_placeholder("OSH_VULN_SUMMARY", OSHReport.vulnerability_summary(osh_data))
        self.update_placeholder("OSH_FRESHNESS_SUMMARY", OSHReport.freshness_summary(osh_data))
        self.update_placeholder("OSH_LEGAL_SUMMARY", OSHReport.legal_summary(osh_data))
        self.update_placeholder("OSH_MANAGEMENT_SUMMARY", OSHReport.management_summary(osh_data))
        
        self.create_osh_report_specific(osh_data, osh_report)
    
    def test_sigrid_token(token):
        if len(token) < 10 or token[0:2] != "ey":
            raise Exception("Invalid Sigrid token. A token is always longer than 10 characters and starts with 'ey'. You can obtain a token from sigrid-says.com. Note that tokens are customer-specific.")
        
    def maintainability_round(rating):
        if rating < 0.1:
            return "N/A"
        else:
            return math.floor(rating * 10) / 10
    
    def calculate_stars(maintainability_rating):
        if maintainability_rating < 0.1:
            return ""
        elif maintainability_rating < 1.5:
            return "★☆☆☆☆"
        elif maintainability_rating < 2.5:
            return "★★☆☆☆"
        elif maintainability_rating < 3.5:
            return "★★★☆☆"
        elif maintainability_rating < 4.5:
            return "★★★★☆"
        else:
            return "★★★★★"

    def calculate_volume_indicator(volume_rating):
        if volume_rating < 1.5:
            return "very large"
        elif volume_rating < 2.5:
            return "large"
        elif volume_rating < 3.5:
            return "medium-sized"
        elif volume_rating < 4.5:
            return "small"
        else:
            return "very small"
    

    def sort_and_aggregate_technology_data(tech_data):
        sorted_tech_data = sorted(tech_data, key=lambda d: d['volumeInPersonMonths'], reverse=True)
        sorted_and_filtered_tech_data = list(filter(lambda d: d['volumeInPersonMonths'] > 0.0, sorted_tech_data))

        if(len(sorted_and_filtered_tech_data)) > 5:
            pmSum = sum([data['volumeInPersonMonths'] for data in sorted_and_filtered_tech_data[4:]])
            locSum = sum([data['volumeInLoc'] for data in sorted_and_filtered_tech_data[4:]])
            # Maintainability and test code ratio are weighted by volume in person month
            maintAggregate = sum([data['maintainability'] * (data['volumeInPersonMonths'] / pmSum) for data in sorted_and_filtered_tech_data[4:]])
            testCodeAggregate = sum([data['testCodeRatio'] * (data['volumeInPersonMonths'] / pmSum) for data in sorted_and_filtered_tech_data[4:]])
            #technology risk aggregate is the worst individual rating
            techRiskAggregate = Report.worstTechRisk([data['technologyRisk'] for data in sorted_and_filtered_tech_data[4:]])
            small_technologies_aggregate = {"name": "others", "displayName": "Others", "volumeInPersonMonths": pmSum, "volumeInLoc": locSum, "maintainability": maintAggregate, "testCodeRatio": testCodeAggregate, "technologyRisk": techRiskAggregate}
            sorted_and_filtered_tech_data = sorted_and_filtered_tech_data[0:4] + [small_technologies_aggregate]
        return sorted_and_filtered_tech_data
    
    def worstTechRisk(risks):
        if "PHASEOUT" in risks:
            return "PHASEOUT"
        elif "TOLERATE" in risks:
            return "TOLERATE"
        else:
            return "TARGET"
    

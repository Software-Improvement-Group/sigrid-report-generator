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

from .static_data import StaticData
from .generic_utils import GenericUtils

"""
This is an old-fashioned implementation of us automatically trying to give smart observations about code.
It is isolated in this class so it can be potentially replaced by a smarter solution. Dare I say AI?
"""
class SmartRemarks:

    def relative_to_market_average(rating):
        if rating < 2.5:
            return "below"
        elif rating >= 3.5:
            return "above"
        else:
            return "at"
        
    def relative_cost(rating):
        if rating < 2.5:
            return "above average"
        elif rating >= 3.5:
            return "below average"
        else:
            return "average"
        
    def relative_volume(volume_rating):
        if volume_rating < 1.5:
            return "very large"
        elif volume_rating < 2.5:
            return "large"
        elif volume_rating < 3.5:
            return "average"
        elif volume_rating < 4.5:
            return "small"
        else:
            return "very small"

        
    # Figure out what the lowest scoring metrics are, and say something intelligent about those
    def maint_observation(maintainability_data):
        sorted_metric_data = SmartRemarks.sort_metrics(maintainability_data, StaticData.maint_metrics)

        worst_metric = sorted_metric_data[0]
        if worst_metric[1] < 2.5:
            return SmartRemarks.worst_metric_observation(worst_metric)


    def maint_observations(maintainability_data):
        sorted_metric_data = SmartRemarks.sort_metrics(maintainability_data, StaticData.maint_metrics)
        res = ""
        for sorted_metric in sorted_metric_data:
            if sorted_metric[1] < 2.5:
                res = res + SmartRemarks.worst_metric_observation(sorted_metric)
                res = res + "\n"
            if sorted_metric[1] > 3.5:
                res = res + SmartRemarks.best_metric_observation(sorted_metric)
                res = res + "\n"
        return res

    def best_metric_observation(best_metric):
        if best_metric[0] == "VOLUME":
            return "The system is small and therefore easier to maintain."
        if best_metric[0] == "DUPLICATION":
            return "The system shows low risk in its duplicated logic."
        if best_metric[0] == "UNIT_SIZE":
            return "The system shows low risk in unit sizing"
        if best_metric[0] == "UNIT_COMPLEXITY":
            return "The system shows low risk in unit complexity."
        if best_metric[0] == "UNIT_INTERFACING":
            return "The system shows low risk in unit interfacing"
        if best_metric[0] == "MODULE_COUPLING":
            return "The system shows loose coupling across modules"
        if best_metric[0] == "COMPONENT_INDEPENDENCE":
            return "The system shows low interdependence between components"
        if best_metric[0] == "COMPONENT_ENTANGLEMENT":
            return "The system shows low entanglement between components"

    def worst_metric_observation(worst_metric):
        if worst_metric[0] == "VOLUME":
            return "The system's large size hinders its effective maintenance"
        elif worst_metric[0] == "DUPLICATION":
            return "The system shows high risk in duplicated code"
        elif worst_metric[0] == "UNIT_SIZE":
            return "The system has a pattern of oversized units of code"
        elif worst_metric[0] == "UNIT_COMPLEXITY":
            return "The system has a pattern of complex units."
        elif worst_metric[0] == "UNIT_INTERFACING":
            return "The system shows high risk in units with large interfaces"
        elif worst_metric[0] == "MODULE_COUPLING":
            return "The system shows high risk in its tightly coupled modules"
        elif worst_metric[0] == "COMPONENT_INDEPENDENCE":
            return "The system shows high risk where components of the system depend on each other"
        elif worst_metric[0] == "COMPONENT_ENTANGLEMENT":
            return "The system shows high risk where components of the system often interact with each other"
        
    def arch_observation(arch_rating):
        if arch_rating < 2.5:
            return "bad"
        elif arch_rating < 3.5:
            return "okayish"
        else:
            return "great"
        
    def test_code_relative(test_code_ratio):
        if test_code_ratio < 0.15:
            return "below market average"
        elif test_code_ratio < 0.5:
            return "market average"
        else:
            return "above market average"
        
    def test_code_summary(test_code_ratio):
        if test_code_ratio < 0.1:
            return "the system does not have an automated testing suite in place. This decreases developer velocity and can increase bugs in production. This can be partially compensated by increased manual testing."
        elif test_code_ratio < 0.15:
            return "breaking changes are likely not caught by an automated test at an early stage. This decreases developer velocity and can increase bugs in production. This can be partially compensated by increased manual testing."
        elif test_code_ratio < 0.5:
            return "breaking changes will be caught by the automated test suite, but not all. The amount of test code can be increased to increase developer velocity and reduce bugs in production."
        elif test_code_ratio < 1.5:
            return "breaking changes are likely to be caught by an automated test at an early stage. This increases developer velocity and reduces bugs in production."
        else:
            return "that an extremely mature automated testing suite is in place, that will likely catch breaking changes at an early stage. This increases developer velocity and reduces bugs in production."
        
    def technology_summary(target_ratio, phaseout_ratio, phaseout_technologies):
        phaseout_technologies_text = ", ".join(phaseout_technologies)
        if target_ratio > 0.9:
            return "The system is built using common and modern technologies."
        elif target_ratio > 0.5:
            if phaseout_ratio < 0.1:
                return "The system is built using mostly modern technologies, and has no or minimal technologies that should be phased out."
            else: 
                return f"The system is built using mostly modern technologies, but also contains older generation technologies that should be considered for replacement: {phaseout_technologies_text}."
        elif target_ratio > 0.2:
            if phaseout_ratio < 0.1:
                return "The system is built using mainly technologies that are of an older generation, but typically still in support. While not ideal, no active replacement may be needed yet."
            else: 
                return f"The system is built using mainly technologies that are of an older generation. These should be considered for active replacement: {phaseout_technologies_text}."
        else:
            if phaseout_ratio < 0.1:
                return "The system is almost completely built using older generation technology, but typically still in support. While not ideal, no active replacement may be needed yet."
            else:
                return "The system is almost completely built using older generation technology. Consider moving development of new components to a newer generation."
            
    def arch_worst_best_metric(aq_rating, aq_system_properties):
        pass

    def arch_worst_metric_remark(arch_sp_ratings):
        sorted_metric_data = SmartRemarks.sort_metrics(arch_sp_ratings, StaticData.arch_metrics)

        worst_metric = sorted_metric_data[0]
        if worst_metric[1] < 2.5:
            return SmartRemarks.arch_worst_metric_observation(worst_metric)
        
    def arch_best_metric_remark(arch_sp_ratings):
        sorted_metric_data = SmartRemarks.sort_metrics(arch_sp_ratings, StaticData.arch_metrics)

        best_metric = sorted_metric_data[-1]
        if best_metric[1] > 3.5:
            return SmartRemarks.arch_best_metric_observation(best_metric)
    
    def sort_metrics(ratings, metrics):
        metric_data = {}
        for metric in metrics:
            value = ratings[GenericUtils.to_json_name(metric)]
            if value > 0.1: # If rating is zero, it means that rating is N/A. Ignore
                metric_data[metric] = value
        return sorted(metric_data.items(), key=lambda item: item[1])

    def arch_best_metric_observation(metric):
        return StaticData.ARCH_BEST_METRIC_TEXT[metric[0]]
    
    def arch_worst_metric_observation(metric):
        return StaticData.ARCH_WORST_METRIC_TEXT[metric[0]]
    
    def tech_variance_remark(sorted_tech_data, total_volume_pm):
        if(sorted_tech_data[0]["volumeInPersonMonths"]) > total_volume_pm * 0.75:
            return f"The system is mainly built using {sorted_tech_data[0]['displayName']}."
        main_technologies = []
        for data in sorted_tech_data:
            if(data["volumeInPersonMonths"]) > total_volume_pm * 0.15:
                main_technologies.append(data["displayName"])
        return f"The system is mainly built using {len(main_technologies)} different technologies: {', '.join(main_technologies)}"

    def osh_remark(libraries):
        mentionable_vulnerability_count = 0
        for vulnerability in libraries.get("vulnerabilities", []):
            if (vulnerability["ratings"][0]["severity"] == "medium") or (vulnerability["ratings"][0]["severity"]=="high") or (vulnerability["ratings"][0]["severity"]=="high"):
                mentionable_vulnerability_count += 1
        mentionable_license_count = 0
        for library in libraries["components"]:
            if (library["properties"][0]["value"] == "CRITICAL") or (library["properties"][0]["value"] == "HIGH") or (library["properties"][0]["value"] == "MEDIUM"):
                mentionable_license_count += 1
        return f"This system has {mentionable_vulnerability_count} medium or higher risk vulnerable libraries and {mentionable_license_count} licenses with potential legal risks that should be investigated"

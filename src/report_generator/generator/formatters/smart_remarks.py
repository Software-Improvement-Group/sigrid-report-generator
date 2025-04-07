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
from typing import List

from report_generator.generator.constants import ArchMetric, MaintMetric, MetricEnum

MAINT_BEST_METRIC_TEXT = {
    MaintMetric.VOLUME                : "The system is small and therefore easier to maintain.",
    MaintMetric.DUPLICATION           : "The system shows low risk in its duplicated logic.",
    MaintMetric.UNIT_SIZE             : "The system shows low risk in unit sizing",
    MaintMetric.UNIT_COMPLEXITY       : "The system shows low risk in unit complexity.",
    MaintMetric.UNIT_INTERFACING      : "The system shows low risk in unit interfacing",
    MaintMetric.MODULE_COUPLING       : "The system shows loose coupling across modules",
    MaintMetric.COMPONENT_INDEPENDENCE: "The system shows low interdependence between components",
    MaintMetric.COMPONENT_ENTANGLEMENT: "The system shows low entanglement between components"
}

MAINT_WORST_METRIC_TEXT = {
    MaintMetric.VOLUME                : "The system's large size hinders its effective maintenance",
    MaintMetric.DUPLICATION           : "The system shows high risk in duplicated code",
    MaintMetric.UNIT_SIZE             : "The system has a pattern of oversized units of code",
    MaintMetric.UNIT_COMPLEXITY       : "The system has a pattern of complex units.",
    MaintMetric.UNIT_INTERFACING      : "The system shows high risk in units with large interfaces",
    MaintMetric.MODULE_COUPLING       : "The system shows high risk in its tightly coupled modules",
    MaintMetric.COMPONENT_INDEPENDENCE: "The system shows high risk where components of the system depend on each other",
    MaintMetric.COMPONENT_ENTANGLEMENT: "The system shows high risk where components of the system often interact with each other"
}

ARCH_BEST_METRIC_TEXT = {
    ArchMetric.CODE_BREAKDOWN              : "The system scores highly in Code Breakdown resulting in increased flexibility through well-defined components that enable efficient parallel work across functional or technical boundaries.",
    ArchMetric.COMPONENT_COUPLING          : "The system's high score in component coupling means components with fewer dependencies, allowing for greater evolution, and minimizing impact on the system or landscape during interface changes.",
    ArchMetric.COMPONENT_COHESION          : "The system's high score in Component Cohesion means highly reusable and replaceable components with focused internal logic. This minimizes external dependencies and references from other external components.",
    ArchMetric.CODE_REUSE                  : "The system scores highly in Code Reuse, minimizing duplication within and between components. This reduces coupling, preventing implicit dependencies and enhancing system modularity.",
    ArchMetric.COMMUNICATION_CENTRALIZATION: "The system's high score Communication Centralization reflects high encapsulation. Centralized calls from a component enhance encapsulation, making it less sensitive to external changes and easier to update in response to such modifications.",
    ArchMetric.DATA_COUPLING               : "The system scores highly in Data coupling, ensuring high flexibility by limiting components accessing a data store, preventing widespread impact from changes to its structure and enhancing system adaptability.",
    ArchMetric.TECHNOLOGY_PREVALENCE       : "The system excels in Technology Prevalence, aligning team knowledge and preventing component abandonment due to unfamiliar tech, fostering adaptability in areas requiring changes.",
    ArchMetric.BOUNDED_EVOLUTION           : "The system's high score in Bounded Evolution signifies limited updates for components, preventing excessive dependencies and knowledge centralization, and promoting a more balanced and adaptable system.",
    ArchMetric.KNOWLEDGE_DISTRIBUTION      : "The system's high score in Knowledge Distribution averts reliance on a single developer, mitigating knowledge loss risks and fostering continuity.",
    ArchMetric.COMPONENT_FRESHNESS         : "The system's high score in Component Freshness ensures activity across multiple components, avoiding centralization, fostering balance, and reducing reliance on a single component."
}

ARCH_WORST_METRIC_TEXT = {
    ArchMetric.CODE_BREAKDOWN              : "The system's low score in Code Breakdown restricts flexibility, hindering parallel work across boundaries, as the codebase lacks clear, well-defined components, impeding efficient collaboration and adaptability.",
    ArchMetric.COMPONENT_COUPLING          : "The system's low score in Component Coupling constrains architecture, constraining evolution and imposing high-impact changes, impeding system adaptability.",
    ArchMetric.COMPONENT_COHESION          : "The system scores poorly in Component Cohesion, constraining evolution and triggering high-impact changes, impeding adaptability across the system or landscape.",
    ArchMetric.CODE_REUSE                  : "The system's low score in Code Reuse heightens complexity, fostering coupling through duplicated code. This impedes flexibility and hinders responsibility separation.",
    ArchMetric.COMMUNICATION_CENTRALIZATION: "The system's low score in Communication Centralization weakens encapsulation, heightening sensitivity to external changes, making updates challenging, and impacting adaptability.",
    ArchMetric.DATA_COUPLING               : "The system's low score in Data Coupling constrains flexibility, demanding changes across components with each alteration to the data store structure, hindering adaptability and system resilience.",
    ArchMetric.TECHNOLOGY_PREVALENCE       : "The system scores poorly in Technology Prevalence, hampering adaptability and risking component abandonment due to misaligned tech knowledge, impacting efficient change implementation.",
    ArchMetric.BOUNDED_EVOLUTION           : "The system scores poorly in Bounded Evolution, implying excessive updates, possibly signaling over-dependence, centralization issues, and hindering system stability and adaptability.",
    ArchMetric.KNOWLEDGE_DISTRIBUTION      : "The system's low score in Knowledge Distribution risks knowledge loss with a single developer on a large component, hindering adaptability and continuity upon that person's departure.",
    ArchMetric.COMPONENT_FRESHNESS         : "The system's low score in Component Freshness impedes adaptability, indicating centralized activity rather than distributed across components, hindering a balanced and responsive system."
}


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
    sorted_metric_data = sort_metrics(maintainability_data, list(MaintMetric))

    worst_metric = sorted_metric_data[0]
    if worst_metric[1] < 2.5:
        return worst_metric_observation(worst_metric)


def maint_observations(maintainability_data):
    sorted_metric_data = sort_metrics(maintainability_data, list(MaintMetric))
    res = ""
    for sorted_metric in sorted_metric_data:
        if sorted_metric[1] < 2.5:
            res += worst_metric_observation(sorted_metric)
            res += "\n"
        if sorted_metric[1] > 3.5:
            res += best_metric_observation(sorted_metric)
            res += "\n"
    return res


def best_metric_observation(best_metric):
    return MAINT_BEST_METRIC_TEXT[best_metric[0]]


def worst_metric_observation(worst_metric):
    return MAINT_WORST_METRIC_TEXT[worst_metric[0]]


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
    sorted_metric_data = sort_metrics(arch_sp_ratings, list(ArchMetric))

    worst_metric = sorted_metric_data[0]
    if worst_metric[1] < 2.5:
        return arch_worst_metric_observation(worst_metric)


def arch_best_metric_remark(arch_sp_ratings):
    sorted_metric_data = sort_metrics(arch_sp_ratings, list(ArchMetric))

    best_metric = sorted_metric_data[-1]
    if best_metric[1] > 3.5:
        return arch_best_metric_observation(best_metric)


def sort_metrics(ratings, metrics: List[MetricEnum]):
    metric_data = {}
    for metric in metrics:
        value = ratings[metric.to_json_name()]
        if value > 0.1:  # If rating is zero, it means that rating is N/A. Ignore
            metric_data[metric] = value
    return sorted(metric_data.items(), key=lambda item: item[1])


def arch_best_metric_observation(metric):
    return ARCH_BEST_METRIC_TEXT[metric[0]]


def arch_worst_metric_observation(metric):
    return ARCH_WORST_METRIC_TEXT[metric[0]]


def tech_variance_remark(sorted_tech_data, total_volume_pm):
    if (sorted_tech_data[0]["volumeInPersonMonths"]) > total_volume_pm * 0.75:
        return f"The system is mainly built using {sorted_tech_data[0]['displayName']}."
    main_technologies = []
    for data in sorted_tech_data:
        if (data["volumeInPersonMonths"]) > total_volume_pm * 0.15:
            main_technologies.append(data["displayName"])
    return f"The system is mainly built using {len(main_technologies)} different technologies: {', '.join(main_technologies)}"


def osh_remark(libraries):
    mentionable_vulnerability_count = 0
    for vulnerability in libraries.get("vulnerabilities", []):
        if (vulnerability["ratings"][0]["severity"] == "medium") or (
                vulnerability["ratings"][0]["severity"] == "high") or (
                vulnerability["ratings"][0]["severity"] == "high"):
            mentionable_vulnerability_count += 1
    mentionable_license_count = 0
    for library in libraries.get("components", []):
        if (library["properties"][0]["value"] == "CRITICAL") or (library["properties"][0]["value"] == "HIGH") or (
                library["properties"][0]["value"] == "MEDIUM"):
            mentionable_license_count += 1
    return f"This system has {mentionable_vulnerability_count} medium or higher risk vulnerable libraries and {mentionable_license_count} licenses with potential legal risks that should be investigated"


def osh_relative_rating(osh_rating):
    if osh_rating < 2.5:
        return "below market average"
    elif osh_rating < 3.5:
        return "market average"
    else:
        return "above market average"

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

from report_generator.generator.constants import ArchMetric, ArchSubcharacteristic, MaintMetric, MetricEnum, \
    OSHMetric
from report_generator.generator.data_models import *
from report_generator.generator.formatters import smart_remarks
from report_generator.generator.formatters.formatters import calculate_stars, format_diff, maintainability_round
from .base import parameterized_text_placeholder, text_placeholder


@text_placeholder()
def system_name():
    """The name of the system as defined in Sigrid Metadata, capitalized."""
    return system_metadata.display_name


@text_placeholder()
def customer_name():
    """The name of the customer as defined in Sigrid, capitalized."""
    return maintainability_data.customer_name


@text_placeholder()
def period_start_date():
    """The reporting period's start date in yyyy-mm-dd format."""
    return maintainability_data.period[0]


@text_placeholder()
def period_end_date():
    """The reporting period's end date in yyyy-mm-dd format."""
    return maintainability_data.period[1]


@text_placeholder()
def report_date():
    """The current date formatted as Month Day, Year."""
    return datetime.now().strftime("%B %d, %Y")


@text_placeholder()
def maint_rating():
    """The 0.5-5.5 star rating provided by SIG's Maintainability Model."""
    return maintainability_round(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_diff():
    """The maintainability rating diff within the reporting period."""
    old_rating = maintainability_data.start_snapshot["maintainability"]
    new_rating = maintainability_data.maintainability_rating
    return format_diff(old_rating, new_rating)


@text_placeholder()
def maint_stars():
    """Stars corresponding to the system's Maintainability Rating."""
    return calculate_stars(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_relative():
    """Remark of the system's Maintainability Rating relative to the benchmark."""
    return smart_remarks.relative_to_market_average(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_indication():
    """Indicates whether the maintainability rating is above, below or at market average."""
    return smart_remarks.relative_cost(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_observation():
    """Short description of the worst maintainability metric."""
    return smart_remarks.maint_observation(maintainability_data.data)


@text_placeholder()
def maint_multiple_observations():
    """Smart Remarks for all maintainability metrics that are either <= 2 stars or >= 4 stars."""
    return smart_remarks.maint_observations(maintainability_data.data)


@text_placeholder()
def maint_date_day():
    """The day of the month the latest system snapshot which was analyzed."""
    return maintainability_data.date.strftime("%d")


@text_placeholder()
def maint_date_month():
    """The month of the latest system snapshot which was analyzed."""
    return maintainability_data.date.strftime("%b").upper()


@text_placeholder()
def maint_date_year():
    """The year of the latest system snapshot which was analyzed."""
    return maintainability_data.date.strftime("%Y")


@text_placeholder()
def maint_size():
    """Description of the system volume."""
    volume_rating = maintainability_data.data["volume"]
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


@text_placeholder()
def test_code_ratio():
    """The test/code ratio of the system. Measured as a ratio of total production code against total test code. No decimals."""
    return format(maintainability_data.data["testCodeRatio"], ".0%")


@text_placeholder()
def test_code_relative():
    """Remark on the system's test/code ratio relative to the industry."""
    if "testCodeRatio" in maintainability_data.data:
        return smart_remarks.test_code_relative(maintainability_data.data["testCodeRatio"])
    return ""


@text_placeholder()
def test_code_summary():
    """Remark on the quality of testing in the system indicated by the total test/code ratio observed."""
    if "testCodeRatio" in maintainability_data.data:
        return smart_remarks.test_code_summary(maintainability_data.data["testCodeRatio"])
    return ""


@text_placeholder()
def system_pm():
    """The volume of the system in person months. 1 decimal."""
    return maintainability_data.system_pm


@text_placeholder()
def system_py():
    """The volume of the system in person years. 1 decimal."""
    return maintainability_data.system_py


@text_placeholder()
def system_loc():
    """The volume of the system in lines of code."""
    return maintainability_data.system_loc


@text_placeholder()
def system_loc_format_locale():
    """The volume of the system in lines of code, formatted with thousands separator corresponding with your system locale settings."""
    return f"{maintainability_data.system_loc:n}" if maintainability_data.system_loc is not None else ""


@text_placeholder()
def system_loc_format_comma():
    """The volume of the system in lines of code, formatted with commas as thousands separator."""
    return f"{maintainability_data.system_loc:,}" if maintainability_data.system_loc is not None else ""


@text_placeholder()
def system_loc_format_dot():
    """The volume of the system in lines of code, formatted with dots as thousands separator."""
    return f"{maintainability_data.system_loc:,}".replace(",",
                                                          ".") if maintainability_data.system_loc is not None else ""


@text_placeholder()
def volume_relative():
    """Relative volume remark for the system."""
    return smart_remarks.relative_volume(maintainability_data.data["volume"])


@text_placeholder()
def tech_common_summary():
    """Remark on how common the technologies used in the system are relative to the industry."""
    return smart_remarks.technology_summary(maintainability_data.tech_target_ratio,
                                            maintainability_data.tech_phaseout_ratio,
                                            maintainability_data.tech_phaseout_technologies)


@text_placeholder()
def tech_variance():
    """Remark on how many significant technologies the system contains (threshold: 15% or more)."""
    return smart_remarks.tech_variance_remark(maintainability_data.sorted_tech,
                                              maintainability_data.tech_total_volume_pm)


@text_placeholder()
def tech_summary():
    """Remark on how common the technologies used in the system are relative to the industry."""
    return smart_remarks.technology_summary(maintainability_data.tech_target_ratio,
                                            maintainability_data.tech_phaseout_ratio,
                                            maintainability_data.tech_phaseout_technologies)


@parameterized_text_placeholder(custom_key="TECH_{parameter}_NAME", parameters=range(1, 6))
def tech_name(idx: int):
    """Name of the technology in the system (if present)."""
    return maintainability_data.sorted_tech_get_key(idx - 1, 'displayName')


@parameterized_text_placeholder(custom_key="TECH_{parameter}_PY", parameters=range(1, 6))
def tech_person_years(idx: int):
    """Volume of the technology in the system (if present) in person years. 1 decimal."""
    volume = maintainability_data.sorted_tech_get_key(idx - 1, 'volumeInPersonMonths', None)
    return round(volume / 12, 1) if volume else ""


@parameterized_text_placeholder(custom_key="TECH_{parameter}_PM", parameters=range(1, 6))
def tech_person_months(idx: int):
    """Volume of the technology in the system (if present) in person months. 1 decimal."""
    volume = maintainability_data.sorted_tech_get_key(idx - 1, 'volumeInPersonMonths', None)
    return round(volume, 1) if volume else ""


@parameterized_text_placeholder(custom_key="TECH_{parameter}_LOC", parameters=range(1, 6))
def tech_lines_of_code(idx: int):
    """Volume of the technology in the system (if present) in lines of code. 1 decimal."""
    return maintainability_data.sorted_tech_get_key(idx - 1, 'volumeInLoc')


@parameterized_text_placeholder(custom_key="TECH_{parameter}_MAINT_RATING", parameters=range(1, 6))
def tech_maintainability_rating(idx: int):
    """Maintainability rating of the technology in the system (if present). One decimal."""
    rating = maintainability_data.sorted_tech_get_key(idx - 1, 'maintainability')
    return round(rating, 1) if rating else ""


@parameterized_text_placeholder(custom_key="TECH_{parameter}_TEST_RATIO", parameters=range(1, 6))
def tech_test_ratio(idx: int):
    """Test code ratio of the technology in the system (if present)."""
    return maintainability_data.sorted_tech_get_key(idx - 1, 'testCodeRatio')


@parameterized_text_placeholder(custom_key="TECH_{parameter}_TECH_RISK", parameters=range(1, 6))
def tech_risk(idx: int):
    """Technology risk rating of the technology in the system (if present)."""
    return maintainability_data.sorted_tech_get_key(idx - 1, 'technologyRisk')


@parameterized_text_placeholder(custom_key="MAINT_RATING_{parameter}", parameters=list(MaintMetric))
def maint_rating_param(metric: MaintMetric):
    """The 0.5-5.5 star rating for this metric."""
    metric_key = metric.to_json_name()
    return maintainability_round(maintainability_data.data[metric_key])


@parameterized_text_placeholder(custom_key="MAINT_DIFF_{parameter}", parameters=list(MaintMetric))
def maint_rating_diff_param(metric: MaintMetric):
    """The rating difference for the specified metric within the reporting period."""
    old_rating = maintainability_data.start_snapshot[metric.to_json_name()]
    new_rating = maintainability_data.data[metric.to_json_name()]
    return format_diff(old_rating, new_rating)


@parameterized_text_placeholder(custom_key="STARS_{parameter}", parameters=list(MaintMetric))
def maint_stars_param(metric: MaintMetric):
    """Stars corresponding to this metric rating."""
    metric_key = metric.to_json_name()
    return calculate_stars(maintainability_data.data[metric_key])


@text_placeholder()
def arch_date_day():
    """The day of the month the latest system snapshot which was analyzed."""
    return architecture_data.date.strftime("%d")


@text_placeholder()
def arch_date_month():
    """The month of the latest system snapshot which was analyzed."""
    return architecture_data.date.strftime("%b").upper()


@text_placeholder()
def arch_date_year():
    """The year of the latest system snapshot which was analyzed."""
    return architecture_data.date.strftime("%Y")


@text_placeholder()
def arch_rating():
    """The 0.5-5.5 star rating provided by SIG's Architecture Quality Model."""
    return maintainability_round(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_model_version():
    """The model version used for architecture analysis."""
    return architecture_data.data["modelVersion"]


@text_placeholder()
def arch_stars():
    """Stars corresponding to the system's Architecture Quality Rating."""
    return calculate_stars(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_at_below():
    """Remark about Architecture Quality being below a certain threshold."""
    return smart_remarks.relative_to_market_average(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_observation():
    """Architecture quality observation remark."""
    return smart_remarks.arch_observation(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_worst_metric_remark():
    """Remark about the lowest rating metric in the system's Architecture Quality analysis."""
    return smart_remarks.arch_worst_metric_remark(architecture_data.ratings["systemProperties"])


@text_placeholder()
def arch_best_metric_remark():
    """Remark about the highest rating metric in the system's Architecture Quality analysis."""
    return smart_remarks.arch_best_metric_remark(architecture_data.ratings["systemProperties"])


@parameterized_text_placeholder(custom_key="ARCH_RATING_{parameter}",
                                parameters=list(ArchMetric) + list(ArchSubcharacteristic))
def arch_rating_param(metric: MetricEnum):
    """The 0.5-5.5 star rating for this metric or subcharacteristic."""
    metric_key = metric.to_json_name()
    return maintainability_round(architecture_data.get_score_for_prop_or_subchar(metric_key))


@parameterized_text_placeholder(custom_key="STARS_{parameter}",
                                parameters=list(ArchMetric) + list(ArchSubcharacteristic))
def arch_stars_param(metric: MetricEnum):
    """Stars corresponding to this metric or subcharacteristic rating."""
    metric_key = metric.to_json_name()
    return calculate_stars(architecture_data.get_score_for_prop_or_subchar(metric_key))


@text_placeholder()
def osh_risk_summary():
    """One-sentence summary of main OSH findings."""
    return smart_remarks.osh_remark(osh_data.raw_data)


@text_placeholder()
def osh_total_deps():
    """Total number of identified open-source dependencies."""
    return osh_data.data.total_deps


@text_placeholder()
def osh_total_vuln():
    """Number of identified open-source dependencies with a known vulnerability."""
    return osh_data.data.total_vulnerable


@text_placeholder()
def osh_date_day():
    """The day of the month the latest system snapshot which was analyzed."""
    return osh_data.data.date_day


@text_placeholder()
def osh_date_month():
    """The month of the latest system snapshot which was analyzed."""
    return osh_data.data.date_month


@text_placeholder()
def osh_date_year():
    """The year of the latest system snapshot which was analyzed."""
    return osh_data.data.date_year


@text_placeholder()
def osh_vuln_summary():
    """Descriptive summary of open-source vulnerability issues identified."""
    return osh_data.vulnerability_summary


@text_placeholder()
def osh_freshness_summary():
    """Descriptive summary of open-source freshness issues identified."""
    return osh_data.freshness_summary


@text_placeholder()
def osh_legal_summary():
    """Descriptive summary of open-source legal issues identified."""
    return osh_data.legal_summary


@text_placeholder()
def osh_management_summary():
    """Descriptive summary of open-source management issues identified."""
    return osh_data.management_summary


@text_placeholder()
def osh_relative():
    """Relative rating remark for open-source health."""
    return smart_remarks.osh_relative_rating(osh_data.data.ratings["system"])


@parameterized_text_placeholder(custom_key="OSH_RATING_{parameter}",
                                parameters=list(OSHMetric))
def osh_rating_param(metric: OSHMetric):
    """The 0.5-5.5 star rating for this OSH metric."""
    metric_key = metric.to_json_name()
    return maintainability_round(osh_data.get_score_for_prop(metric_key))


@parameterized_text_placeholder(custom_key="STARS_{parameter}",
                                parameters=list(OSHMetric))
def osh_stars_param(metric: OSHMetric):
    """Stars corresponding to this OSH metric rating."""
    metric_key = metric.to_json_name()
    return calculate_stars(osh_data.get_score_for_prop(metric_key))


@text_placeholder()
def maintenance_fte():
    """Estimated maintenance FTE (Full-Time Equivalent) for the system."""
    return f"{maintainability_data.system_py * 0.15:.1f}"


@text_placeholder()
def technical_debt_py():
    """Technical debt of the system in person years."""
    return f"{modernization_data.single_system_candidate.technical_debt_in_py:.1f}"


@text_placeholder()
def renovation_effort_py():
    """Estimated renovation effort in person years."""
    return f"{modernization_data.single_system_candidate.estimated_effort_py:.1f}"


@text_placeholder()
def technical_debt_percentage():
    """Technical debt as a percentage of total system volume."""
    volume_in_py = modernization_data.single_system_candidate.volume_in_py
    technical_debt_in_py = modernization_data.single_system_candidate.technical_debt_in_py
    return f"{(technical_debt_in_py * 100.0 / volume_in_py):.0f}"


@parameterized_text_placeholder(custom_key="MODERNIZATION_SYSTEM_{parameter}", parameters=range(1, 11))
def modernization_system_name(index: int):
    """Name of the modernization candidate system."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return modernization_data.modernization_candidates[index].display_name


@parameterized_text_placeholder(custom_key="MODERNIZATION_BUSINESS_{parameter}", parameters=range(1, 11))
def modernization_business_criticality(index: int):
    """Business criticality of the modernization candidate system."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return modernization_data.modernization_candidates[index].business_criticality.title()


@parameterized_text_placeholder(custom_key="MODERNIZATION_PY_{parameter}", parameters=range(1, 11))
def modernization_volume(index: int):
    """Volume of the modernization candidate system in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{modernization_data.modernization_candidates[index].volume_in_py:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_ACTIVITY_{parameter}", parameters=range(1, 11))
def modernization_activity(index: int):
    """Activity level of the modernization candidate system in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""

    activity = modernization_data.modernization_candidates[index].activity_in_py
    return "Unknown" if activity is None else f"{activity:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_SCENARIO_{parameter}", parameters=range(1, 11))
def modernization_scenario(index: int):
    """Modernization scenario for the candidate system."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return modernization_data.modernization_candidates[index].scenario.value.upper()


@parameterized_text_placeholder(custom_key="MODERNIZATION_TECHNICAL_DEBT_{parameter}", parameters=range(1, 11))
def modernization_technical_debt(index: int):
    """Technical debt of the modernization candidate system in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{modernization_data.modernization_candidates[index].technical_debt_in_py:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_CHANGE_SPEED_{parameter}", parameters=range(1, 11))
def modernization_change_speed(index: int):
    """Estimated change speed improvement for the modernization candidate."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"+ {modernization_data.modernization_candidates[index].estimated_change_speed:.0f}%"


@parameterized_text_placeholder(custom_key="MODERNIZATION_EFFORT_{parameter}", parameters=range(1, 11))
def modernization_effort(index: int):
    """Estimated modernization effort in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{modernization_data.modernization_candidates[index].estimated_effort_py:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_N_{parameter}", parameters=range(1, 11))
def modernization_index(index: int):
    """Index number for the modernization candidate."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{index}."


@text_placeholder()
def modernization_system_count():
    """Total number of modernization candidate systems."""
    return len(modernization_data.possible_candidates)


@text_placeholder()
def modernization_customer_name():
    """Customer name for modernization analysis."""
    return modernization_data.possible_candidates[0].metadata["customerName"].title()

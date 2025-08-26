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

from report_generator.generator.constants import MaintMetric
from report_generator.generator.data_models import *
from report_generator.generator.formatters import smart_remarks
from report_generator.generator.formatters.formatters import calculate_stars, format_diff, maintainability_round
from .base import parameterized_text_placeholder, text_placeholder


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

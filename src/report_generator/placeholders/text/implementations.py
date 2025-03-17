from datetime import datetime

from report_generator import constants
from report_generator.data_models import *
from report_generator.formatters import smart_remarks
from report_generator.formatters.formatters import maintainability_round, calculate_stars
from .base import text_placeholder, parameterized_text_placeholder


def _to_json_name(metric):
    metric = metric.replace("_", " ").title().replace(" ", "")
    return metric[0].lower() + metric[1:]


@text_placeholder()
def system_name():
    return maintainability_data.system_name


@text_placeholder()
def customer_name():
    return maintainability_data.customer_name


@text_placeholder()
def report_date():
    return datetime.now().strftime("%B %d, %Y")


@text_placeholder()
def maint_rating():
    return maintainability_round(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_stars():
    return calculate_stars(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_relative():
    return smart_remarks.relative_to_market_average(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_indication():
    return smart_remarks.relative_cost(maintainability_data.maintainability_rating)


@text_placeholder()
def maint_observation():
    return smart_remarks.maint_observation(maintainability_data.data)


@text_placeholder()
def maint_multiple_observations():
    return smart_remarks.maint_observations(maintainability_data.data)


@text_placeholder()
def maint_date_day():
    return maintainability_data.date.strftime("%d")


@text_placeholder()
def maint_date_month():
    return maintainability_data.date.strftime("%b")


@text_placeholder()
def maint_date_year():
    return maintainability_data.date.strftime("%Y")


@text_placeholder()
def maint_size():
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
    return format(maintainability_data.data["testCodeRatio"], ".0%")


@text_placeholder()
def test_code_relative():
    return smart_remarks.test_code_relative(maintainability_data.data["testCodeRatio"])


@text_placeholder()
def test_code_summary():
    return smart_remarks.test_code_summary(maintainability_data.data["testCodeRatio"])


@text_placeholder()
def system_pm():
    return maintainability_data.system_pm


@text_placeholder()
def system_py():
    return maintainability_data.system_py


@text_placeholder()
def system_loc():
    return maintainability_data.system_loc


@text_placeholder()
def system_loc_format_locale():
    return f"{maintainability_data.system_loc:n}" if maintainability_data.system_loc is not None else ""


@text_placeholder()
def system_loc_format_comma():
    return f"{maintainability_data.system_loc:,}" if maintainability_data.system_loc is not None else ""


@text_placeholder()
def system_loc_format_dot():
    return f"{maintainability_data.system_loc:,}".replace(",",
                                                          ".") if maintainability_data.system_loc is not None else ""


@text_placeholder()
def volume_relative():
    return smart_remarks.relative_volume(maintainability_data.data["volume"])


@text_placeholder()
def tech_common_summary():
    return smart_remarks.technology_summary(maintainability_data.tech_target_ratio,
                                            maintainability_data.tech_phaseout_ratio,
                                            maintainability_data.tech_phaseout_technologies)


@text_placeholder()
def tech_variance():
    return smart_remarks.tech_variance_remark(maintainability_data.sorted_tech,
                                              maintainability_data.tech_total_volume_pm)


@text_placeholder()
def tech_summary():
    return smart_remarks.technology_summary(maintainability_data.tech_target_ratio,
                                            maintainability_data.tech_phaseout_ratio,
                                            maintainability_data.tech_phaseout_technologies)


@parameterized_text_placeholder(custom_key="TECH_{parameter}_NAME", parameters=range(1, 6))
def tech_name(idx: int):
    return maintainability_data.sorted_tech_get_key(idx - 1, 'displayName')


@parameterized_text_placeholder(custom_key="TECH_{parameter}_PY", parameters=range(1, 6))
def tech_person_years(idx: int):
    volume = maintainability_data.sorted_tech_get_key(idx - 1, 'volumeInPersonMonths', None)
    return round(volume / 12, 1) if volume else ""


@parameterized_text_placeholder(custom_key="TECH_{parameter}_PM", parameters=range(1, 6))
def tech_person_months(idx: int):
    volume = maintainability_data.sorted_tech_get_key(idx - 1, 'volumeInPersonMonths', None)
    return round(volume, 1) if volume else ""


@parameterized_text_placeholder(custom_key="TECH_{parameter}_LOC", parameters=range(1, 6))
def tech_lines_of_code(idx: int):
    return maintainability_data.sorted_tech_get_key(idx - 1, 'volumeInLoc')


@parameterized_text_placeholder(custom_key="TECH_{parameter}_MAINT_RATING", parameters=range(1, 6))
def tech_maintainability_rating(idx: int):
    return maintainability_data.sorted_tech_get_key(idx - 1, 'maintainability')


@parameterized_text_placeholder(custom_key="TECH_{parameter}_TEST_RATIO", parameters=range(1, 6))
def tech_test_ratio(idx: int):
    return maintainability_data.sorted_tech_get_key(idx - 1, 'testCodeRatio')


@parameterized_text_placeholder(custom_key="TECH_{parameter}_TECH_RISK", parameters=range(1, 6))
def tech_risk(idx: int):
    return maintainability_data.sorted_tech_get_key(idx - 1, 'technologyRisk')


@parameterized_text_placeholder(custom_key="MAINT_RATING_{parameter}", parameters=constants.MAINT_METRICS)
def maint_rating_param(metric: str):
    metric_key = _to_json_name(metric)
    return maintainability_round(maintainability_data.data[metric_key])


@parameterized_text_placeholder(custom_key="STARS_{parameter}", parameters=constants.MAINT_METRICS)
def maint_stars_param(metric: str):
    metric_key = _to_json_name(metric)
    return calculate_stars(maintainability_data.data[metric_key])


@text_placeholder()
def arch_date_day():
    return architecture_data.date.strftime("%d")


@text_placeholder()
def arch_date_month():
    return architecture_data.date.strftime("%b")


@text_placeholder()
def arch_date_year():
    return architecture_data.date.strftime("%Y")


@text_placeholder()
def arch_rating():
    return maintainability_round(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_model_version():
    return architecture_data.data["modelVersion"]


@text_placeholder()
def arch_stars():
    return calculate_stars(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_at_below():
    return smart_remarks.relative_to_market_average(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_observation():
    return smart_remarks.arch_observation(architecture_data.ratings["architecture"])


@text_placeholder()
def arch_worst_metric_remark():
    return smart_remarks.arch_worst_metric_remark(architecture_data.ratings["systemProperties"])


@text_placeholder()
def arch_best_metric_remark():
    return smart_remarks.arch_best_metric_remark(architecture_data.ratings["systemProperties"])


@parameterized_text_placeholder(custom_key="ARCH_RATING_{parameter}",
                                parameters=constants.ARCH_METRICS + constants.ARCH_SUBCHARACTERISTICS)
def arch_rating_param(metric: str):
    metric_key = _to_json_name(metric)
    return maintainability_round(architecture_data.get_score_for_prop_or_subchar(metric_key))


@parameterized_text_placeholder(custom_key="STARS_{parameter}",
                                parameters=constants.ARCH_METRICS + constants.ARCH_SUBCHARACTERISTICS)
def arch_stars_param(metric: str):
    metric_key = _to_json_name(metric)
    return calculate_stars(architecture_data.get_score_for_prop_or_subchar(metric_key))


@text_placeholder()
def osh_risk_summary():
    return smart_remarks.osh_remark(osh_data.raw_data)


@text_placeholder()
def osh_total_deps():
    return osh_data.data.total_deps


@text_placeholder()
def osh_total_vuln():
    return osh_data.data.total_vulnerable


@text_placeholder()
def osh_date_day():
    return osh_data.data.date_day


@text_placeholder()
def osh_date_month():
    return osh_data.data.date_month


@text_placeholder()
def osh_date_year():
    return osh_data.data.date_year


@text_placeholder()
def osh_vuln_summary():
    return osh_data.vulnerability_summary


@text_placeholder()
def osh_freshness_summary():
    return osh_data.freshness_summary


@text_placeholder()
def osh_legal_summary():
    return osh_data.legal_summary


@text_placeholder()
def osh_management_summary():
    return osh_data.management_summary

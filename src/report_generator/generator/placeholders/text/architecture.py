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

from report_generator.generator.constants import ArchMetric, ArchSubcharacteristic, MetricEnum
from report_generator.generator.data_models import *
from report_generator.generator.formatters import smart_remarks
from report_generator.generator.formatters.formatters import calculate_stars, maintainability_round
from .base import parameterized_text_placeholder, text_placeholder


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

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

from report_generator.generator.domain import (
    COLUMNS_BY_TYPE,
    DELTA_QUALITY_METRICS,
    maintainability_delta_quality_system_by_type,
)
from report_generator.generator.domain.portfolio.maintainability_delta_quality_portfolio import (
    maintainability_delta_quality_new_code,
)
from report_generator.generator.domain.system.maintainability_delta_quality import (
    DeltaColumn,
)
from report_generator.generator.placeholders.formatting.formatters import (
    star_rating_round,
)
from report_generator.generator.placeholders.implementations.base import (
    MultiParameterList,
)
from report_generator.generator.utils.constants.metrics import DeltaType, MaintMetric

from .base import parameterized_text_placeholder, text_placeholder


def _delta_rating_text(
    delta_type: DeltaType, metric: MaintMetric, column: DeltaColumn
) -> str:
    rating = maintainability_delta_quality_system_by_type[delta_type].rating(
        metric, column
    )
    return star_rating_round(rating) if rating is not None else ""


def _delta_summary_rating_text(delta_type: DeltaType) -> str:
    rating = maintainability_delta_quality_system_by_type[delta_type].summary_rating
    return star_rating_round(rating) if rating is not None else ""


@parameterized_text_placeholder(
    custom_key="DELTA_QUALITY_NEW_CODE_{metric}_RATING_{column}",
    parameters=MultiParameterList(
        DELTA_QUALITY_METRICS, COLUMNS_BY_TYPE[DeltaType.NEW_CODE]
    ),
)
def delta_quality_new_code_rating(metric: MaintMetric, column: DeltaColumn):
    """Star rating of a maintainability metric for a new-code delta-quality column."""
    return _delta_rating_text(DeltaType.NEW_CODE, metric, column)


@parameterized_text_placeholder(
    custom_key="DELTA_QUALITY_CHANGED_CODE_{metric}_RATING_{column}",
    parameters=MultiParameterList(
        DELTA_QUALITY_METRICS, COLUMNS_BY_TYPE[DeltaType.CHANGED_CODE]
    ),
)
def delta_quality_changed_code_rating(metric: MaintMetric, column: DeltaColumn):
    """Star rating of a maintainability metric for a changed-code delta-quality column."""
    return _delta_rating_text(DeltaType.CHANGED_CODE, metric, column)


@parameterized_text_placeholder(
    custom_key="DELTA_QUALITY_REMOVED_CODE_{metric}_RATING_{column}",
    parameters=MultiParameterList(
        DELTA_QUALITY_METRICS, COLUMNS_BY_TYPE[DeltaType.REMOVED_CODE]
    ),
)
def delta_quality_removed_code_rating(metric: MaintMetric, column: DeltaColumn):
    """Star rating of a maintainability metric for a removed-code delta-quality column."""
    return _delta_rating_text(DeltaType.REMOVED_CODE, metric, column)


@parameterized_text_placeholder(
    custom_key="DELTA_QUALITY_{type}_SUMMARY_RATING",
    parameters=list(DeltaType),
)
def delta_quality_summary_rating(delta_type: DeltaType):
    """Overall maintainability star rating of the delta-quality code category."""
    return _delta_summary_rating_text(delta_type)


@text_placeholder()
def portfolio_new_code_biggest_changes():
    """Descriptive summary of the biggest maintainability changes in the portfolio."""
    stats = maintainability_delta_quality_new_code.statistics
    res = []
    highest_system = stats["highest_system"]
    if highest_system:
        rating_str = star_rating_round(highest_system[1])
        res.append(
            f"The highest maintainability rating for new code was achieved by {highest_system[0]} ({rating_str} stars)."
        )
    lowest_system = stats["lowest_system"]
    if lowest_system:
        rating_str = star_rating_round(lowest_system[1])
        res.append(
            f"The lowest maintainability rating for new code was in {lowest_system[0]} ({rating_str} stars)."
        )
    if res:
        return " ".join(res)
    return ""

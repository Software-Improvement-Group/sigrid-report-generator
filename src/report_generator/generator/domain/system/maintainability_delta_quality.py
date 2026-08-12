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

from enum import Enum
from functools import cached_property

from report_generator.generator.context import sigrid_api
from report_generator.generator.utils.constants.metrics import DeltaType, MaintMetric

# The maintainability properties shown on the delta-quality slides, in display order.
# Component-level properties (independence, entanglement) and volume are intentionally
# excluded: the delta-quality endpoint does not report a risk profile for them, matching
# what Sigrid's own delta-quality page displays.
DELTA_QUALITY_METRICS = [
    MaintMetric.DUPLICATION,
    MaintMetric.UNIT_SIZE,
    MaintMetric.UNIT_COMPLEXITY,
    MaintMetric.UNIT_INTERFACING,
    MaintMetric.MODULE_COUPLING,
]

# The risk buckets of a delta-quality risk profile, in best-to-worst order.
_RISK_BUCKET_FIELDS = ("lowRisk", "moderateRisk", "highRisk", "veryHighRisk")


class DeltaColumn(Enum):
    """Identifies one comparison column on a delta-quality slide.

    Purely a data concern: the member identifies the column (its value doubles as the
    identifier used in template placeholder keys) and ``profile_field`` names the API
    risk-profile object the column reads. User-facing labels are a presentation concern
    and live in the placeholder layer.
    """

    TOTAL_BEFORE = "TOTAL_BEFORE"
    NEW_AFTER = "NEW_AFTER"
    CHANGED_BEFORE = "CHANGED_BEFORE"
    CHANGED_AFTER = "CHANGED_AFTER"
    DELETED_BEFORE = "DELETED_BEFORE"

    @property
    def profile_field(self) -> str:
        return _PROFILE_FIELD_BY_COLUMN[self]

    def __str__(self) -> str:
        return self.value


# Which risk-profile object in the API response each column reads.
_PROFILE_FIELD_BY_COLUMN = {
    DeltaColumn.TOTAL_BEFORE: "systemRiskProfileAtStart",
    DeltaColumn.NEW_AFTER: "filesRiskProfileAtEnd",
    DeltaColumn.CHANGED_BEFORE: "filesRiskProfileAtStart",
    DeltaColumn.CHANGED_AFTER: "filesRiskProfileAtEnd",
    DeltaColumn.DELETED_BEFORE: "filesRiskProfileAtStart",
}


# The ordered comparison columns shown for each delta type, matching Sigrid's slides.
COLUMNS_BY_TYPE = {
    DeltaType.NEW_CODE: [DeltaColumn.TOTAL_BEFORE, DeltaColumn.NEW_AFTER],
    DeltaType.CHANGED_CODE: [
        DeltaColumn.TOTAL_BEFORE,
        DeltaColumn.CHANGED_BEFORE,
        DeltaColumn.CHANGED_AFTER,
    ],
    DeltaType.REMOVED_CODE: [DeltaColumn.TOTAL_BEFORE, DeltaColumn.DELETED_BEFORE],
}

# The summary rating of the changed files. For removed code the files no longer exist at
# the end of the period, so the rating measured at the start is used instead.
_SUMMARY_RATING_FIELD = {
    DeltaType.NEW_CODE: "filesRatingAtEnd",
    DeltaType.CHANGED_CODE: "filesRatingAtEnd",
    DeltaType.REMOVED_CODE: "filesRatingAtStart",
}


class MaintainabilityDeltaQualitySystemData:
    """System-level delta quality for a single delta type (new / changed / removed code).

    Wraps the delta-quality endpoint for the system in the current context and exposes
    per-metric, per-column ratings and risk distributions ready for the report.
    """

    def __init__(self, delta_type: DeltaType):
        self._delta_type = delta_type

    @cached_property
    def data(self) -> dict:
        return sigrid_api.get_maintainability_delta_quality(
            delta_type=str(self._delta_type)
        )

    @property
    def columns(self) -> list[DeltaColumn]:
        return COLUMNS_BY_TYPE[self._delta_type]

    @property
    def metrics(self) -> list[MaintMetric]:
        return DELTA_QUALITY_METRICS

    def _risk_profile(self, metric: MaintMetric, column: DeltaColumn) -> dict | None:
        metric_data = self.data.get(metric.to_json_name())
        if not metric_data:
            return None
        return metric_data.get(column.profile_field)

    def rating(self, metric: MaintMetric, column: DeltaColumn) -> float | None:
        profile = self._risk_profile(metric, column)
        return profile.get("rating") if profile else None

    def risk_buckets(
        self, metric: MaintMetric, column: DeltaColumn
    ) -> list[float] | None:
        """The [low, moderate, high, very-high] risk percentages, or None if absent."""
        profile = self._risk_profile(metric, column)
        if not profile:
            return None
        return [profile.get(field, 0.0) for field in _RISK_BUCKET_FIELDS]

    @cached_property
    def summary_rating(self) -> float | None:
        return self.data.get(_SUMMARY_RATING_FIELD[self._delta_type])


maintainability_delta_quality_new_code_system = MaintainabilityDeltaQualitySystemData(
    DeltaType.NEW_CODE
)
maintainability_delta_quality_changed_code_system = (
    MaintainabilityDeltaQualitySystemData(DeltaType.CHANGED_CODE)
)
maintainability_delta_quality_removed_code_system = (
    MaintainabilityDeltaQualitySystemData(DeltaType.REMOVED_CODE)
)

maintainability_delta_quality_system_by_type = {
    DeltaType.NEW_CODE: maintainability_delta_quality_new_code_system,
    DeltaType.CHANGED_CODE: maintainability_delta_quality_changed_code_system,
    DeltaType.REMOVED_CODE: maintainability_delta_quality_removed_code_system,
}

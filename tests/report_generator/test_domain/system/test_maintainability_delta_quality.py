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

from unittest.mock import patch

from report_generator.generator.domain.system.maintainability_delta_quality import (
    DeltaColumn,
    MaintainabilityDeltaQualitySystemData,
)
from report_generator.generator.utils.constants.metrics import DeltaType, MaintMetric


def _profile(rating, low, moderate, high, very_high):
    return {
        "rating": rating,
        "lowRisk": low,
        "moderateRisk": moderate,
        "highRisk": high,
        "veryHighRisk": very_high,
    }


NEW_CODE_RESPONSE = {
    "systemRatingAtStart": 3.7,
    "systemRatingAtEnd": 3.6,
    "filesRatingAtStart": None,
    "filesRatingAtEnd": 4.27,
    "duplication": {
        "systemRiskProfileAtStart": _profile(4.2, 97.0, 0.0, 0.0, 3.0),
        "filesRiskProfileAtStart": None,
        "filesRiskProfileAtEnd": _profile(4.5, 98.0, 0.0, 0.0, 2.0),
    },
    "unitSize": {
        "systemRiskProfileAtStart": _profile(4.3, 70.0, 17.0, 6.0, 10.0),
        "filesRiskProfileAtStart": None,
        "filesRiskProfileAtEnd": _profile(4.7, 77.4, 17.0, 3.8, 1.8),
    },
}

REMOVED_CODE_RESPONSE = {
    "systemRatingAtStart": 3.7,
    "systemRatingAtEnd": 3.6,
    "filesRatingAtStart": 4.41,
    "filesRatingAtEnd": None,
    "unitSize": {
        "systemRiskProfileAtStart": _profile(4.3, 70.0, 17.0, 6.0, 10.0),
        "filesRiskProfileAtStart": _profile(4.7, 80.0, 17.3, 2.1, 0.6),
        "filesRiskProfileAtEnd": None,
    },
}


def _system_data(delta_type, response):
    with patch(
        "report_generator.generator.domain.system.maintainability_delta_quality.sigrid_api"
    ) as sigrid_api:
        sigrid_api.get_maintainability_delta_quality.return_value = response
        data = MaintainabilityDeltaQualitySystemData(delta_type)
        # Trigger the cached fetch inside the patched context.
        _ = data.data
        return data, sigrid_api


class TestMaintainabilityDeltaQualitySystemData:
    def test_fetches_with_delta_type_string(self):
        _, sigrid_api = _system_data(DeltaType.NEW_CODE, NEW_CODE_RESPONSE)
        sigrid_api.get_maintainability_delta_quality.assert_called_once_with(
            delta_type="NEW_CODE"
        )

    def test_new_code_columns(self):
        data, _ = _system_data(DeltaType.NEW_CODE, NEW_CODE_RESPONSE)
        assert data.columns == [DeltaColumn.TOTAL_BEFORE, DeltaColumn.NEW_AFTER]

    def test_removed_code_columns(self):
        data, _ = _system_data(DeltaType.REMOVED_CODE, REMOVED_CODE_RESPONSE)
        assert data.columns == [DeltaColumn.TOTAL_BEFORE, DeltaColumn.DELETED_BEFORE]

    def test_rating_reads_profile_field_per_column(self):
        data, _ = _system_data(DeltaType.NEW_CODE, NEW_CODE_RESPONSE)
        # Total code (Before) reads systemRiskProfileAtStart.
        assert data.rating(MaintMetric.UNIT_SIZE, DeltaColumn.TOTAL_BEFORE) == 4.3
        # New code (After) reads filesRiskProfileAtEnd.
        assert data.rating(MaintMetric.UNIT_SIZE, DeltaColumn.NEW_AFTER) == 4.7

    def test_risk_buckets_order(self):
        data, _ = _system_data(DeltaType.NEW_CODE, NEW_CODE_RESPONSE)
        assert data.risk_buckets(MaintMetric.UNIT_SIZE, DeltaColumn.TOTAL_BEFORE) == [
            70.0,
            17.0,
            6.0,
            10.0,
        ]

    def test_missing_metric_returns_none(self):
        data, _ = _system_data(DeltaType.NEW_CODE, NEW_CODE_RESPONSE)
        # module coupling is absent from the fixture response.
        assert (
            data.rating(MaintMetric.MODULE_COUPLING, DeltaColumn.TOTAL_BEFORE) is None
        )
        assert (
            data.risk_buckets(MaintMetric.MODULE_COUPLING, DeltaColumn.TOTAL_BEFORE)
            is None
        )

    def test_null_profile_returns_none(self):
        # A metric whose profile for a column is explicitly null yields None, not a crash.
        response = {
            "filesRatingAtEnd": 4.0,
            "unitSize": {
                "systemRiskProfileAtStart": _profile(4.3, 70.0, 17.0, 6.0, 10.0),
                "filesRiskProfileAtStart": None,
                "filesRiskProfileAtEnd": None,
            },
        }
        data, _ = _system_data(DeltaType.NEW_CODE, response)
        assert data.rating(MaintMetric.UNIT_SIZE, DeltaColumn.NEW_AFTER) is None
        assert data.risk_buckets(MaintMetric.UNIT_SIZE, DeltaColumn.NEW_AFTER) is None

    def test_summary_rating_uses_files_rating_at_end_for_new_code(self):
        data, _ = _system_data(DeltaType.NEW_CODE, NEW_CODE_RESPONSE)
        assert data.summary_rating == 4.27

    def test_summary_rating_uses_files_rating_at_start_for_removed_code(self):
        data, _ = _system_data(DeltaType.REMOVED_CODE, REMOVED_CODE_RESPONSE)
        # Removed files no longer exist at the end, so the start rating is used.
        assert data.summary_rating == 4.41

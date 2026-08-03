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

from unittest.mock import MagicMock, patch

from report_generator.generator.domain.system.maintainability_delta_quality import (
    DeltaColumn,
)
from report_generator.generator.placeholders.implementations.text import (
    maintainability_delta_quality as module,
)
from report_generator.generator.placeholders.implementations.text.maintainability_delta_quality import (
    _delta_rating_text,
    _delta_summary_rating_text,
    delta_quality_summary_rating,
)
from report_generator.generator.utils.constants.metrics import DeltaType, MaintMetric

MODULE_PATH = (
    "report_generator.generator.placeholders.implementations.text."
    "maintainability_delta_quality"
)


def _patched_by_type(system_data):
    return {delta_type: system_data for delta_type in DeltaType}


class TestDeltaRatingText:
    def test_formats_rating_with_star_rounding(self):
        system_data = MagicMock()
        system_data.rating.return_value = 4.27
        with patch.object(
            module,
            "maintainability_delta_quality_system_by_type",
            _patched_by_type(system_data),
        ):
            result = _delta_rating_text(
                DeltaType.NEW_CODE, MaintMetric.UNIT_SIZE, DeltaColumn.TOTAL_BEFORE
            )
        assert result == "4.2"
        system_data.rating.assert_called_once_with(
            MaintMetric.UNIT_SIZE, DeltaColumn.TOTAL_BEFORE
        )

    def test_missing_rating_returns_empty_string(self):
        system_data = MagicMock()
        system_data.rating.return_value = None
        with patch.object(
            module,
            "maintainability_delta_quality_system_by_type",
            _patched_by_type(system_data),
        ):
            result = _delta_rating_text(
                DeltaType.NEW_CODE, MaintMetric.MODULE_COUPLING, DeltaColumn.NEW_AFTER
            )
        assert result == ""


class TestDeltaSummaryRatingText:
    def test_formats_summary_rating(self):
        system_data = MagicMock()
        system_data.summary_rating = 4.41
        with patch.object(
            module,
            "maintainability_delta_quality_system_by_type",
            _patched_by_type(system_data),
        ):
            assert _delta_summary_rating_text(DeltaType.REMOVED_CODE) == "4.4"

    def test_missing_summary_rating_returns_empty_string(self):
        system_data = MagicMock()
        system_data.summary_rating = None
        with patch.object(
            module,
            "maintainability_delta_quality_system_by_type",
            _patched_by_type(system_data),
        ):
            assert _delta_summary_rating_text(DeltaType.NEW_CODE) == ""


class TestSummaryRatingPlaceholder:
    def test_key_expands_per_delta_type(self):
        import re

        keys = {
            re.sub(r"\{[^}]+\}", str(delta_type), delta_quality_summary_rating.key)
            for delta_type in delta_quality_summary_rating.allowed_parameters
        }
        assert keys == {
            "DELTA_QUALITY_NEW_CODE_SUMMARY_RATING",
            "DELTA_QUALITY_CHANGED_CODE_SUMMARY_RATING",
            "DELTA_QUALITY_REMOVED_CODE_SUMMARY_RATING",
        }

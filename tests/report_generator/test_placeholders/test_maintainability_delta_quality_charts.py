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
from report_generator.generator.placeholders.implementations.base import (
    PlaceholderDocType,
)
from report_generator.generator.placeholders.implementations.charts import (
    maintainability_delta_quality_charts as module,
)
from report_generator.generator.placeholders.implementations.charts.maintainability_delta_quality_charts import (
    MaintainabilityDeltaQualityChartPlaceholder,
    _build_delta_chart_data,
    _column_series_values,
    _resolve_delta_chart,
)
from report_generator.generator.utils.constants.metrics import DeltaType, MaintMetric

MODULE_PATH = (
    "report_generator.generator.placeholders.implementations.charts."
    "maintainability_delta_quality_charts"
)


class TestColumnSeriesValues:
    def test_duplication_collapses_to_two_series(self):
        # low risk becomes non-redundant; everything else becomes redundant.
        result = _column_series_values(MaintMetric.DUPLICATION, [97.0, 0.0, 0.0, 3.0])
        assert result == [97.0, 3.0]

    def test_duplication_sums_moderate_high_very_high_into_redundant(self):
        result = _column_series_values(MaintMetric.DUPLICATION, [90.0, 4.0, 3.0, 3.0])
        assert result[0] == 90.0
        assert abs(result[1] - 10.0) < 1e-9

    def test_four_bucket_metric_normalizes_to_100(self):
        result = _column_series_values(MaintMetric.UNIT_SIZE, [70.0, 17.0, 6.0, 10.0])
        assert len(result) == 4
        assert abs(sum(result) - 100.0) < 1e-9


class _StubSystemData:
    def __init__(self, columns, buckets_by_column):
        self._columns = columns
        self._buckets = buckets_by_column

    @property
    def columns(self):
        return self._columns

    def risk_buckets(self, metric, column):
        return self._buckets.get(column)


class TestBuildDeltaChartData:
    def _patched_by_type(self, columns, buckets_by_column):
        stub = _StubSystemData(columns, buckets_by_column)
        return {DeltaType.NEW_CODE: stub}

    def test_categories_are_column_labels(self):
        by_type = self._patched_by_type(
            [DeltaColumn.TOTAL_BEFORE, DeltaColumn.NEW_AFTER],
            {
                DeltaColumn.TOTAL_BEFORE: [70.0, 17.0, 6.0, 10.0],
                DeltaColumn.NEW_AFTER: [77.4, 17.0, 3.8, 1.8],
            },
        )
        with patch.object(
            module, "maintainability_delta_quality_system_by_type", by_type
        ):
            chart_data = _build_delta_chart_data(
                DeltaType.NEW_CODE, MaintMetric.UNIT_SIZE
            )
        assert [category.label for category in chart_data.categories] == [
            "Total code (Before)",
            "New code (After)",
        ]

    def test_four_series_for_regular_metric(self):
        by_type = self._patched_by_type(
            [DeltaColumn.TOTAL_BEFORE, DeltaColumn.NEW_AFTER],
            {
                DeltaColumn.TOTAL_BEFORE: [70.0, 17.0, 6.0, 10.0],
                DeltaColumn.NEW_AFTER: [77.4, 17.0, 3.8, 1.8],
            },
        )
        with patch.object(
            module, "maintainability_delta_quality_system_by_type", by_type
        ):
            chart_data = _build_delta_chart_data(
                DeltaType.NEW_CODE, MaintMetric.UNIT_SIZE
            )
        names = [series.name for series in chart_data]
        assert names == ["Low risk", "Medium risk", "High risk", "Very high risk"]

    def test_two_series_for_duplication(self):
        by_type = self._patched_by_type(
            [DeltaColumn.TOTAL_BEFORE, DeltaColumn.NEW_AFTER],
            {
                DeltaColumn.TOTAL_BEFORE: [97.0, 0.0, 0.0, 3.0],
                DeltaColumn.NEW_AFTER: [98.0, 0.0, 0.0, 2.0],
            },
        )
        with patch.object(
            module, "maintainability_delta_quality_system_by_type", by_type
        ):
            chart_data = _build_delta_chart_data(
                DeltaType.NEW_CODE, MaintMetric.DUPLICATION
            )
        names = [series.name for series in chart_data]
        assert names == ["Non-redundant", "Redundant"]

    def test_missing_buckets_default_to_zero(self):
        by_type = self._patched_by_type(
            [DeltaColumn.TOTAL_BEFORE, DeltaColumn.NEW_AFTER],
            {DeltaColumn.TOTAL_BEFORE: [70.0, 17.0, 6.0, 10.0]},  # NEW_AFTER missing
        )
        with patch.object(
            module, "maintainability_delta_quality_system_by_type", by_type
        ):
            chart_data = _build_delta_chart_data(
                DeltaType.NEW_CODE, MaintMetric.UNIT_SIZE
            )
        # The missing column contributes an all-zero bar without raising.
        low_risk = next(iter(chart_data))
        assert low_risk.values[1] == 0.0


class TestResolveDeltaChart:
    @patch(f"{MODULE_PATH}.rendering.pptx.find_charts")
    def test_no_charts_skips_value_cb(self, mock_find_charts):
        mock_find_charts.return_value = []
        value_cb = MagicMock()
        _resolve_delta_chart(MagicMock(), "KEY", value_cb)
        value_cb.assert_not_called()

    @patch(f"{MODULE_PATH}.rendering.pptx.find_charts")
    def test_replaces_data_and_scales_axis(self, mock_find_charts):
        chart = MagicMock()
        mock_find_charts.return_value = [chart]
        chart_data = MagicMock()
        value_cb = MagicMock(return_value=chart_data)

        _resolve_delta_chart(MagicMock(), "KEY", value_cb)

        value_cb.assert_called_once()
        chart.replace_data.assert_called_once_with(chart_data)
        assert chart.value_axis.minimum_scale == 0
        assert chart.value_axis.maximum_scale == 100


class TestChartPlaceholder:
    def test_key_and_doc_type(self):
        assert (
            MaintainabilityDeltaQualityChartPlaceholder.key
            == "DELTA_QUALITY_{type}_{metric}_CHART"
        )
        assert (
            MaintainabilityDeltaQualityChartPlaceholder.__doc_type__
            == PlaceholderDocType.CHART
        )

    def test_expands_to_fifteen_keys(self):
        import re

        ap = MaintainabilityDeltaQualityChartPlaceholder.allowed_parameters
        keys = set()
        for delta_type, metric in ap.product():
            key = MaintainabilityDeltaQualityChartPlaceholder.key
            for param in (delta_type, metric):
                key = re.sub(r"\{[^}]+\}", str(param), key, count=1)
            keys.add(key)
        assert len(keys) == 15
        assert "DELTA_QUALITY_NEW_CODE_UNIT_SIZE_CHART" in keys

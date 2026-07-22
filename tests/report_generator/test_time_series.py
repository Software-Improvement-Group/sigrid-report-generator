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

from datetime import date, datetime

from freezegun import freeze_time

from report_generator.generator.utils.time_series import (
    Period,
    add_months,
    parse_iso_datetime,
)


class TestAddMonths:
    def test_add_within_year(self):
        assert add_months(date(2025, 1, 15), 2) == date(2025, 3, 15)

    def test_subtract_across_year_boundary(self):
        assert add_months(date(2025, 1, 15), -1) == date(2024, 12, 15)
        assert add_months(date(2025, 6, 1), -12) == date(2024, 6, 1)

    def test_add_across_year_boundary(self):
        assert add_months(date(2025, 11, 10), 3) == date(2026, 2, 10)

    def test_day_clamped_to_short_month(self):
        # Jan 31 + 1 month has no Feb 31; clamp to the last valid day.
        assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)
        assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)  # leap year

    def test_preserves_datetime_time_component(self):
        assert add_months(datetime(2025, 1, 15, 9, 30), 1) == datetime(
            2025, 2, 15, 9, 30
        )


class TestParseIsoDatetime:
    def test_parses_naive_string(self):
        result = parse_iso_datetime("2026-03-10T00:00:00")
        assert result == datetime(2026, 3, 10, 0, 0, 0)
        assert result.tzinfo is None

    def test_parses_z_suffix_as_naive(self):
        result = parse_iso_datetime("2024-01-15T00:00:00Z")
        assert result == datetime(2024, 1, 15, 0, 0, 0)
        assert result.tzinfo is None

    def test_parses_offset_as_naive(self):
        result = parse_iso_datetime("2024-01-15T00:00:00+02:00")
        assert result.tzinfo is None


class TestTimeSeries:
    def test_period_contains(self):
        period = Period("2025-05-01", "2025-06-01")

        assert period.contains("2025-05-01")
        assert period.contains("2025-05-15")
        assert period.contains("2025-05-30")

        assert not period.contains("2025-04-30")
        assert not period.contains("2025-06-01")
        assert not period.contains("2025-06-02")

    def test_for_months(self):
        periods = Period.for_months("2025-01-15", "2025-04-15")

        assert len(periods) == 4
        assert str(periods[0]) == "2025-01-01 to 2025-02-01"
        assert str(periods[1]) == "2025-02-01 to 2025-03-01"
        assert str(periods[2]) == "2025-03-01 to 2025-04-01"
        assert str(periods[3]) == "2025-04-01 to 2025-05-01"

    @freeze_time("2025-07-22")
    def test_for_last_year_months(self):
        periods = Period.for_last_year_months()

        assert len(periods) == 12
        assert str(periods[0]) == "2024-08-01 to 2024-09-01"
        assert str(periods[-1]) == "2025-07-01 to 2025-08-01"

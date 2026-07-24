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

import calendar
from datetime import UTC, datetime


def add_months(d, months):
    """Shift a date/datetime by a whole number of months.

    The day is clamped to the length of the target month (e.g. Jan 31 + 1 month -> Feb 28/29).
    """
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)


def parse_iso_datetime(value: str) -> datetime:
    """Parse an ISO-8601 string (including a trailing 'Z') to a naive UTC datetime.

    Offset-bearing inputs are converted to UTC before tzinfo is stripped, so the
    naive result still represents the correct instant. tzinfo is stripped so results
    can be subtracted from a naive ``datetime.now()``; returning a tz-aware value
    would raise ``TypeError`` on live 'Z'-bearing API data.
    """
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo:
        return parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


def parse_date(date: str | datetime) -> datetime:
    if isinstance(date, datetime):
        return date
    return datetime.strptime(date[0:10], "%Y-%m-%d")


class Period:
    """Represents a time period between the start date (inclusive) and end date (exclusive)."""

    def __init__(self, start: str | datetime, end: str | datetime):
        self.start = parse_date(start)
        self.end = parse_date(end)

    def contains(self, date):
        if not date:
            return False
        date = parse_date(date)
        return self.start <= date < self.end

    def __str__(self):
        return f"{self.start.strftime('%Y-%m-%d')} to {self.end.strftime('%Y-%m-%d')}"

    @staticmethod
    def for_months(start: str | datetime, end: str | datetime):
        period_start = parse_date(start).replace(day=1)
        period_end = parse_date(end)
        months = []
        while period_start < period_end:
            period = Period(period_start, add_months(period_start, 1))
            period_start = period.end
            months.append(period)
        return months

    @staticmethod
    def for_last_year_months():
        today = datetime.now()
        last_year = add_months(today, -12)
        return Period.for_months(last_year, today)[-12:]

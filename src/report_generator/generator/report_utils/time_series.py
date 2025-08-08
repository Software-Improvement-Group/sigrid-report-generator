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
from dateutil.relativedelta import relativedelta


def parse_date(date):
    if isinstance(date, datetime):
        return date
    return datetime.strptime(date[0:10], "%Y-%m-%d")


class Period:
    """Represents a time period between the start date (inclusive) and end date (exclusive)."""

    def __init__(self, start, end):
        self.start = parse_date(start)
        self.end = parse_date(end)

    def contains(self, date):
        if not date:
            return False
        date = parse_date(date)
        return date >= self.start and date < self.end

    def __str__(self):
        return f"{self.start.strftime('%Y-%m-%d')} to {self.end.strftime('%Y-%m-%d')}"

    @staticmethod
    def for_months(start, end):
        period_start = parse_date(start).replace(day=1)
        months = []
        while period_start < parse_date(end):
            period = Period(period_start, period_start + relativedelta(months=1))
            period_start = period.end
            months.append(period)
        return months

    @staticmethod
    def for_last_year_months():
        today = datetime.now()
        last_year = today + relativedelta(months=-12)
        return Period.for_months(last_year, today)[-12:]

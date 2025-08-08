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

from report_generator.generator.report_utils.time_series import Period


class TestTimeSeries:
    def test_period_contains(self):
        period = Period("2025-05-01", "2025-06-01")

        assert period.contains("2025-05-01") == True
        assert period.contains("2025-05-15") == True
        assert period.contains("2025-05-30") == True

        assert period.contains("2025-04-30") == False
        assert period.contains("2025-06-01") == False
        assert period.contains("2025-06-02") == False

    def test_for_months(self):
        periods = Period.for_months("2025-01-15", "2025-04-15")

        assert len(periods) == 4
        assert str(periods[0]) == "2025-01-01 to 2025-02-01"
        assert str(periods[1]) == "2025-02-01 to 2025-03-01"
        assert str(periods[2]) == "2025-03-01 to 2025-04-01"
        assert str(periods[3]) == "2025-04-01 to 2025-05-01"

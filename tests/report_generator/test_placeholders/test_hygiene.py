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

import logging

from report_generator.generator.context import sigrid_api
from report_generator.generator.domain import (
    sigrid_hygiene_portfolio_data,
)
from report_generator.generator.placeholders.implementations.misc.category_chart import (
    UsersLastLoginChartPlaceholder,
)


class TestPortfolioHygienePlaceholders:
    """Test cases for hygiene report generation placeholders."""

    def test_users_last_login_chart_access_denied_returns_empty_series(
        self, mocker, caplog
    ):
        """Test that UsersLastLoginChartPlaceholder handles access-denied errors gracefully."""

        # Arrange: mock all three calls to raise the exception
        mocker.patch.object(
            sigrid_hygiene_portfolio_data,
            "get_last_access_time_users",
            side_effect=sigrid_api.SigridAccessDeniedError(
                url="fake_url", customer="fake_customer", system="fake_system"
            ),
        )

        # Capture log output
        caplog.set_level(logging.WARNING)

        # Act
        result = UsersLastLoginChartPlaceholder.series()

        # Expected: result should be 3 identical series of the same length filled with 0's
        assert len(result) == 3

        assert result[0] == result[1] == result[2]

        for series in result:
            assert all(x == 0 for x in series)

        # Assert that warning log was produced
        assert "access denied (403)" in caplog.text

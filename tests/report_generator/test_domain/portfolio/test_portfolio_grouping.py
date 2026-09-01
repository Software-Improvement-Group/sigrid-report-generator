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

import pytest

from report_generator.generator.context import portfolio_metadata
from report_generator.generator.domain.portfolio.portfolio_grouping import (
    portfolio_grouping,
)


@pytest.fixture(autouse=True)
def reset_grouping_context():
    portfolio_metadata.reset_group_by()
    yield
    portfolio_metadata.reset_group_by()


class TestPortfolioGrouping:
    def test_selected_reflects_context_default(self):
        assert portfolio_grouping.selected == "team"

    def test_selected_reflects_context_after_set(self):
        portfolio_metadata.set_group_by("business_criticality")

        assert portfolio_grouping.selected == "business_criticality"

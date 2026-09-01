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

from report_generator.generator.context import portfolio_metadata
from report_generator.generator.domain.portfolio.portfolio_filter_info import (
    portfolio_filter_info,
)


class TestPortfolioFilterInfo:
    def test_applied_filters_empty_by_default(self):
        portfolio_metadata.reset_context()

        assert portfolio_filter_info.applied_filters == []

    def test_applied_filters_reflects_context_after_set(self):
        portfolio_metadata.set_context(team=["TeamA"])

        try:
            applied = portfolio_filter_info.applied_filters
        finally:
            portfolio_metadata.reset_context()

        assert len(applied) == 1
        assert applied[0].name == "team"
        assert applied[0].values == ["TeamA"]

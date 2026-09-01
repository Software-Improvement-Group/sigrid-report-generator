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

from report_generator.generator.context.portfolio_metadata import get_group_by


class PortfolioGrouping:
    """Exposes the metadata dimension portfolio treemaps are currently grouped by."""

    @property
    def selected(self) -> str:
        return get_group_by()


portfolio_grouping = PortfolioGrouping()

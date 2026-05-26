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

from report_generator.generator.domain import security_ratings_portfolio_data
from report_generator.generator.placeholders.implementations.table.findings_table_base import (
    FindingsTopSystemsTableBase,
)


class SecurityFindingsTopSystemsTable(FindingsTopSystemsTableBase):
    """Table of the top 10 systems with the most open security findings above objective. Headers are: System, Objective set, Findings above objective, Rating, Link."""

    key = "SECURITY_FINDINGS_TOP_SYSTEMS_TABLE"
    _url_path = "security"

    @classmethod
    def _get_systems(cls) -> list[dict]:
        return security_ratings_portfolio_data.top_systems_by_findings_above_objective

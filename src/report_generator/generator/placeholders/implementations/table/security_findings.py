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

from report_generator.generator.context import sigrid_api
from report_generator.generator.domain import security_ratings_portfolio_data
from report_generator.generator.placeholders.formatting.formatters import (
    calculate_stars,
)
from report_generator.generator.placeholders.implementations.table.base import (
    Hyperlink,
    TableMatrix,
    TablePlaceholder,
)

_TOP_N = 10


class SecurityFindingsTopSystemsTable(TablePlaceholder):
    """Table of the top 10 systems with the most open security findings above objective. Headers are: System, Objective set, Findings above objective, Rating, Link."""

    key = "SECURITY_FINDINGS_TOP_SYSTEMS_TABLE"

    @classmethod
    def value(cls) -> TableMatrix:
        systems = (
            security_ratings_portfolio_data.top_systems_by_findings_above_objective(
                _TOP_N
            )
        )
        return cls._to_table_matrix(systems)

    @classmethod
    def _format_row(cls, entry: dict) -> list:
        system_name = entry["systemName"]
        rating = entry.get("rating")
        objective_target = entry.get("objective_target")
        return [
            system_name,
            f"\u2265 {objective_target.title()}" if objective_target else "N/A",
            entry["findings_above_objective"],
            calculate_stars(rating) if rating is not None else "N/A",
            Hyperlink(
                "link",
                f"https://sigrid-says.com/{sigrid_api._customer}/{system_name}/-/security",
            ),
        ]

    @classmethod
    def _to_table_matrix(cls, systems: list[dict]) -> TableMatrix:
        header: TableMatrix = [
            ["System", "Objective set", "Findings above objective", "Rating", "Link"]
        ]
        return header + [cls._format_row(entry) for entry in systems]

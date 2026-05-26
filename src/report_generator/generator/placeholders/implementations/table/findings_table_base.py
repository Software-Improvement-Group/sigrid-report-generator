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

from abc import abstractmethod

from report_generator.generator.context import sigrid_api
from report_generator.generator.placeholders.formatting.formatters import (
    print_star,
    star_rating_round,
)
from report_generator.generator.placeholders.implementations.table.base import (
    Hyperlink,
    TableMatrix,
    TablePlaceholder,
)

_TOP_N = 10
_HEADER = [
    "System",
    "Objective set",
    "Findings above objective",
    "Rating",
    "Sigrid Link",
]


class FindingsTopSystemsTableBase(TablePlaceholder):
    """Abstract base for top-N findings tables (security, reliability)."""

    _url_path: str = ""

    @classmethod
    @abstractmethod
    def _get_systems(cls, limit: int) -> list[dict]:
        """Return top systems from the relevant domain data object."""

    @classmethod
    def value(cls) -> TableMatrix:
        return cls._to_table_matrix(cls._get_systems(_TOP_N))

    @classmethod
    def _format_row(cls, entry: dict) -> list:
        system_name = entry["systemName"]
        rating = entry.get("rating")
        objective_target = entry.get("objective_target")
        return [
            entry["displayName"],
            f"\u2265 {objective_target.title()}" if objective_target else "N/A",
            entry["findings_above_objective"],
            f"{star_rating_round(rating)}{print_star()}"
            if rating is not None
            else "N/A",
            Hyperlink(
                "link",
                f"https://sigrid-says.com/{sigrid_api._customer}/{system_name}/-/{cls._url_path}",
            ),
        ]

    @classmethod
    def _to_table_matrix(cls, systems: list[dict]) -> TableMatrix:
        return [_HEADER] + [cls._format_row(entry) for entry in systems]

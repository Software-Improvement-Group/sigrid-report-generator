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
from report_generator.generator.domain import maintainability_portfolio_data
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
_HEADER = ["System", "Maintainability Rating", "Volume (in PY)", "Sigrid Link"]


class MaintainabilityTopSystemsTable(TablePlaceholder):
    """Table of the top 10 systems with the lowest maintainability rating. Headers are: System, Maintainability Rating, Volume (in PY), Sigrid Link."""

    key = "MAINTAINABILITY_TOP_SYSTEMS_TABLE"

    @classmethod
    def value(cls) -> TableMatrix:
        systems = (
            maintainability_portfolio_data.bottom_systems_by_maintainability_rating[
                :_TOP_N
            ]
        )
        return [_HEADER] + [cls._format_row(entry) for entry in systems]

    @classmethod
    def _format_row(cls, entry: dict) -> list:
        system_name = entry["systemName"]
        return [
            entry["displayName"],
            f"{star_rating_round(entry['rating'])}{print_star()}",
            entry["volume_py"],
            Hyperlink(
                "link",
                f"https://sigrid-says.com/{sigrid_api._customer}/{system_name}/-/maintainability",
            ),
        ]

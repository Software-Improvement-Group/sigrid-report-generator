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
from report_generator.generator.domain import (
    maintainability_portfolio_data,
    npr_5333_functional_suitability_portfolio_data,
)
from report_generator.generator.placeholders.formatting.formatters import (
    ratio_to_percentage,
)
from report_generator.generator.placeholders.implementations.table.base import (
    Hyperlink,
    TableMatrix,
    TablePlaceholder,
)

_TOP_N = 10
_HEADER = ["System", "Test Code Ratio", "Open CWEs", "Sigrid Link"]


class FunctionalSuitabilityTopSystemsTable(TablePlaceholder):
    """Table of the top 10 systems with the most open functional suitability CWEs. Headers are: System, Test Code Ratio, Open CWEs, Sigrid Link."""

    key = "FUNCTIONAL_SUITABILITY_TOP_SYSTEMS_TABLE"

    @classmethod
    def value(cls) -> TableMatrix:
        systems = (
            npr_5333_functional_suitability_portfolio_data.top_systems_by_finding_count[
                :_TOP_N
            ]
        )
        return [_HEADER] + [cls._format_row(entry) for entry in systems]

    @classmethod
    def _format_row(cls, entry: dict) -> list:
        system_name = entry["systemName"]
        snapshot = maintainability_portfolio_data.end_snapshot(system_name)
        test_code_ratio = snapshot.get("testCodeRatio") if snapshot else None
        display_name = maintainability_portfolio_data.get_system_display_name(
            system_name
        )
        return [
            display_name,
            ratio_to_percentage(test_code_ratio)
            if test_code_ratio is not None
            else "N/A",
            entry["finding_count"],
            Hyperlink(
                "link",
                f"https://sigrid-says.com/{sigrid_api._customer}/{system_name}/-/overview",
            ),
        ]

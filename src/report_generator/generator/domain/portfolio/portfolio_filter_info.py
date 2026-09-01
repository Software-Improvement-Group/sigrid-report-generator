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

from typing import NamedTuple

from report_generator.generator.context.portfolio_metadata import (
    FILTER_CONFIGURATION,
    FilterSpec,
    get_filter_values,
)


class AppliedFilter(NamedTuple):
    name: str
    values: list[str]


class PortfolioFilterInfo:
    """Exposes the portfolio filters the report is currently filtered on."""

    @property
    def applied_filters(self) -> list[AppliedFilter]:
        applied = []
        for name, spec in FILTER_CONFIGURATION.items():
            values = get_filter_values(name)
            if values:
                applied.append(
                    AppliedFilter(name, [self._label(spec, v) for v in values])
                )
        return applied

    @staticmethod
    def _label(spec: FilterSpec, value: str) -> str:
        if spec.value_mapping:
            return spec.value_mapping.get(value, value)
        return value


portfolio_filter_info = PortfolioFilterInfo()

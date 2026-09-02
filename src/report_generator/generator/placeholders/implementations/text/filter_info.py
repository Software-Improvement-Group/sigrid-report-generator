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

from report_generator.generator.domain import portfolio_filter_info
from report_generator.generator.utils.constants.metadata_labels import METADATA_LABELS

from .base import text_placeholder


@text_placeholder()
def filter_info():
    """A comma-separated description of every portfolio filter applied to the report. Each
    filter is prefixed with its label, singular for a single value or plural for multiple
    (e.g. "team: teamA, divisions: divA, divB"). Empty when no filter is applied."""
    segments = []
    for applied in portfolio_filter_info.applied_filters:
        singular, plural = METADATA_LABELS[applied.name]
        label = singular if len(applied.values) == 1 else plural
        segments.append(f"{label}: {', '.join(applied.values)}")
    return ", ".join(segments)

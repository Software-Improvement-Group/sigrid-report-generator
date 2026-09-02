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

from report_generator.generator.placeholders.context import get_group_by
from report_generator.generator.utils.constants.metadata_labels import METADATA_LABELS

from .base import text_placeholder


@text_placeholder()
def grouped_by_label():
    """The human-readable label of the metadata dimension all portfolio treemaps are
    currently grouped by (e.g. "Team", "Lifecycle phase"), following the --group-by
    CLI parameter."""
    singular, _ = METADATA_LABELS[get_group_by()]
    return singular.title()

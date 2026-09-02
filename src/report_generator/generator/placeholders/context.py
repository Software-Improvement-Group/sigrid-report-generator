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

from report_generator.generator.utils.constants.metadata_labels import METADATA_LABELS

GROUPING_OPTIONS: tuple[str, ...] = tuple(METADATA_LABELS.keys())
DEFAULT_GROUP_BY = "team"

_group_by: str = DEFAULT_GROUP_BY


def set_group_by(group_by: str) -> None:
    if group_by not in GROUPING_OPTIONS:
        raise ValueError(
            f"Invalid group-by value: {group_by}. Allowed: {', '.join(GROUPING_OPTIONS)}"
        )
    global _group_by
    _group_by = group_by


def reset_group_by() -> None:
    global _group_by
    _group_by = DEFAULT_GROUP_BY


def get_group_by() -> str:
    return _group_by

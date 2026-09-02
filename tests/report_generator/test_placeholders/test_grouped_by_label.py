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

import pytest

from report_generator.generator.placeholders import context as placeholders_context
from report_generator.generator.placeholders.implementations.text.grouped_by_label import (
    grouped_by_label,
)


@pytest.fixture(autouse=True)
def reset_grouping_context():
    placeholders_context.reset_group_by()
    yield
    placeholders_context.reset_group_by()


class TestGroupedByLabelPlaceholder:
    def test_key_is_grouped_by_label(self):
        assert grouped_by_label.key == "GROUPED_BY_LABEL"

    def test_defaults_to_team_label(self):
        assert grouped_by_label.value() == "Team"

    def test_reflects_selected_grouping(self):
        placeholders_context.set_group_by("lifecycle")

        assert grouped_by_label.value() == "Lifecycle Phase"

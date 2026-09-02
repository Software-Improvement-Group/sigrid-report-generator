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

from report_generator.generator.placeholders.context import (
    get_group_by,
    reset_group_by,
    set_group_by,
)


class TestGroupBy:
    def teardown_method(self):
        reset_group_by()

    def test_defaults_to_team(self):
        assert get_group_by() == "team"

    def test_set_group_by_updates_selected_grouping(self):
        set_group_by("lifecycle")

        assert get_group_by() == "lifecycle"

    def test_set_group_by_rejects_unknown_dimension(self):
        with pytest.raises(ValueError, match="Invalid group-by value"):
            set_group_by("not-a-real-dimension")

    def test_reset_group_by_restores_default(self):
        set_group_by("supplier")
        reset_group_by()

        assert get_group_by() == "team"

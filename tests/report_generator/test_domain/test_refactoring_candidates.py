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

from report_generator.generator.context.sigrid_api import SigridAPIRequestFailedError
from report_generator.generator.domain.system.maintainability import (
    maintainability_data,
)
from report_generator.generator.domain.system.refactoring_candidates import (
    refactoring_candidates_data,
)
from report_generator.generator.utils.constants import MaintMetric


def _mock_sorted_tech(mocker, tech_names):
    mocker.patch.object(
        type(maintainability_data),
        "sorted_tech",
        new_callable=mocker.PropertyMock,
        return_value=[{"name": name} for name in tech_names],
    )


def _mock_candidates(mocker, candidates):
    mocker.patch.object(
        refactoring_candidates_data, "get_candidates", return_value=candidates
    )


class TestGetCandidatesForTechnology:
    def test_returns_only_matching_technology(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        _mock_candidates(
            mocker,
            [
                {"technology": "csharp", "name": "Foo"},
                {"technology": "java", "name": "Bar"},
                {"technology": "csharp", "name": "Baz"},
            ],
        )
        result = refactoring_candidates_data.get_candidates_for_technology(
            MaintMetric.UNIT_SIZE, 1
        )
        assert [c["name"] for c in result] == ["Foo", "Baz"]

    def test_raises_when_technology_has_no_candidates(self, mocker):
        _mock_sorted_tech(mocker, ["csharp", "java"])
        _mock_candidates(mocker, [{"technology": "csharp", "name": "Foo"}])
        with pytest.raises(SigridAPIRequestFailedError):
            refactoring_candidates_data.get_candidates_for_technology(
                MaintMetric.UNIT_SIZE, 2
            )

    def test_raises_for_out_of_range_index(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        _mock_candidates(mocker, [{"technology": "csharp", "name": "Foo"}])
        with pytest.raises(SigridAPIRequestFailedError):
            refactoring_candidates_data.get_candidates_for_technology(
                MaintMetric.UNIT_SIZE, 5
            )

    def test_raises_for_others(self, mocker):
        _mock_sorted_tech(mocker, ["others"])
        _mock_candidates(mocker, [{"technology": "others", "name": "Foo"}])
        with pytest.raises(SigridAPIRequestFailedError):
            refactoring_candidates_data.get_candidates_for_technology(
                MaintMetric.UNIT_SIZE, 1
            )

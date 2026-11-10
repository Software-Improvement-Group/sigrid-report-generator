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
from report_generator.generator.placeholders.implementations.table.refactoring_candidates import (
    RefactoringCandidatesTableComponentIndependenceTech,
    RefactoringCandidatesTableDuplicationTech,
    RefactoringCandidatesTableModuleCouplingTech,
    RefactoringCandidatesTableUnitComplexityTech,
    RefactoringCandidatesTableUnitInterfacingTech,
    RefactoringCandidatesTableUnitSizeTech,
)


def _mock_sorted_tech(mocker, tech_names):
    techs = [{"name": name} for name in tech_names]
    mocker.patch.object(
        type(maintainability_data),
        "sorted_tech",
        new_callable=mocker.PropertyMock,
        return_value=techs,
    )


class TestRefactoringCandidatesTableDuplicationTech:
    def test_key(self):
        assert (
            RefactoringCandidatesTableDuplicationTech.key
            == "REFACTORING_CANDIDATES_TABLE_DUPLICATION_TECH_{tech_idx}"
        )

    def test_allowed_parameters(self):
        assert RefactoringCandidatesTableDuplicationTech.allowed_parameters.param_lists[
            0
        ] == [1, 2, 3, 4]

    def test_value_filters_candidates(self, mocker):
        _mock_sorted_tech(mocker, ["csharp", "java"])
        mocker.patch.object(
            refactoring_candidates_data,
            "get_candidates",
            return_value=[
                {
                    "technology": "csharp",
                    "loc": 10,
                    "locations": [{"file": "Foo.cs"}],
                    "sameFile": True,
                    "sameComponent": False,
                },
                {
                    "technology": "java",
                    "loc": 5,
                    "locations": [{"file": "Bar.java"}],
                    "sameFile": False,
                    "sameComponent": True,
                },
            ],
        )
        result = RefactoringCandidatesTableDuplicationTech.value(1)
        assert result[0] == ["Description", "Redundant LOC", "Level", "Technology"]
        assert len(result) == 2  # header + 1 csharp row

    def test_value_raises_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        with pytest.raises(SigridAPIRequestFailedError):
            RefactoringCandidatesTableDuplicationTech.value(4)


class TestRefactoringCandidatesTableUnitSizeTech:
    def test_key(self):
        assert (
            RefactoringCandidatesTableUnitSizeTech.key
            == "REFACTORING_CANDIDATES_TABLE_UNIT_SIZE_TECH_{tech_idx}"
        )

    def test_allowed_parameters(self):
        assert RefactoringCandidatesTableUnitSizeTech.allowed_parameters.param_lists[
            0
        ] == [1, 2, 3, 4]

    def test_value_filters_candidates(self, mocker):
        _mock_sorted_tech(mocker, ["csharp", "java"])
        mocker.patch.object(
            refactoring_candidates_data,
            "get_candidates",
            return_value=[
                {"technology": "csharp", "name": "Foo", "loc": 50, "component": "Core"},
                {"technology": "java", "name": "Bar", "loc": 30, "component": "Api"},
            ],
        )
        result = RefactoringCandidatesTableUnitSizeTech.value(1)
        assert result[0] == [
            "Unit name",
            "LOC",
            "McCabe",
            "Parameters",
            "Component",
            "Technology",
        ]
        assert len(result) == 2  # header + 1 csharp row

    def test_value_raises_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        with pytest.raises(SigridAPIRequestFailedError):
            RefactoringCandidatesTableUnitSizeTech.value(4)


class TestRefactoringCandidatesTableUnitComplexityTech:
    def test_key(self):
        assert (
            RefactoringCandidatesTableUnitComplexityTech.key
            == "REFACTORING_CANDIDATES_TABLE_UNIT_COMPLEXITY_TECH_{tech_idx}"
        )

    def test_allowed_parameters(self):
        assert (
            RefactoringCandidatesTableUnitComplexityTech.allowed_parameters.param_lists[
                0
            ]
            == [1, 2, 3, 4]
        )

    def test_value_raises_for_others_tech(self, mocker):
        _mock_sorted_tech(mocker, ["others"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        with pytest.raises(SigridAPIRequestFailedError):
            RefactoringCandidatesTableUnitComplexityTech.value(1)


class TestRefactoringCandidatesTableUnitInterfacingTech:
    def test_key(self):
        assert (
            RefactoringCandidatesTableUnitInterfacingTech.key
            == "REFACTORING_CANDIDATES_TABLE_UNIT_INTERFACING_TECH_{tech_idx}"
        )

    def test_allowed_parameters(self):
        assert (
            RefactoringCandidatesTableUnitInterfacingTech.allowed_parameters.param_lists[
                0
            ]
            == [1, 2, 3, 4]
        )

    def test_value_raises_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        with pytest.raises(SigridAPIRequestFailedError):
            RefactoringCandidatesTableUnitInterfacingTech.value(4)


class TestRefactoringCandidatesTableModuleCouplingTech:
    def test_key(self):
        assert (
            RefactoringCandidatesTableModuleCouplingTech.key
            == "REFACTORING_CANDIDATES_TABLE_MODULE_COUPLING_TECH_{tech_idx}"
        )

    def test_allowed_parameters(self):
        assert (
            RefactoringCandidatesTableModuleCouplingTech.allowed_parameters.param_lists[
                0
            ]
            == [1, 2, 3, 4]
        )

    def test_value_filters_candidates(self, mocker):
        _mock_sorted_tech(mocker, ["csharp", "java"])
        mocker.patch.object(
            refactoring_candidates_data,
            "get_candidates",
            return_value=[
                {
                    "technology": "csharp",
                    "file": "src/Foo.cs",
                    "fanIn": 5,
                    "component": "Core",
                },
                {
                    "technology": "java",
                    "file": "src/Bar.java",
                    "fanIn": 3,
                    "component": "Api",
                },
            ],
        )
        result = RefactoringCandidatesTableModuleCouplingTech.value(2)
        assert result[0] == ["File name", "LOC", "Fan-in", "Component", "Technology"]
        assert len(result) == 2  # header + 1 java row

    def test_value_raises_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        with pytest.raises(SigridAPIRequestFailedError):
            RefactoringCandidatesTableModuleCouplingTech.value(4)


class TestRefactoringCandidatesTableComponentIndependenceTech:
    def test_key(self):
        assert (
            RefactoringCandidatesTableComponentIndependenceTech.key
            == "REFACTORING_CANDIDATES_TABLE_COMPONENT_INDEPENDENCE_TECH_{tech_idx}"
        )

    def test_allowed_parameters(self):
        assert (
            RefactoringCandidatesTableComponentIndependenceTech.allowed_parameters.param_lists[
                0
            ]
            == [1, 2, 3, 4]
        )

    def test_value_filters_candidates(self, mocker):
        _mock_sorted_tech(mocker, ["csharp", "java"])
        mocker.patch.object(
            refactoring_candidates_data,
            "get_candidates",
            return_value=[
                {"technology": "csharp", "file": "src/Foo.cs", "component": "Core"},
                {"technology": "java", "file": "src/Bar.java", "component": "Api"},
            ],
        )
        result = RefactoringCandidatesTableComponentIndependenceTech.value(1)
        assert result[0] == ["File name", "LOC", "Component", "Technology"]
        assert len(result) == 2  # header + 1 csharp row

    def test_value_raises_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        with pytest.raises(SigridAPIRequestFailedError):
            RefactoringCandidatesTableComponentIndependenceTech.value(4)

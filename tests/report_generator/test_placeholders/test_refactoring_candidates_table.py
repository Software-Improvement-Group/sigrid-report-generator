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
    _filter_by_technology,
    _get_technology_name_at_index,
)


def _mock_sorted_tech(mocker, tech_names):
    techs = [{"name": name} for name in tech_names]
    mocker.patch.object(
        type(maintainability_data),
        "sorted_tech",
        new_callable=mocker.PropertyMock,
        return_value=techs,
    )


class TestTechnologyHelpers:
    def test_out_of_range_index_returns_none(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        assert _get_technology_name_at_index(2) is None

    def test_others_name_returns_none(self, mocker):
        _mock_sorted_tech(mocker, ["others"])
        assert _get_technology_name_at_index(1) is None

    def test_valid_index_returns_name(self, mocker):
        _mock_sorted_tech(mocker, ["csharp", "java"])
        assert _get_technology_name_at_index(1) == "csharp"
        assert _get_technology_name_at_index(2) == "java"

    def test_filter_returns_only_matching_technology(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        candidates = [
            {"technology": "csharp", "name": "Foo"},
            {"technology": "java", "name": "Bar"},
            {"technology": "csharp", "name": "Baz"},
        ]
        result = _filter_by_technology(candidates, 1)
        assert len(result) == 2
        assert all(c["technology"] == "csharp" for c in result)

    def test_filter_returns_empty_for_out_of_range(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        candidates = [{"technology": "csharp", "name": "Foo"}]
        assert _filter_by_technology(candidates, 5) == []

    def test_filter_returns_empty_for_others(self, mocker):
        _mock_sorted_tech(mocker, ["others"])
        candidates = [{"technology": "others", "name": "Foo"}]
        assert _filter_by_technology(candidates, 1) == []


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

    def test_value_returns_header_only_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        result = RefactoringCandidatesTableDuplicationTech.value(4)
        assert result == [["Description", "Redundant LOC", "Level", "Technology"]]


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

    def test_value_returns_header_only_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        result = RefactoringCandidatesTableUnitSizeTech.value(4)
        assert result == [
            ["Unit name", "LOC", "McCabe", "Parameters", "Component", "Technology"]
        ]


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

    def test_value_returns_header_only_for_others_tech(self, mocker):
        _mock_sorted_tech(mocker, ["others"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        result = RefactoringCandidatesTableUnitComplexityTech.value(1)
        assert result == [
            ["Unit name", "LOC", "McCabe", "Parameters", "Component", "Technology"]
        ]


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

    def test_value_returns_header_only_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        result = RefactoringCandidatesTableUnitInterfacingTech.value(4)
        assert result == [
            ["Unit name", "LOC", "McCabe", "Parameters", "Component", "Technology"]
        ]


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

    def test_value_returns_header_only_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        result = RefactoringCandidatesTableModuleCouplingTech.value(4)
        assert result == [["File name", "LOC", "Fan-in", "Component", "Technology"]]


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

    def test_value_returns_header_only_for_out_of_range_tech(self, mocker):
        _mock_sorted_tech(mocker, ["csharp"])
        mocker.patch.object(
            refactoring_candidates_data, "get_candidates", return_value=[]
        )
        result = RefactoringCandidatesTableComponentIndependenceTech.value(4)
        assert result == [["File name", "LOC", "Component", "Technology"]]

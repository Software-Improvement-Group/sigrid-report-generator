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

from abc import ABC, abstractmethod

from report_generator.generator.domain import refactoring_candidates_data
from report_generator.generator.domain.system.maintainability import (
    maintainability_data,
)
from report_generator.generator.placeholders.formatting.technologies import (
    get_technology_name,
)
from report_generator.generator.placeholders.implementations.base import (
    ParameterizedPlaceholder,
)
from report_generator.generator.placeholders.implementations.table.base import (
    TableMatrix,
    TablePlaceholder,
)
from report_generator.generator.utils.constants import MaintMetric


class _AbstractRefactoringCandidatesTablePlaceholder(TablePlaceholder):
    metric: MaintMetric

    @classmethod
    @abstractmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        pass

    @classmethod
    def value(cls) -> TableMatrix:
        return cls._to_table_matrix(
            refactoring_candidates_data.get_candidates(cls.metric)
        )


class RefactoringCandidatesTableDuplication(
    _AbstractRefactoringCandidatesTablePlaceholder
):
    """Table for refactoring candidates related to code duplication. Headers are: Description, Redundant LOC, Level, Technology."""

    metric = MaintMetric.DUPLICATION
    key = "REFACTORING_CANDIDATES_TABLE_DUPLICATION"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [["Description", "Redundant LOC", "Level", "Technology"]]

        for finding in data:
            locs: list = finding["locations"]

            unique_filenames = sorted({loc["file"].split("/")[-1] for loc in locs})

            rows.append(
                [
                    f"{finding['loc']} lines occurring {len(locs)} times in {', '.join(unique_filenames)}",
                    finding["loc"] * (len(locs) - 1),
                    "File"
                    if finding["sameFile"]
                    else "Component"
                    if finding["sameComponent"]
                    else "System",
                    get_technology_name(finding["technology"]),
                ]
            )

        return rows


class RefactoringCandidatesTableUnitSize(
    _AbstractRefactoringCandidatesTablePlaceholder
):
    """Table for refactoring candidates related to unit size. Headers are: Unit name, LOC, McCabe, Parameters, Component, Technology."""

    metric = MaintMetric.UNIT_SIZE
    key = "REFACTORING_CANDIDATES_TABLE_UNIT_SIZE"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [["Unit name", "LOC", "McCabe", "Parameters", "Component", "Technology"]]
        rows.extend(
            [
                finding["name"],
                finding["loc"],
                finding.get("mcCabe", "-"),
                finding.get("parameters", "-"),
                finding["component"],
                get_technology_name(finding["technology"]),
            ]
            for finding in data
        )
        return rows


class RefactoringCandidatesTableUnitComplexity(
    _AbstractRefactoringCandidatesTablePlaceholder
):
    """Table for refactoring candidates related to unit complexity. Headers are: Unit name, LOC, McCabe, Parameters, Component, Technology."""

    metric = MaintMetric.UNIT_COMPLEXITY
    key = "REFACTORING_CANDIDATES_TABLE_UNIT_COMPLEXITY"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [["Unit name", "LOC", "McCabe", "Parameters", "Component", "Technology"]]
        rows.extend(
            [
                finding["name"],
                finding.get("loc", "-"),
                finding["mcCabe"],
                finding.get("parameters", "-"),
                finding["component"],
                get_technology_name(finding["technology"]),
            ]
            for finding in data
        )
        return rows


class RefactoringCandidatesTableUnitInterfacing(
    _AbstractRefactoringCandidatesTablePlaceholder
):
    """Table for refactoring candidates related to unit interfacing. Headers are: Unit name, LOC, McCabe, Parameters, Component, Technology."""

    metric = MaintMetric.UNIT_INTERFACING
    key = "REFACTORING_CANDIDATES_TABLE_UNIT_INTERFACING"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [["Unit name", "LOC", "McCabe", "Parameters", "Component", "Technology"]]
        rows.extend(
            [
                finding["name"],
                finding.get("loc", "-"),
                finding.get("mcCabe", "-"),
                finding["parameters"],
                finding["component"],
                get_technology_name(finding["technology"]),
            ]
            for finding in data
        )
        return rows


class RefactoringCandidatesTableModuleCoupling(
    _AbstractRefactoringCandidatesTablePlaceholder
):
    """Table for refactoring candidates related to module coupling. Headers are: File name, LOC, Fan-in, Component, Technology."""

    metric = MaintMetric.MODULE_COUPLING
    key = "REFACTORING_CANDIDATES_TABLE_MODULE_COUPLING"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [["File name", "LOC", "Fan-in", "Component", "Technology"]]
        rows.extend(
            [
                finding["file"].split("/")[-1],
                finding.get("loc", "-"),
                finding["fanIn"],
                finding["component"],
                get_technology_name(finding["technology"]),
            ]
            for finding in data
        )
        return rows


class RefactoringCandidatesTableComponentEntanglement(
    _AbstractRefactoringCandidatesTablePlaceholder
):
    """Table for refactoring candidates related to component entanglement. Headers are: Description, Weight."""

    metric = MaintMetric.COMPONENT_ENTANGLEMENT
    key = "REFACTORING_CANDIDATES_TABLE_COMPONENT_ENTANGLEMENT"

    @staticmethod
    def _generate_description(finding) -> str:
        entanglement_type = finding["type"]

        if entanglement_type == "COMMUNICATION_DENSITY":
            severity = finding["severity"].replace("_", " ").capitalize()
            component_name = finding["component"]
            return f"{severity} communication density on {component_name}"

        # Check if type is valid (you'll need to implement this based on your validation logic)
        special_type_names = {
            "LAYER_BYPASSING_DEPENDENCY": "transitive dependency",
        }

        base_description = special_type_names.get(
            entanglement_type, entanglement_type.replace("_", " ").lower()
        ).capitalize()
        source_component = finding["sourceComponent"]
        target_component = finding["targetComponent"]

        return f"{base_description} between {source_component} and {target_component}"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [["Description", "Weight"]]
        rows.extend(
            [
                RefactoringCandidatesTableComponentEntanglement._generate_description(
                    finding
                ),
                finding["weight"],
            ]
            for finding in data
        )
        return rows


class RefactoringCandidatesTableComponentIndependence(
    _AbstractRefactoringCandidatesTablePlaceholder
):
    """Table for refactoring candidates related to component independence. Headers are: File name, LOC, Component, Technology."""

    metric = MaintMetric.COMPONENT_INDEPENDENCE
    key = "REFACTORING_CANDIDATES_TABLE_COMPONENT_INDEPENDENCE"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [["File name", "LOC", "Component", "Technology"]]
        rows.extend(
            [
                finding["file"].split("/")[-1],
                finding.get("loc", "-"),
                finding["component"],
                get_technology_name(finding["technology"]),
            ]
            for finding in data
        )
        return rows


def _get_technology_name_at_index(tech_index: int) -> str | None:
    name = maintainability_data.sorted_tech_get_key(tech_index - 1, "name", None)
    return None if name in (None, "others") else name


def _filter_by_technology(candidates: list, tech_index: int) -> list:
    name = _get_technology_name_at_index(tech_index)
    if name is None:
        return []
    return [c for c in candidates if c.get("technology") == name]


class _AbstractRefactoringCandidatesTableTechPlaceholder(
    ParameterizedPlaceholder, _AbstractRefactoringCandidatesTablePlaceholder, ABC
):
    """Mixin that adds per-technology filtering to a refactoring candidates table.

    Must be combined with a concrete original table class that supplies `metric`
    and `_to_table_matrix`. Concrete subclasses only need to declare a `key`.
    """

    allowed_parameters = (1, 2, 3, 4)

    @classmethod
    def value(cls, tech_index: int) -> TableMatrix:
        candidates = refactoring_candidates_data.get_candidates(cls.metric)
        return cls._to_table_matrix(_filter_by_technology(candidates, tech_index))


class RefactoringCandidatesTableDuplicationTech(
    _AbstractRefactoringCandidatesTableTechPlaceholder,
    RefactoringCandidatesTableDuplication,
):
    """Table for refactoring candidates related to code duplication, filtered by technology. Headers are: Description, Redundant LOC, Level, Technology."""

    key = "REFACTORING_CANDIDATES_TABLE_DUPLICATION_TECH_{tech_idx}"


class RefactoringCandidatesTableUnitSizeTech(
    _AbstractRefactoringCandidatesTableTechPlaceholder,
    RefactoringCandidatesTableUnitSize,
):
    """Table for refactoring candidates related to unit size, filtered by technology. Headers are: Unit name, LOC, McCabe, Parameters, Component, Technology."""

    key = "REFACTORING_CANDIDATES_TABLE_UNIT_SIZE_TECH_{tech_idx}"


class RefactoringCandidatesTableUnitComplexityTech(
    _AbstractRefactoringCandidatesTableTechPlaceholder,
    RefactoringCandidatesTableUnitComplexity,
):
    """Table for refactoring candidates related to unit complexity, filtered by technology. Headers are: Unit name, LOC, McCabe, Parameters, Component, Technology."""

    key = "REFACTORING_CANDIDATES_TABLE_UNIT_COMPLEXITY_TECH_{tech_idx}"


class RefactoringCandidatesTableUnitInterfacingTech(
    _AbstractRefactoringCandidatesTableTechPlaceholder,
    RefactoringCandidatesTableUnitInterfacing,
):
    """Table for refactoring candidates related to unit interfacing, filtered by technology. Headers are: Unit name, LOC, McCabe, Parameters, Component, Technology."""

    key = "REFACTORING_CANDIDATES_TABLE_UNIT_INTERFACING_TECH_{tech_idx}"


class RefactoringCandidatesTableModuleCouplingTech(
    _AbstractRefactoringCandidatesTableTechPlaceholder,
    RefactoringCandidatesTableModuleCoupling,
):
    """Table for refactoring candidates related to module coupling, filtered by technology. Headers are: File name, LOC, Fan-in, Component, Technology."""

    key = "REFACTORING_CANDIDATES_TABLE_MODULE_COUPLING_TECH_{tech_idx}"


class RefactoringCandidatesTableComponentIndependenceTech(
    _AbstractRefactoringCandidatesTableTechPlaceholder,
    RefactoringCandidatesTableComponentIndependence,
):
    """Table for refactoring candidates related to component independence, filtered by technology. Headers are: File name, LOC, Component, Technology."""

    key = "REFACTORING_CANDIDATES_TABLE_COMPONENT_INDEPENDENCE_TECH_{tech_idx}"

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

from abc import abstractmethod

from report_generator.generator.constants import MaintMetric
from report_generator.generator.data_models import refactoring_candidates_data
from report_generator.generator.formatters.formatters import technology_name
from report_generator.generator.placeholders.table.base import TableMatrix, TablePlaceholder


class _AbstractRefactoringCandidatesTablePlaceholder(TablePlaceholder):
    _key_pattern = "REFACTORING_CANDIDATES_TABLE_[metric]"
    metric: MaintMetric

    @classmethod
    @property
    def key(cls):
        return cls._key_pattern.replace('[metric]', str(cls.metric))

    @classmethod
    @abstractmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        pass

    @classmethod
    def value(cls, parameter=None) -> TableMatrix:
        return cls._to_table_matrix(refactoring_candidates_data.get_candidates(cls.metric))


class RefactoringCandidatesTableDuplication(_AbstractRefactoringCandidatesTablePlaceholder):
    metric = MaintMetric.DUPLICATION

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [['Description', 'Redundant LOC', 'Level', 'Technology']]

        for finding in data:
            locs: list = finding['locations']

            unique_filenames = {loc['file'].split('/')[-1] for loc in locs}

            rows.append([
                f"{finding['loc']} lines occurring {len(locs)} times in {', '.join(unique_filenames)}",
                finding['loc'] * (len(locs) - 1),
                "File" if finding['sameFile'] else "Component" if finding['sameComponent'] else "System",
                technology_name(finding['technology'])
            ])

        return rows


class RefactoringCandidatesTableUnitSize(_AbstractRefactoringCandidatesTablePlaceholder):
    metric = MaintMetric.UNIT_SIZE

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [['Unit name', 'LOC', 'McCabe', 'Parameters', 'Component', 'Technology']]

        for finding in data:
            rows.append([
                finding["name"],
                finding["loc"],
                finding.get("mcCabe", "-"),
                finding.get("parameters", "-"),
                finding["component"],
                technology_name(finding['technology'])
            ])

        return rows


class RefactoringCandidatesTableUnitComplexity(_AbstractRefactoringCandidatesTablePlaceholder):
    metric = MaintMetric.UNIT_COMPLEXITY

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [['Unit name', 'LOC', 'McCabe', 'Parameters', 'Component', 'Technology']]

        for finding in data:
            rows.append([
                finding["name"],
                finding.get("loc", "-"),
                finding["mcCabe"],
                finding.get("parameters", "-"),
                finding["component"],
                technology_name(finding['technology'])
            ])

        return rows


class RefactoringCandidatesTableUnitInterfacing(_AbstractRefactoringCandidatesTablePlaceholder):
    metric = MaintMetric.UNIT_INTERFACING

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [['Unit name', 'LOC', 'McCabe', 'Parameters', 'Component', 'Technology']]

        for finding in data:
            rows.append([
                finding["name"],
                finding.get("loc", "-"),
                finding.get("mcCabe", "-"),
                finding["parameters"],
                finding["component"],
                technology_name(finding['technology'])
            ])

        return rows

class RefactoringCandidatesTableModuleCoupling(_AbstractRefactoringCandidatesTablePlaceholder):
    metric = MaintMetric.MODULE_COUPLING

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [['File name', 'LOC', 'Fan-in', 'Component', 'Technology']]

        for finding in data:
            rows.append([
                finding["file"].split("/")[-1],
                finding.get("loc", "-"),
                finding["fanIn"],
                finding["component"],
                technology_name(finding['technology'])
            ])

        return rows


class RefactoringCandidatesComponentEntanglement(_AbstractRefactoringCandidatesTablePlaceholder):
    metric = MaintMetric.COMPONENT_ENTANGLEMENT

    @staticmethod
    def _generate_description(finding) ->str:
        entanglement_type = finding["type"]

        if entanglement_type == 'COMMUNICATION_DENSITY':
            severity = finding["severity"].replace("_", " ").capitalize()
            component_name = finding["component"]
            return f"{severity} communication density on {component_name}"

        # Check if type is valid (you'll need to implement this based on your validation logic)
        special_type_names = {
            "LAYER_BYPASSING_DEPENDENCY": "transitive dependency",
        }

        base_description = special_type_names.get(entanglement_type, entanglement_type.replace("_", " ").lower()).capitalize()
        source_component = finding["sourceComponent"]
        target_component = finding["targetComponent"]

        return f"{base_description} between {source_component} and {target_component}"

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [['Description', 'Weight']]

        for finding in data:
            rows.append([
                RefactoringCandidatesComponentEntanglement._generate_description(finding),
                finding['weight']
            ])

        return rows
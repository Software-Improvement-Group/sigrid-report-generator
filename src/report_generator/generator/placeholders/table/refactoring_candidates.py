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

from report_generator.generator import sigrid_api
from report_generator.generator.constants import MaintMetric
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
        return cls._to_table_matrix(
            sigrid_api.get_maintainability_refactoring_candidates(system_property=cls.metric).get(
                'refactoringCandidates', [])
        )


class RefactoringCandidatesTableDuplication(_AbstractRefactoringCandidatesTablePlaceholder):
    metric = MaintMetric.DUPLICATION

    @classmethod
    def _to_table_matrix(cls, data) -> TableMatrix:
        rows = [['Description', 'Redundant LOC', 'Same file', 'Same component', 'Technology']]

        for candidate in data:
            locs: list = candidate['locations']

            unique_filenames = {loc['file'].split('/')[-1] for loc in locs}

            rows.append([
                f"{candidate['loc']} lines occurring {len(locs)} times in {', '.join(unique_filenames)}",
                candidate['loc'] * (len(locs) - 1),
                "yes" if candidate['sameFile'] else "no",
                "yes" if candidate['sameComponent'] else "no",
                technology_name(candidate['technology'])
            ])

        return rows

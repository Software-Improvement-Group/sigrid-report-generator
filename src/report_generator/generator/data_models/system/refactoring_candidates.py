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
from functools import lru_cache

from report_generator.generator import sigrid_api
from report_generator.generator.constants import MaintMetric


class RefactoringCandidatesData:
    @staticmethod
    def _get_api_data(metric: MaintMetric):
        return sigrid_api.get_maintainability_refactoring_candidates(system_property=metric, count=20)

    @lru_cache()
    def get_candidates(self, metric: MaintMetric):
        return self._get_api_data(metric).get('refactoringCandidates', [])


refactoring_candidates_data = RefactoringCandidatesData()

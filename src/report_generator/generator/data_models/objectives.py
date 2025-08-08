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

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import cached_property

from report_generator.generator import sigrid_api
from report_generator.generator.report_utils.time_series import Period


class ObjectiveStatus(Enum):
    MET = "MET"
    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    WORSENED = "WORSENED"
    UNKNOWN = "UNKNOWN"


class ObjectivesData:
    @cached_property
    def periods(self):
        return Period.for_last_year_months()

    @cached_property
    def comparison_period(self):
        period = sigrid_api.get_period()
        return Period(period[0], period[1])

    @cached_property
    def objectives_evaluation_trend(self):
        return [(period, sigrid_api.get_objectives_evaluation(period)["systems"]) for period in self.periods]

    @cached_property
    def objectives_evaluation_status(self):
        period = self.comparison_period
        return sigrid_api.get_objectives_evaluation(period)["systems"]

    @cached_property
    def teams(self):
        result = defaultdict(list)
        for system_metadata in sigrid_api.get_portfolio_metadata():
            for team in system_metadata["teamNames"]:
                result[team].append(system_metadata["systemName"])
            if len(system_metadata["teamNames"]) == 0:
                result["Unknown"].append(system_metadata["systemName"])
        return dict(sorted(result.items(), key=lambda item: item[0], reverse=True))

    def get_portfolio_trend_series(self, capability):
        series = []
        for status in ObjectiveStatus:
            row = []
            for period, evaluation in self.objectives_evaluation_trend:
                row.append(self.get_portfolio_percentage(evaluation, capability, status))
            series.append(row)
        return series

    def get_portfolio_status_series(self):
        evaluation = self.objectives_evaluation_status
        return [[self.get_portfolio_percentage(evaluation, None, status)] for status in ObjectiveStatus]

    def get_team_status_series(self):
        series = []
        for status in ObjectiveStatus:
            row = []
            for team, system_names in self.teams.items():
                evaluation = self.filter_system_evaluations(self.objectives_evaluation_status, system_names)
                row.append(self.get_portfolio_percentage(evaluation, None, status))
            series.append(row)
        return series

    def get_portfolio_percentage(self, evaluations, capability, status):
        with_status = 0
        total = 0

        for system in evaluations:
            for objective_evaluation in system["objectives"]:
                if capability is None or objective_evaluation["feature"] == capability:
                    if self.determine_system_status(objective_evaluation) == status:
                        with_status += 1
                    total += 1

        return with_status * 100.0 / total if total > 0 else 0

    def determine_system_status(self, objective_evaluation):
        if objective_evaluation["targetMetAtEnd"] == "UNKNOWN":
            return ObjectiveStatus.UNKNOWN
        elif objective_evaluation["targetMetAtEnd"] == "MET":
            return ObjectiveStatus.MET
        elif objective_evaluation["delta"] == "IMPROVING":
            return ObjectiveStatus.IMPROVED
        elif objective_evaluation["delta"] == "DETERIORATING":
            return ObjectiveStatus.WORSENED
        elif objective_evaluation["delta"] == "SIMILAR":
            return ObjectiveStatus.UNCHANGED
        else:
            return ObjectiveStatus.UNKNOWN

    def filter_system_evaluations(self, evaluation, system_names):
        return [system for system in evaluation if system["systemName"] in system_names]


objectives_data = ObjectivesData()

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

from enum import Enum
from functools import cached_property

import numpy as np

from report_generator.generator.context import sigrid_api
from report_generator.generator.utils.time_series import Period


class ProgressStatus(Enum):
    MET_AT_START = "MET_AT_START"
    MET_AT_END = "MET_AT_END"
    UNKNOWN = "UNKNOWN"


class ProgressSigridData:
    def __init__(self):
        self.capabilities = ["SECURITY", "OPEN_SOURCE_HEALTH", "ARCHITECTURE_QUALITY", "MAINTAINABILITY"]

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

    def get_portfolio_trend_series(self, capability):
        row = [[], [], [], []]
        for period, evaluation in self.objectives_evaluation_trend:
            row = np.hstack((row, self.get_portfolio_percentage(evaluation, capability)))
        res = row[0] + row[1]
        return [res]

    def get_portfolio_status_series(self):
        evaluation = self.objectives_evaluation_status
        return self.get_portfolio_percentage(evaluation, None)

    def get_capability_status_series(self):
        evaluation = self.objectives_evaluation_status

        row = [[], [], [], []]
        for capability in self.capabilities:
            row = np.hstack((row, self.get_portfolio_percentage(evaluation, capability)))
        return row

    def get_portfolio_percentage(self, evaluations, capability):
        with_status_at_start = 0
        with_status_at_end = 0
        with_status_unknown = 0
        total = 0

        for system in evaluations:
            for objective_evaluation in system["objectives"]:
                if capability is None or objective_evaluation["feature"] == capability:
                    if self.determine_system_status(objective_evaluation, ProgressStatus.MET_AT_START) == True:
                        with_status_at_start += 1
                    if self.determine_system_status(objective_evaluation, ProgressStatus.MET_AT_END) == True:
                        with_status_at_end += 1
                    if self.determine_system_status(objective_evaluation, ProgressStatus.UNKNOWN) == True:
                        with_status_unknown += 1
                    total += 1

        with_status_at_start = with_status_at_start * 100.0 / (total - with_status_unknown) if (
                                                                                                           total - with_status_unknown) > 0 else 0
        with_status_at_end = with_status_at_end * 100.0 / (total - with_status_unknown) if (
                                                                                                       total - with_status_unknown) > 0 else 0

        if with_status_at_end >= with_status_at_start:
            improved = np.round(with_status_at_end - with_status_at_start, 0)
            return [[np.round(with_status_at_start, 0)], [improved], [0.0], [100.0 - with_status_at_start - improved]]
        else:
            worsened = np.round(with_status_at_start - with_status_at_end, 0)
            return [[np.round(with_status_at_end, 0)], [0.0], [worsened], [100.0 - with_status_at_end - worsened]]

    @staticmethod
    def determine_system_status(objective_evaluation, status):
        if status == ProgressStatus.MET_AT_START:
            return objective_evaluation["targetMetAtStart"] == "MET"
        if status == ProgressStatus.MET_AT_END:
            return objective_evaluation["targetMetAtEnd"] == "MET"
        if status == ProgressStatus.UNKNOWN:
            return (objective_evaluation["targetMetAtEnd"] == "UNKNOWN"
                    or (objective_evaluation["targetMetAtEnd"] != "MET"
                        and objective_evaluation["delta"] != "IMPROVING"
                        and objective_evaluation["delta"] != "DETERIORATING"
                        and objective_evaluation["delta"] != "SIMILAR"))


progress_sigrid_data = ProgressSigridData()

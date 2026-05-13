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
from typing import NamedTuple

import numpy as np

from report_generator.generator.context import sigrid_api
from report_generator.generator.utils.time_series import Period


class ProgressStatus(Enum):
    MET_AT_START = "MET_AT_START"
    MET_AT_END = "MET_AT_END"
    UNKNOWN = "UNKNOWN"


class _StatusCounts(NamedTuple):
    at_start: float
    at_end: float
    known_total: float


class ProgressSigridData:
    def __init__(self):
        self.capabilities = [
            "SECURITY",
            "OPEN_SOURCE_HEALTH",
            "ARCHITECTURE_QUALITY",
            "MAINTAINABILITY",
        ]

    @cached_property
    def periods(self):
        return Period.for_last_year_months()

    @cached_property
    def comparison_period(self):
        period = sigrid_api.get_period()
        return Period(period[0], period[1])

    @cached_property
    def objectives_evaluation_trend(self):
        return [
            (period, sigrid_api.get_objectives_evaluation(period)["systems"])
            for period in self.periods
        ]

    @cached_property
    def objectives_evaluation_status(self):
        period = self.comparison_period
        return sigrid_api.get_objectives_evaluation(period)["systems"]

    def get_portfolio_trend_series(self, capability):
        row = [[], [], [], []]
        for _period, evaluation in self.objectives_evaluation_trend:
            row = np.hstack(
                (row, self.get_portfolio_percentage(evaluation, capability))
            )
        res = row[0] + row[1]
        return [res]

    def get_portfolio_status_series(self):
        evaluation = self.objectives_evaluation_status
        return self.get_portfolio_percentage(evaluation, None)

    def get_capability_status_series(self):
        evaluation = self.objectives_evaluation_status

        row = [[], [], [], []]
        for capability in self.capabilities:
            row = np.hstack(
                (row, self.get_portfolio_percentage(evaluation, capability))
            )
        return row

    def _count_statuses(self, evaluations, capability) -> _StatusCounts:
        at_start = at_end = unknown = total = 0
        for system in evaluations:
            for obj in system["objectives"]:
                if capability is None or obj["feature"] == capability:
                    if self.determine_system_status(obj, ProgressStatus.MET_AT_START):
                        at_start += 1
                    if self.determine_system_status(obj, ProgressStatus.MET_AT_END):
                        at_end += 1
                    if self.determine_system_status(obj, ProgressStatus.UNKNOWN):
                        unknown += 1
                    total += 1
        known = total - unknown
        return _StatusCounts(
            at_start=at_start * 100.0 / known if known > 0 else 0,
            at_end=at_end * 100.0 / known if known > 0 else 0,
            known_total=known,
        )

    @staticmethod
    def _build_stacked_result(counts: _StatusCounts) -> list:
        start, end = counts.at_start, counts.at_end
        if end >= start:
            improved = np.round(end - start, 0)
            return [[np.round(start, 0)], [improved], [0.0], [100.0 - start - improved]]
        else:
            worsened = np.round(start - end, 0)
            return [[np.round(end, 0)], [0.0], [worsened], [100.0 - end - worsened]]

    def get_portfolio_percentage(self, evaluations, capability):
        return self._build_stacked_result(self._count_statuses(evaluations, capability))

    @staticmethod
    def determine_system_status(objective_evaluation, status):
        if status == ProgressStatus.MET_AT_START:
            return objective_evaluation["targetMetAtStart"] == "MET"
        if status == ProgressStatus.MET_AT_END:
            return objective_evaluation["targetMetAtEnd"] == "MET"
        if status == ProgressStatus.UNKNOWN:
            return objective_evaluation["targetMetAtEnd"] == "UNKNOWN" or (
                objective_evaluation["targetMetAtEnd"] != "MET"
                and objective_evaluation["delta"] != "IMPROVING"
                and objective_evaluation["delta"] != "DETERIORATING"
                and objective_evaluation["delta"] != "SIMILAR"
            )


progress_sigrid_data = ProgressSigridData()

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

from functools import cached_property
from report_generator.generator.context import sigrid_api
from datetime import datetime

import pandas as pd
import numpy as np


class SigridHygienePortfolioData:
    def __init__(self):
        self.metadata_fields = ["softwareDistributionStrategy", "applicationType", "deploymentType", "targetIndustry",
                                "lifecyclePhase", "businessCriticality", "inProductionSince", "supplierNames", "teamNames", "divisionName"]
        #self.metadata = sigrid_api.get_portfolio_metadata()

    @cached_property
    def get_metadata(self):
        return sigrid_api.get_portfolio_metadata()

    @cached_property
    def get_metadata_fields(self):
        return ["Distribution strategy", "Application type", "Deployment type", "Target industry", "Lifecycle phase",
                "Business criticality", "In production since", "Supplier", "Team", "Division"]


    def _compute_metadata_dataframe(self):
        df = pd.DataFrame(columns=self.metadata_fields)
        metadata = {system["systemName"]: system for system in self.get_metadata()}
        active_systems = [name for name, meta in metadata.items() if meta["active"] and not meta["isDevelopmentOnly"]]

        for system in active_systems:
            row = {}

            for field in self.metadata_fields:
                value_metadata = metadata[system][field]
                row[field] = 0 if not value_metadata else 1

            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        return df


    def get_portfolio_metadata_completeness(self):
        metadata_df = self._compute_metadata_dataframe()
        column_completeness = metadata_df.sum().to_dict()
        total_systems = len(metadata_df)
        row = [[], []]

        for field in self.metadata_fields:
            complete = np.round(column_completeness[field] / total_systems * 100, 0).astype(int)
            row = np.hstack((row, [[complete], [100-complete]]))

        return row


    def get_number_systems_complete_metadata(self):
        metadata_df = self._compute_metadata_dataframe()
        fully_complete_count = (metadata_df.sum(axis=1) == len(self.metadata_fields)).sum()
        return fully_complete_count


    def get_snapshot_freshness(self):
        metadata = {system["systemName"]: system for system in self.get_metadata()}
        active_systems = [name for name, meta in metadata.items() if meta["active"] and not meta["isDevelopmentOnly"]]
        time_now = datetime.now()
        days_7 = 0
        days_30 = 0
        days_90 = 0
        days_180 = 0
        days_more = 0

        for system in active_systems:
            snapshot_date = sigrid_api.get_architecture_findings(system)["snapshotDate"]
            freshness = (time_now - datetime.fromisoformat(snapshot_date)).days

            if freshness < 7: days_7 += 1
            elif freshness < 30: days_30 += 1
            elif freshness < 90: days_90 += 1
            elif freshness < 180: days_180 += 1
            else: days_more += 1

        return [[len(active_systems), days_7, days_30, days_90, days_180, days_more]]


    def get_eol_deactivated_systems(self):
        metadata = {system["systemName"]: system for system in self.get_metadata()}
        deactivated_systems = [name for name, meta in metadata.items() if not meta["active"] or meta["isDevelopmentOnly"]]
        eol_systems = [name for name, meta in metadata.items() if meta["lifecyclePhase"] == "EOL"]
        deactivated_eol = set(deactivated_systems) & set(eol_systems)

        return [[len(metadata), len(deactivated_systems), len(eol_systems), len(deactivated_eol)]]


    def get_last_access_time_users(self):
        users = sigrid_api.get_users()["users"]
        roles = ["ADMIN", "MAINTAINER", "USER"]
        time_now = datetime.now()

        # 5 time buckets (7, 30, 90, 365, >365 days) × 3 roles
        buckets = np.zeros((5, 3), dtype=int)

        for i, role in enumerate(roles):
            freshness_list = [(time_now - datetime.fromisoformat(user["lastLoginAt"])).days
                              for user in users
                              if user["lastLoginAt"] is not None and user["role"] == role]

            for days in freshness_list:
                if days < 7: buckets[0, i] += 1
                elif days < 30: buckets[1, i] += 1
                elif days < 90: buckets[2, i] += 1
                elif days < 365: buckets[3, i] += 1
                else: buckets[4, i] += 1

        totals = buckets.sum(axis=0)
        # result: 3 rows (roles) × 6 columns (total + 5 time buckets)
        result = np.column_stack((totals, buckets.T))

        return result.tolist()


sigrid_hygiene_portfolio_data = SigridHygienePortfolioData()


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

from datetime import datetime, timedelta
from functools import cached_property

from dateutil import parser

from report_generator.generator.context import sigrid_api
from report_generator.generator.utils.time_series import Period


class SigridHygienePortfolioData:
    def __init__(self):
        self.metadata_fields = [
            "softwareDistributionStrategy",
            "applicationType",
            "deploymentType",
            "targetIndustry",
            "lifecyclePhase",
            "businessCriticality",
            "inProductionSince",
            "supplierNames",
            "teamNames",
            "divisionName",
        ]

    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()

    def _compute_list_metadata_dict(self):
        list_system_dict = []
        metadata = {system["systemName"]: system for system in self.metadata}

        for system in metadata.keys():
            system_dict = {}

            for field in self.metadata_fields:
                value_metadata = metadata[system][field]
                system_dict[field] = 0 if not value_metadata else 1

            list_system_dict.append(system_dict)

        return list_system_dict

    @cached_property
    def metadata_completeness(self):
        list_system_dict = self._compute_list_metadata_dict()
        total_systems = len(list_system_dict)

        # If there are no systems, then all metadata values completeness is 0%
        if total_systems == 0:
            return {field: (0, 100) for field in self.metadata_fields}

        field_completeness = {
            field: sum(system[field] == 1 for system in list_system_dict)
            for field in self.metadata_fields
        }

        result = {}
        for field in self.metadata_fields:
            complete = int(round(field_completeness[field] / total_systems * 100, 0))
            result[field] = (complete, 100 - complete)

        return result

    @cached_property
    def snapshot_freshness(self):
        active_systems = [system["systemName"] for system in self.metadata]
        dict_freshness_days = {}
        time_now = datetime.now()
        portfolio_architecture = sigrid_api.get_portfolio_architecture_findings()

        for system_architecture in portfolio_architecture:
            if system_architecture["system"] in active_systems:
                if "snapshotDate" in system_architecture:
                    freshness = (
                        time_now - parser.isoparse(system_architecture["snapshotDate"])
                    ).days
                    dict_freshness_days[system_architecture["system"]] = freshness

        return dict_freshness_days

    @cached_property
    def eol_deactivated_systems(self):
        metadata = {
            system["systemName"]: system
            for system in sigrid_api.get_portfolio_metadata(hide_deactivated=False)
        }
        deactivated_systems = [
            name
            for name, meta in metadata.items()
            if not meta["active"] or meta["isDevelopmentOnly"]
        ]
        eol_systems = [
            name for name, meta in metadata.items() if meta["lifecyclePhase"] == "EOL"
        ]
        deactivated_eol = set(deactivated_systems) & set(eol_systems)

        return [
            [
                len(metadata),
                len(deactivated_systems),
                len(eol_systems),
                len(deactivated_eol),
            ]
        ]

    @staticmethod
    def get_last_access_time_users(role="USER"):
        users = sigrid_api.get_users()["users"]
        time_now = datetime.now()

        list_freshness_days = [
            (time_now - parser.isoparse(user["lastLoginAt"])).days
            for user in users
            if user["lastLoginAt"] is not None and user["role"] == role
        ]

        return list_freshness_days

    def get_objectives_coverage(self):
        metadata = {system["systemName"]: system for system in self.get_metadata}
        active_systems = [
            name
            for name, meta in metadata.items()
            if meta["active"] and not meta["isDevelopmentOnly"]
        ]

        time_now = datetime.now()
        period = Period(time_now - timedelta(days=1), time_now)
        objectives = sigrid_api.get_objectives_evaluation(period)["systems"]
        list_system_dict = []

        for system in objectives:
            system_dict = {
                "MAINTAINABILITY": 0,
                "ARCHITECTURE_QUALITY": 0,
                "OPEN_SOURCE_HEALTH": 0,
                "SECURITY": 0,
            }
            if system["systemName"] in active_systems:
                for objective in system["objectives"]:
                    if (
                        objective["feature"] in system_dict
                        and system_dict[objective["feature"]] == 0
                    ):
                        system_dict[objective["feature"]] = 1

            list_system_dict.append(system_dict)


sigrid_hygiene_portfolio_data = SigridHygienePortfolioData()

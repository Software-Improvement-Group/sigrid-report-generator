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
from unittest.mock import patch

from freezegun import freeze_time

from report_generator.generator.domain.portfolio.sigrid_hygiene_portfolio import (
    sigrid_hygiene_portfolio_data,
)


class TestSigridHygienePortfolioData:
    """Test cases for SigridHygienePortfolioData model."""

    def teardown_method(self):
        """Clean up cached properties after each test case."""
        cache_attrs = [
            "metadata",
            "metadata_completeness",
            "snapshot_freshness",
            "eol_deactivated_systems",
        ]

        for attr in cache_attrs:
            sigrid_hygiene_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.sigrid_hygiene_portfolio.sigrid_api"
    )
    def test_portfolio_metadata_completeness(self, mock_api):
        """Test that the metadata completeness percentages are computed correctly."""
        mock_api.get_portfolio_metadata.return_value = [
            {
                "systemName": "A",
                "active": True,
                "isDevelopmentOnly": False,
                "softwareDistributionStrategy": "x",
                "applicationType": None,
                "deploymentType": "y",
                "targetIndustry": None,
                "lifecyclePhase": "prod",
                "businessCriticality": None,
                "inProductionSince": "2020-01-01",
                "supplierNames": None,
                "teamNames": None,
                "divisionName": "div",
            }
        ]

        data = sigrid_hygiene_portfolio_data.metadata_completeness

        # We expect one entry per metadata field, each with (complete%, missing%)
        assert len(data) == len(sigrid_hygiene_portfolio_data.metadata_fields)
        assert all(v[0] in (0, 100) and v[1] in (0, 100) for v in data.values())

    @freeze_time("2026-03-15 00:00:00")
    @patch(
        "report_generator.generator.domain.portfolio.sigrid_hygiene_portfolio.sigrid_api"
    )
    def test_snapshot_freshness(self, mock_api):
        """Test that snapshot freshness dates are classified correctly in the time buckets."""
        mock_api.get_portfolio_metadata.return_value = [
            {"systemName": "sys1", "active": True, "isDevelopmentOnly": False}
        ]

        mock_api.get_portfolio_architecture_findings.return_value = [
            {
                "analysisDate": (
                    datetime.now() - timedelta(days=5)
                ).isoformat(),  # 5 days old
                "customer": "test_customer",
                "modelVersion": "2025",
                "ratings": {},
                "snapshotDate": (
                    datetime.now() - timedelta(days=5)
                ).isoformat(),  # 5 days old
                "system": "sys1",
            },
            {
                "analysisDate": (
                    datetime.now() - timedelta(days=10)
                ).isoformat(),  # 10 days old
                "customer": "test_customer",
                "modelVersion": "2025",
                "ratings": {},
                "snapshotDate": (
                    datetime.now() - timedelta(days=10)
                ).isoformat(),  # 10 days old
                "system": "inactive_system",
            },
        ]

        result = sigrid_hygiene_portfolio_data.snapshot_freshness

        # Format: {"sys1": 5}
        assert len(result) == 1  # total systems
        assert "sys1" in result.keys()  # systems contained
        assert "inactive_system" not in result.keys()  # systems not contained
        assert 5 in result.values()  # values contained (5 from active system)
        assert (
            10 not in result.values()
        )  # values not contained (10 from inactive system)

    @patch(
        "report_generator.generator.domain.portfolio.sigrid_hygiene_portfolio.sigrid_api"
    )
    def test_eol_deactivated_systems(self, mock_api):
        """Test that EOL and deactivated systems are correctly counted."""
        mock_api.get_portfolio_metadata.return_value = [
            {
                "systemName": "A",
                "active": False,
                "isDevelopmentOnly": False,
                "lifecyclePhase": "EOL",
            },
            {
                "systemName": "B",
                "active": True,
                "isDevelopmentOnly": False,
                "lifecyclePhase": "LIVE",
            },
            {
                "systemName": "C",
                "active": False,
                "isDevelopmentOnly": True,
                "lifecyclePhase": "LIVE",
            },
        ]

        result = sigrid_hygiene_portfolio_data.eol_deactivated_systems

        # Total systems: 3
        assert result[0][0] == 3
        # Deactivated = A + C = 2
        assert result[0][1] == 2
        # EOL = A
        assert result[0][2] == 1
        # EOL & deactivated = A
        assert result[0][3] == 1

    @freeze_time("2026-03-15 00:00:00")
    @patch(
        "report_generator.generator.domain.portfolio.sigrid_hygiene_portfolio.sigrid_api"
    )
    def test_last_access_time_users(self, mock_api):
        """Test that user access times are classified correctly in the time buckets."""
        mock_api.get_users.return_value = {
            "users": [
                {
                    "role": "ADMIN",
                    "lastLoginAt": (datetime.now() - timedelta(days=5)).isoformat(),
                },  # <7 days
                {
                    "role": "MAINTAINER",
                    "lastLoginAt": (datetime.now() - timedelta(days=40)).isoformat(),
                },  # ~40 days
                {
                    "role": "USER",
                    "lastLoginAt": (datetime.now() - timedelta(days=420)).isoformat(),
                },  # >365 days
            ]
        }

        # Result admin: [5]
        result_admin = sigrid_hygiene_portfolio_data.get_last_access_time_users(
            role="ADMIN"
        )
        assert len(result_admin) == 1
        assert 5 in result_admin

        # Result maintainer: [40]
        result_maintainer = sigrid_hygiene_portfolio_data.get_last_access_time_users(
            role="MAINTAINER"
        )
        assert len(result_maintainer) == 1
        assert 40 in result_maintainer

        # Result user: [420]
        result_user = sigrid_hygiene_portfolio_data.get_last_access_time_users(
            role="USER"
        )
        assert len(result_user) == 1
        assert 420 in result_user

        # Result default value (role = user): [420]
        result_default = sigrid_hygiene_portfolio_data.get_last_access_time_users()
        assert result_default == result_user

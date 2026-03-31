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
            "get_metadata",
            "get_metadata_fields_labels",
            "get_snapshot_freshness_labels",
            "get_eol_deactivated_systems_labels",
            "get_last_access_time_labels",
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

        row = sigrid_hygiene_portfolio_data.get_portfolio_metadata_completeness()

        # We expect: for each metadata field -> (1 or 0) completeness vs missing
        assert len(row) == 2  # two rows: complete %, missing %
        assert len(row[0]) == len(sigrid_hygiene_portfolio_data.metadata_fields)
        assert all(v in (0, 100) for v in row[0])

    @freeze_time("2026-03-15 00:00:00")
    @patch(
        "report_generator.generator.domain.portfolio.sigrid_hygiene_portfolio.sigrid_api"
    )
    def test_snapshot_freshness(self, mock_api):
        """Test that snapshot freshness dates are classified correctly in the time buckets."""
        mock_api.get_portfolio_metadata.return_value = [
            {"systemName": "sys1", "active": True, "isDevelopmentOnly": False}
        ]

        mock_api.get_architecture_findings.return_value = {
            "snapshotDate": (
                datetime.now() - timedelta(days=5)
            ).isoformat(),  # 5 days old
        }

        result = sigrid_hygiene_portfolio_data.get_snapshot_freshness()

        # Format: [[total, <1wk, 1mo, 3mo, 6mo, >6mo]]
        assert result[0][0] == 1  # total systems
        assert result[0][1] == 1  # in "< 7 days" bucket

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

        result = sigrid_hygiene_portfolio_data.get_eol_deactivated_systems()

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
                    "lastLoginAt": (
                        datetime.now() - timedelta(days=5)
                    ).isoformat(),
                },  # <7 days
                {
                    "role": "MAINTAINER",
                    "lastLoginAt": (
                        datetime.now() - timedelta(days=40)
                    ).isoformat(),
                },  # ~40 days
                {
                    "role": "USER",
                    "lastLoginAt": (
                        datetime.now() - timedelta(days=420)
                    ).isoformat(),
                },  # >365 days
            ]
        }

        result = sigrid_hygiene_portfolio_data.get_last_access_time_users()

        # Result shape: 3 rows (roles), 6 columns (total + 5 buckets)
        assert len(result) == 3
        assert len(result[0]) == 6

        # Admin: should be in <7 days bucket
        assert result[0][1] == 1  # bucket 1 for ADMIN (<7 days)

        # Maintainer: should be in 30 < days < 90 category
        assert result[1][3] == 1  # bucket for 30-90 days

        # User: > 1 year
        assert result[2][5] == 1  # last bucket > 365 days

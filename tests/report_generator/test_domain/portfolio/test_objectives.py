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

from unittest.mock import patch

from report_generator.generator.context.portfolio_filters import reset_context
from report_generator.generator.domain.portfolio.objectives import (
    ObjectivesData,
    ObjectiveStatus,
    objectives_data,
)


class TestObjectivesData:
    """Test cases for ObjectivesData model."""

    def setup_method(self):
        """Store the original capabilities so tests do not leak state."""
        self._original_capabilities = objectives_data.capabilities

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = [
            "periods",
            "comparison_period",
            "objectives_evaluation_trend",
            "objectives_evaluation_status",
            "teams",
            "objectives_coverage",
        ]
        for attr in cache_attrs:
            objectives_data.__dict__.pop(attr, None)

        objectives_data.capabilities = self._original_capabilities

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_determine_system_status_met(self, mock_sigrid_api):
        """Test that determine_system_status returns MET when target is met."""
        objective = {"targetMetAtEnd": "MET", "delta": "SIMILAR"}

        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.MET

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_determine_system_status_improved(self, mock_sigrid_api):
        """Test that determine_system_status returns IMPROVED when improving."""
        objective = {"targetMetAtEnd": "NOT_MET", "delta": "IMPROVING"}

        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.IMPROVED

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_determine_system_status_worsened(self, mock_sigrid_api):
        """Test that determine_system_status returns WORSENED when deteriorating."""
        objective = {"targetMetAtEnd": "NOT_MET", "delta": "DETERIORATING"}

        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.WORSENED

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_determine_system_status_unchanged(self, mock_sigrid_api):
        """Test that determine_system_status returns UNCHANGED when similar."""
        objective = {"targetMetAtEnd": "NOT_MET", "delta": "SIMILAR"}

        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.UNCHANGED

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_determine_system_status_unknown(self, mock_sigrid_api):
        """Test that determine_system_status returns UNKNOWN for unknown states."""
        objective = {"targetMetAtEnd": "UNKNOWN", "delta": "SIMILAR"}

        status = ObjectivesData.determine_system_status(objective)
        assert status == ObjectiveStatus.UNKNOWN

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_filter_system_evaluations(self, mock_sigrid_api):
        """Test that filter_system_evaluations filters systems correctly."""
        evaluation = [
            {"systemName": "system1", "objectives": []},
            {"systemName": "system2", "objectives": []},
            {"systemName": "system3", "objectives": []},
        ]

        filtered = ObjectivesData.filter_system_evaluations(
            evaluation, ["system1", "system3"]
        )

        assert len(filtered) == 2
        assert filtered[0]["systemName"] == "system1"
        assert filtered[1]["systemName"] == "system3"

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_get_portfolio_percentage_with_no_objectives(self, mock_sigrid_api):
        """Test that get_portfolio_percentage returns 0 when no objectives exist."""
        evaluations = [{"systemName": "system1", "objectives": []}]

        percentage = objectives_data.get_portfolio_percentage(
            evaluations, None, ObjectiveStatus.MET
        )

        assert percentage == 0

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_get_portfolio_percentage_calculates_correctly(self, mock_sigrid_api):
        """Test that get_portfolio_percentage calculates percentage correctly."""
        evaluations = [
            {
                "systemName": "system1",
                "objectives": [
                    {
                        "feature": "MAINTAINABILITY",
                        "targetMetAtEnd": "MET",
                        "delta": "SIMILAR",
                    },
                    {
                        "feature": "SECURITY",
                        "targetMetAtEnd": "NOT_MET",
                        "delta": "IMPROVING",
                    },
                    {
                        "feature": "ARCHITECTURE_QUALITY",
                        "targetMetAtEnd": "NOT_MET",
                        "delta": "DETERIORATING",
                    },
                ],
            }
        ]

        # 1 out of 3 is MET = 33.33%
        met_percentage = objectives_data.get_portfolio_percentage(
            evaluations, None, ObjectiveStatus.MET
        )
        assert abs(met_percentage - 33.333333) < 0.01

        # 1 out of 3 is IMPROVED = 33.33%
        improved_percentage = objectives_data.get_portfolio_percentage(
            evaluations, None, ObjectiveStatus.IMPROVED
        )
        assert abs(improved_percentage - 33.333333) < 0.01

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_objectives_coverage_no_systems(self, mock_sigrid_api):
        """Return correct result when portfolio is empty."""
        objectives_data.capabilities = [
            "MAINTAINABILITY",
            "ARCHITECTURE_QUALITY",
            "OPEN_SOURCE_HEALTH",
            "SECURITY",
        ]

        mock_sigrid_api.get_period.return_value = ("2026-03-13", "2026-04-13")
        mock_sigrid_api.get_objectives_evaluation.return_value = {"systems": []}

        result = objectives_data.objectives_coverage

        # All values should be set to 0
        assert result["TOTAL"] == 0
        assert result["ALL_CAPABILITIES"] == 0
        for capability in objectives_data.capabilities:
            assert result[capability] == 0

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_objectives_coverage_all_capabilities(self, mock_sigrid_api):
        """All systems have objectives set for all capabilities."""
        objectives_data.capabilities = [
            "MAINTAINABILITY",
            "OPEN_SOURCE_HEALTH",
        ]

        mock_sigrid_api.get_period.return_value = ("2026-03-13", "2026-04-13")
        mock_sigrid_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "objectives": [
                        {"feature": "MAINTAINABILITY"},
                        {"feature": "OPEN_SOURCE_HEALTH"},
                    ],
                    "systemName": "sys1",
                },
                {
                    "objectives": [
                        {"feature": "MAINTAINABILITY"},
                        {"feature": "OPEN_SOURCE_HEALTH"},
                    ],
                    "systemName": "sys2",
                },
            ]
        }

        result = objectives_data.objectives_coverage

        # Every capability appears twice
        assert result["TOTAL"] == 2
        assert result["ALL_CAPABILITIES"] == 2
        for capability in objectives_data.capabilities:
            assert result[capability] == 2

    @patch("report_generator.generator.domain.portfolio.objectives.sigrid_api")
    def test_objectives_coverage_mixed_capabilities(self, mock_sigrid_api):
        """Mixed systems with partial objectives coverage."""
        objectives_data.capabilities = [
            "MAINTAINABILITY",
            "OPEN_SOURCE_HEALTH",
        ]

        mock_sigrid_api.get_period.return_value = ("2026-03-13", "2026-04-13")
        mock_sigrid_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "objectives": [
                        {"feature": "MAINTAINABILITY"},
                    ],
                    "systemName": "sys1",
                },
                {
                    "objectives": [
                        {"feature": "OPEN_SOURCE_HEALTH"},
                    ],
                    "systemName": "sys2",
                },
            ]
        }

        result = objectives_data.objectives_coverage

        assert result["TOTAL"] == 2
        assert result["ALL_CAPABILITIES"] == 0
        for capability in objectives_data.capabilities:
            assert result[capability] == 1

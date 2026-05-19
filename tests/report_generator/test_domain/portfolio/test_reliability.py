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
from report_generator.generator.domain.portfolio.reliability_portfolio import (
    ReliabilityRatingsPortfolioData,
    reliability_ratings_portfolio_data,
)


class TestReliabilityPortfolioData:
    """Test cases for ReliabilityRatingsPortfolioData model."""

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = [
            "data",
            "metadata",
            "period",
            "system_names",
            "reliability_findings",
        ]
        for attr in cache_attrs:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
        ]
        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data

        reliability_ratings_portfolio_data.__dict__.pop("data", None)

        system = reliability_ratings_portfolio_data.get_system("system1")

        assert system is not None
        assert system["systemName"] == "system1"
        assert abs(system["rating"] - 4.5) < 0.01

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
            {"systemName": "system3", "rating": 4.2},
        ]
        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data

        for attr in ["data", "system_names"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        names = reliability_ratings_portfolio_data.system_names

        assert len(names) == 3
        assert "system1" in names
        assert "system2" in names
        assert "system3" in names

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_reliability_findings_aggregates_per_system(self, mock_sigrid_api):
        """Test that reliability_findings returns findings per system."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
        ]
        findings_system1 = [
            {"id": "a1", "severity": "HIGH"},
            {"id": "a2", "severity": "LOW"},
        ]
        findings_system2 = [{"id": "b1", "severity": "CRITICAL"}]

        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data
        mock_sigrid_api.get_reliability_findings.side_effect = [
            findings_system1,
            findings_system2,
        ]

        for attr in ["data", "system_names", "reliability_findings"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        result = reliability_ratings_portfolio_data.reliability_findings

        assert len(result) == 2
        assert result[0] == {"systemName": "system1", "findings": findings_system1}
        assert result[1] == {"systemName": "system2", "findings": findings_system2}

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_reliability_findings_handles_api_error_gracefully(self, mock_sigrid_api):
        """Test that a failing API call for one system returns empty findings and logs a warning."""
        mock_data = [
            {"systemName": "system1", "rating": 4.5},
            {"systemName": "system2", "rating": 3.8},
        ]
        findings_system1 = [{"id": "a1", "severity": "HIGH"}]

        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data
        mock_sigrid_api.get_reliability_findings.side_effect = [
            findings_system1,
            Exception("API error"),
        ]

        for attr in ["data", "system_names", "reliability_findings"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        result = reliability_ratings_portfolio_data.reliability_findings

        assert len(result) == 2
        assert result[0] == {"systemName": "system1", "findings": findings_system1}
        assert result[1] == {"systemName": "system2", "findings": []}

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_reliability_findings_empty_portfolio(self, mock_sigrid_api):
        """Test that reliability_findings returns an empty list when there are no systems."""
        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = []

        for attr in ["data", "system_names", "reliability_findings"]:
            reliability_ratings_portfolio_data.__dict__.pop(attr, None)

        result = reliability_ratings_portfolio_data.reliability_findings

        assert result == []

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_reliability_findings_uses_fresh_instance(self, mock_sigrid_api):
        """Test that a fresh instance fetches its own findings independently."""
        mock_data = [
            {"systemName": "system1", "rating": 3.5},
        ]
        findings = [{"id": "c1", "severity": "MEDIUM"}]

        mock_sigrid_api.get_portfolio_reliability_ratings.return_value = mock_data
        mock_sigrid_api.get_reliability_findings.return_value = findings

        portfolio = ReliabilityRatingsPortfolioData()

        result = portfolio.reliability_findings

        assert result == [{"systemName": "system1", "findings": findings}]
        mock_sigrid_api.get_reliability_findings.assert_called_once_with("system1")


class TestFindingsAboveObjectiveReliability:
    """Tests for ReliabilityRatingsPortfolioData.findings_above_objective."""

    def _make_instance(self, ratings_data):
        instance = ReliabilityRatingsPortfolioData()
        instance.__dict__["data"] = ratings_data
        instance.__dict__["system_names"] = [s["systemName"] for s in ratings_data]
        return instance

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_objective_met_returns_zero(self, mock_api):
        instance = self._make_instance([{"systemName": "sys1", "rating": 4.0}])
        instance.__dict__["reliability_findings"] = [
            {"systemName": "sys1", "findings": [{"severity": "CRITICAL"}]}
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "systemName": "sys1",
                    "objectives": [
                        {
                            "type": "RELIABILITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "MET",
                        }
                    ],
                }
            ]
        }

        result = instance.findings_above_objective
        assert result == [{"systemName": "sys1", "findings_above_objective": 0}]

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_no_objective_uses_fallback(self, mock_api):
        instance = self._make_instance([{"systemName": "sys1", "rating": 3.0}])
        instance.__dict__["reliability_findings"] = [
            {
                "systemName": "sys1",
                "findings": [
                    {"severity": "LOW"},
                    {"severity": "HIGH"},
                    {"severity": "CRITICAL"},
                ],
            }
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {"systems": []}

        result = instance.findings_above_objective
        assert result == [{"systemName": "sys1", "findings_above_objective": 2}]

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_objective_not_met_counts_above_target(self, mock_api):
        instance = self._make_instance([{"systemName": "sys1", "rating": 2.5}])
        instance.__dict__["reliability_findings"] = [
            {
                "systemName": "sys1",
                "findings": [
                    {"severity": "LOW"},
                    {"severity": "HIGH"},
                    {"severity": "CRITICAL"},
                ],
            }
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "systemName": "sys1",
                    "objectives": [
                        {
                            "type": "RELIABILITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "NOT_MET",
                        }
                    ],
                }
            ]
        }

        result = instance.findings_above_objective
        assert result == [{"systemName": "sys1", "findings_above_objective": 1}]

    @patch(
        "report_generator.generator.domain.portfolio.reliability_portfolio.sigrid_api"
    )
    def test_multiple_systems_mixed_objectives(self, mock_api):
        instance = self._make_instance(
            [
                {"systemName": "sys1", "rating": 4.0},
                {"systemName": "sys2", "rating": 3.0},
                {"systemName": "sys3", "rating": 2.0},
            ]
        )
        instance.__dict__["reliability_findings"] = [
            {"systemName": "sys1", "findings": [{"severity": "CRITICAL"}]},
            {
                "systemName": "sys2",
                "findings": [{"severity": "HIGH"}, {"severity": "CRITICAL"}],
            },
            {
                "systemName": "sys3",
                "findings": [{"severity": "LOW"}, {"severity": "HIGH"}],
            },
        ]
        mock_api.get_period.return_value = ("2024-01-01", "2024-12-31")
        mock_api.get_objectives_evaluation.return_value = {
            "systems": [
                {
                    "systemName": "sys1",
                    "objectives": [
                        {
                            "type": "RELIABILITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "MET",
                        }
                    ],
                },
                {
                    "systemName": "sys2",
                    "objectives": [
                        {
                            "type": "RELIABILITY_MAX_SEVERITY",
                            "target": "HIGH",
                            "targetMetAtEnd": "NOT_MET",
                        }
                    ],
                },
                {
                    "systemName": "sys3",
                    "objectives": [],
                },
            ]
        }

        result = instance.findings_above_objective
        assert result == [
            {"systemName": "sys1", "findings_above_objective": 0},
            {"systemName": "sys2", "findings_above_objective": 1},
            {"systemName": "sys3", "findings_above_objective": 1},
        ]


class TestFunctionalSuitabilityFindings:
    """Tests for ReliabilityRatingsPortfolioData.functional_suitability_findings."""

    def _make_instance(self, system_names, reliability_findings):
        instance = ReliabilityRatingsPortfolioData()
        instance.__dict__["system_names"] = system_names
        instance.__dict__["reliability_findings"] = reliability_findings
        return instance

    def test_filters_to_npr5333_cwes_only(self):
        instance = self._make_instance(
            ["sys1"],
            [
                {
                    "systemName": "sys1",
                    "findings": [
                        {"cweId": "CWE-476", "severity": "HIGH"},
                        {"cweId": "CWE-252", "severity": "MEDIUM"},
                        {"cweId": "CWE-835", "severity": "CRITICAL"},
                    ],
                }
            ],
        )

        result = instance.functional_suitability_findings

        assert len(result) == 1
        assert result[0]["systemName"] == "sys1"
        assert len(result[0]["findings"]) == 2
        assert all(f["cweId"] in {"CWE-476", "CWE-835"} for f in result[0]["findings"])

    def test_empty_findings_when_no_matching_cwes(self):
        instance = self._make_instance(
            ["sys1"],
            [
                {
                    "systemName": "sys1",
                    "findings": [
                        {"cweId": "CWE-252", "severity": "MEDIUM"},
                        {"cweId": "CWE-547", "severity": "LOW"},
                    ],
                }
            ],
        )

        result = instance.functional_suitability_findings

        assert result == [{"systemName": "sys1", "findings": []}]

    def test_finding_without_cwe_id_is_excluded(self):
        instance = self._make_instance(
            ["sys1"],
            [
                {
                    "systemName": "sys1",
                    "findings": [
                        {"severity": "HIGH"},
                        {"cweId": None, "severity": "MEDIUM"},
                        {"cweId": "CWE-682", "severity": "CRITICAL"},
                    ],
                }
            ],
        )

        result = instance.functional_suitability_findings

        assert len(result[0]["findings"]) == 1
        assert result[0]["findings"][0]["cweId"] == "CWE-682"

    def test_multiple_systems_filtered_independently(self):
        instance = self._make_instance(
            ["sys1", "sys2"],
            [
                {
                    "systemName": "sys1",
                    "findings": [
                        {"cweId": "CWE-476"},
                        {"cweId": "CWE-999"},
                    ],
                },
                {
                    "systemName": "sys2",
                    "findings": [
                        {"cweId": "CWE-999"},
                    ],
                },
            ],
        )

        result = instance.functional_suitability_findings

        assert result[0] == {"systemName": "sys1", "findings": [{"cweId": "CWE-476"}]}
        assert result[1] == {"systemName": "sys2", "findings": []}

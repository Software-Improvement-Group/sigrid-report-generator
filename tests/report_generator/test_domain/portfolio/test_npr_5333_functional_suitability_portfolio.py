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
from report_generator.generator.context.sigrid_api import SigridAPIRequestFailedError
from report_generator.generator.domain.portfolio.npr_5333_functional_suitability_portfolio import (
    Npr5333FunctionalSuitabilityPortfolioData,
    npr_5333_functional_suitability_portfolio_data,
)

_PATCH_TARGET = "report_generator.generator.domain.portfolio.npr_5333_functional_suitability_portfolio.sigrid_api"


class TestNpr5333SystemNames:
    """Tests for system_names: sorted union of reliability and security systems."""

    def test_union_includes_all_systems(self):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["_reliability_ratings"] = [
            {"systemName": "sys1"},
            {"systemName": "sys2"},
        ]
        instance.__dict__["_security_ratings"] = [
            {"systemName": "sys2"},
            {"systemName": "sys3"},
        ]

        assert instance.system_names == ["sys1", "sys2", "sys3"]

    def test_reliability_only_systems_included(self):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["_reliability_ratings"] = [{"systemName": "rel-only"}]
        instance.__dict__["_security_ratings"] = []

        assert instance.system_names == ["rel-only"]

    def test_security_only_systems_included(self):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["_reliability_ratings"] = []
        instance.__dict__["_security_ratings"] = [{"systemName": "sec-only"}]

        assert instance.system_names == ["sec-only"]

    def test_system_names_are_sorted(self):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["_reliability_ratings"] = [{"systemName": "zzz"}]
        instance.__dict__["_security_ratings"] = [{"systemName": "aaa"}]

        assert instance.system_names == ["aaa", "zzz"]


class TestNpr5333Findings:
    """Tests for the findings property: merge, deduplicate, filter by CWE."""

    def teardown_method(self):
        reset_context()
        for attr in [
            "_reliability_ratings",
            "_security_ratings",
            "system_names",
            "findings",
        ]:
            npr_5333_functional_suitability_portfolio_data.__dict__.pop(attr, None)

    @patch(_PATCH_TARGET)
    def test_deduplicates_by_id(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = ["sys1"]
        shared = {"id": "dup-1", "cweId": "CWE-476", "severity": "HIGH"}
        mock_api.get_reliability_findings.return_value = [shared]
        mock_api.get_security_findings.return_value = [shared]

        result = instance.findings

        assert len(result[0]["findings"]) == 1
        assert result[0]["findings"][0]["id"] == "dup-1"

    @patch(_PATCH_TARGET)
    def test_unique_findings_from_both_sources_are_kept(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = ["sys1"]
        mock_api.get_reliability_findings.return_value = [
            {"id": "r1", "cweId": "CWE-476", "severity": "HIGH"}
        ]
        mock_api.get_security_findings.return_value = [
            {"id": "s1", "cweId": "CWE-682", "severity": "MEDIUM"}
        ]

        result = instance.findings

        assert len(result[0]["findings"]) == 2

    @patch(_PATCH_TARGET)
    def test_filters_to_npr5333_cwes_only(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = ["sys1"]
        mock_api.get_reliability_findings.return_value = [
            {"id": "r1", "cweId": "CWE-476"},
            {"id": "r2", "cweId": "CWE-999"},
        ]
        mock_api.get_security_findings.return_value = [
            {"id": "s1", "cweId": "CWE-835"},
            {"id": "s2", "cweId": "CWE-111"},
        ]

        result = instance.findings

        cwes = {f["cweId"] for f in result[0]["findings"]}
        assert cwes == {"CWE-476", "CWE-835"}

    @patch(_PATCH_TARGET)
    def test_finding_without_cwe_is_excluded(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = ["sys1"]
        mock_api.get_reliability_findings.return_value = [
            {"id": "r1", "severity": "HIGH"},
            {"id": "r2", "cweId": None, "severity": "MEDIUM"},
        ]
        mock_api.get_security_findings.return_value = []

        result = instance.findings

        assert result[0]["findings"] == []

    @patch(_PATCH_TARGET)
    def test_reliability_api_failure_falls_back_to_empty(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = ["sys1"]
        mock_api.get_reliability_findings.side_effect = SigridAPIRequestFailedError(
            "get_reliability_findings"
        )
        mock_api.get_security_findings.return_value = [{"id": "s1", "cweId": "CWE-476"}]

        result = instance.findings

        assert len(result[0]["findings"]) == 1
        assert result[0]["findings"][0]["id"] == "s1"

    @patch(_PATCH_TARGET)
    def test_security_api_failure_falls_back_to_empty(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = ["sys1"]
        mock_api.get_reliability_findings.return_value = [
            {"id": "r1", "cweId": "CWE-682"}
        ]
        mock_api.get_security_findings.side_effect = SigridAPIRequestFailedError(
            "get_security_findings"
        )

        result = instance.findings

        assert len(result[0]["findings"]) == 1
        assert result[0]["findings"][0]["id"] == "r1"

    @patch(_PATCH_TARGET)
    def test_multiple_systems_filtered_independently(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = ["sys1", "sys2"]
        mock_api.get_reliability_findings.side_effect = [
            [{"id": "r1", "cweId": "CWE-476"}],
            [{"id": "r2", "cweId": "CWE-999"}],
        ]
        mock_api.get_security_findings.return_value = []

        result = instance.findings

        assert len(result[0]["findings"]) == 1
        assert result[0]["findings"][0]["cweId"] == "CWE-476"
        assert result[1]["findings"] == []

    @patch(_PATCH_TARGET)
    def test_empty_portfolio_returns_empty_list(self, mock_api):
        instance = Npr5333FunctionalSuitabilityPortfolioData()
        instance.__dict__["system_names"] = []

        result = instance.findings

        assert result == []

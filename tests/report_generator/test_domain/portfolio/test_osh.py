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

from typing import ClassVar
from unittest.mock import patch

import pytest

from report_generator.generator.context.portfolio_filters import reset_context
from report_generator.generator.domain.portfolio.osh_portfolio import (
    OSHRatingsPortfolioData,
    osh_portfolio_data,
)


class TestOSHPortfolioData:
    """Test cases for OSHRatingsPortfolioData model."""

    def setup_method(self):
        """Reset portfolio context before each test."""
        reset_context()

    def teardown_method(self):
        """Clean up portfolio context and cached data after each test."""
        reset_context()

        cache_attrs = ["raw_data", "metadata", "period", "system_names"]
        for attr in cache_attrs:
            osh_portfolio_data.__dict__.pop(attr, None)

    def test_extract_osh_rating_with_valid_data(self):
        """Test _extract_osh_rating extracts ratings correctly from SBOM metadata."""
        portfolio = OSHRatingsPortfolioData()
        system = {
            "sbom": {
                "metadata": {
                    "properties": [
                        {"name": "sigrid:ratings:system", "value": "4.5"},
                        {"name": "sigrid:ratings:vulnerability", "value": "3.2"},
                    ]
                }
            }
        }

        rating = portfolio._extract_osh_rating(system, "system")
        assert rating == pytest.approx(4.5)

        rating = portfolio._extract_osh_rating(system, "vulnerability")
        assert rating == pytest.approx(3.2)

    def test_extract_osh_rating_with_missing_metadata(self):
        """Test _extract_osh_rating returns None when metadata is missing."""
        portfolio = OSHRatingsPortfolioData()
        system = {"sbom": {}}

        rating = portfolio._extract_osh_rating(system, "system")
        assert rating is None

    def test_extract_osh_rating_with_missing_property(self):
        """Test _extract_osh_rating returns None when requested property doesn't exist."""
        portfolio = OSHRatingsPortfolioData()
        system = {
            "sbom": {
                "metadata": {
                    "properties": [
                        {"name": "sigrid:ratings:vulnerability", "value": "3.2"}
                    ]
                }
            }
        }

        rating = portfolio._extract_osh_rating(system, "system")
        assert rating is None

    def test_extract_osh_rating_with_invalid_value(self):
        """Test _extract_osh_rating returns None when rating value is not a valid float."""
        portfolio = OSHRatingsPortfolioData()
        system = {
            "sbom": {
                "metadata": {
                    "properties": [
                        {"name": "sigrid:ratings:system", "value": "invalid"}
                    ]
                }
            }
        }

        rating = portfolio._extract_osh_rating(system, "system")
        assert rating is None

    @patch("report_generator.generator.domain.portfolio.osh_portfolio.sigrid_api")
    def test_get_system_returns_correct_system(self, mock_sigrid_api):
        """Test that get_system returns correct system data."""
        mock_data = {
            "systems": [
                {"systemName": "system1", "oshRating": 4.5},
                {"systemName": "system2", "oshRating": 3.8},
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data

        osh_portfolio_data.__dict__.pop("raw_data", None)

        system = osh_portfolio_data.get_system("system1")

        assert system is not None
        assert system["systemName"] == "system1"
        assert abs(system["oshRating"] - 4.5) < 0.01

    @patch("report_generator.generator.domain.portfolio.osh_portfolio.sigrid_api")
    def test_find_system_returns_correct_system(self, mock_sigrid_api):
        """Test that find_system returns correct system data (alias for get_system)."""
        mock_data = {"systems": [{"systemName": "system1", "oshRating": 4.5}]}
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data

        osh_portfolio_data.__dict__.pop("raw_data", None)

        system = osh_portfolio_data.find_system("system1")

        assert system is not None
        assert system["systemName"] == "system1"

    @patch("report_generator.generator.domain.portfolio.osh_portfolio.sigrid_api")
    def test_system_names_returns_all_systems(self, mock_sigrid_api):
        """Test that system_names property returns all system names."""
        mock_data = {
            "systems": [
                {"systemName": "system1", "oshRating": 4.5},
                {"systemName": "system2", "oshRating": 3.8},
                {"systemName": "system3", "oshRating": 4.2},
            ]
        }
        mock_sigrid_api.get_portfolio_osh_findings.return_value = mock_data

        for attr in ["raw_data", "data", "system_names"]:
            osh_portfolio_data.__dict__.pop(attr, None)

        names = osh_portfolio_data.system_names

        assert len(names) == 3
        assert "system1" in names
        assert "system2" in names
        assert "system3" in names

    @patch("report_generator.generator.domain.portfolio.osh_portfolio.sigrid_api")
    def test_get_property_rating_returns_metric_value(self, mock_sigrid_api):
        mock_sigrid_api.get_portfolio_osh_findings.return_value = {
            "systems": [
                {
                    "systemName": "system1",
                    "sbom": {
                        "metadata": {
                            "properties": [
                                {"name": "sigrid:ratings:vulnerability", "value": "3.2"}
                            ]
                        }
                    },
                }
            ]
        }
        osh_portfolio_data.__dict__.pop("raw_data", None)

        rating = osh_portfolio_data.get_property_rating("system1", "vulnerability")

        assert rating == pytest.approx(3.2)

    @patch("report_generator.generator.domain.portfolio.osh_portfolio.sigrid_api")
    def test_get_property_rating_returns_none_for_unknown_system(self, mock_sigrid_api):
        mock_sigrid_api.get_portfolio_osh_findings.return_value = {
            "systems": [{"systemName": "system1", "sbom": {}}]
        }
        osh_portfolio_data.__dict__.pop("raw_data", None)

        assert (
            osh_portfolio_data.get_property_rating("missing", "vulnerability") is None
        )


class _StubOSHMetrics:
    """Stub implementations of OSHMetricsBase abstract methods for testing."""

    @property
    def vulnerability_distribution(self) -> dict[str, int]:
        return {}

    @property
    def cves_mapped_to_libraries(self) -> dict[str, dict]:
        return {}

    @property
    def age_distribution(self) -> list[int]:
        return []


class TestOSHMetricsBase:
    """Test cases for OSHMetricsBase shared metrics calculations."""

    def test_vulnerabilities_count_calculates_from_risk_distribution(self):
        """Test vulnerabilities_count sums critical to low risk levels (0-3)."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            vulnerability_risk_distribution: ClassVar[list] = [
                5,
                10,
                8,
                3,
                20,
            ]  # critical, high, medium, low, no_risk
            dependencies_count = 46

        metrics = TestMetrics()
        assert metrics.vulnerabilities_count == 26  # 5 + 10 + 8 + 3

    def test_vulnerabilities_fraction_calculates_correctly(self):
        """Test vulnerabilities_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            vulnerability_risk_distribution: ClassVar[list] = [5, 10, 8, 3, 20]
            dependencies_count = 46

        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(26 / 46)

    def test_vulnerabilities_fraction_returns_zero_when_no_vulnerabilities(self):
        """Test vulnerabilities_fraction returns 0.0 when count is zero."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            vulnerability_risk_distribution: ClassVar[list] = [0, 0, 0, 0, 46]
            dependencies_count = 46

        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.0)

    def test_vulnerabilities_fraction_has_minimum_floor(self):
        """Test vulnerabilities_fraction has a minimum value of 0.01."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            vulnerability_risk_distribution: ClassVar[list] = [0, 0, 0, 1, 999]
            dependencies_count = 1000

        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.01)

    def test_outdated_count_only_includes_critical_to_medium(self):
        """Test outdated_count sums critical to medium freshness risk (0-2), excluding low."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            freshness_risk_distribution: ClassVar[list] = [
                3,
                7,
                12,
                5,
                20,
            ]  # critical, high, medium, low, no_risk
            dependencies_count = 47

        metrics = TestMetrics()
        assert metrics.outdated_count == 22  # 3 + 7 + 12 (excludes low=5)

    def test_outdated_fraction_calculates_correctly(self):
        """Test outdated_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            freshness_risk_distribution: ClassVar[list] = [3, 7, 12, 5, 20]
            dependencies_count = 47

        metrics = TestMetrics()
        assert metrics.outdated_fraction == pytest.approx(22 / 47)

    def test_legal_risk_count_only_includes_critical_to_medium(self):
        """Test legal_risk_count sums critical to medium license risk (0-2), excluding low."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            legal_risk_distribution: ClassVar[list] = [
                2,
                5,
                8,
                10,
                25,
            ]  # critical, high, medium, low, no_risk
            dependencies_count = 50

        metrics = TestMetrics()
        assert metrics.legal_risk_count == 15  # 2 + 5 + 8 (excludes low=10)

    def test_legal_risk_fraction_calculates_correctly(self):
        """Test legal_risk_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            legal_risk_distribution: ClassVar[list] = [2, 5, 8, 10, 25]
            dependencies_count = 50

        metrics = TestMetrics()
        assert metrics.legal_risk_fraction == pytest.approx(15 / 50)

    def test_unmanaged_count_includes_all_risk_levels(self):
        """Test unmanaged_count sums critical to low management risk (0-3)."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            management_risk_distribution: ClassVar[list] = [
                1,
                3,
                5,
                7,
                30,
            ]  # critical, high, medium, low, no_risk
            dependencies_count = 46

        metrics = TestMetrics()
        assert metrics.unmanaged_count == 16  # 1 + 3 + 5 + 7

    def test_unmanaged_fraction_calculates_correctly(self):
        """Test unmanaged_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            management_risk_distribution: ClassVar[list] = [1, 3, 5, 7, 30]
            dependencies_count = 46

        metrics = TestMetrics()
        assert metrics.unmanaged_fraction == pytest.approx(16 / 46)

    def test_activity_risk_count_includes_all_risk_levels(self):
        """Test activity_risk_count sums critical to low activity risk (0-3)."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            activity_risk_distribution: ClassVar[list] = [
                2,
                4,
                6,
                8,
                35,
            ]  # critical, high, medium, low, no_risk
            dependencies_count = 55

        metrics = TestMetrics()
        assert metrics.activity_risk_count == 20  # 2 + 4 + 6 + 8

    def test_activity_risk_fraction_calculates_correctly(self):
        """Test activity_risk_fraction divides count by total dependencies with minimum."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            activity_risk_distribution: ClassVar[list] = [2, 4, 6, 8, 35]
            dependencies_count = 55

        metrics = TestMetrics()
        assert metrics.activity_risk_fraction == pytest.approx(20 / 55)

    def test_all_fractions_have_minimum_floor_of_0_01(self):
        """Test all fraction methods apply minimum floor of 0.01 when count is non-zero."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            vulnerability_risk_distribution: ClassVar[list] = [0, 0, 0, 1, 9999]
            freshness_risk_distribution: ClassVar[list] = [1, 0, 0, 0, 9999]
            legal_risk_distribution: ClassVar[list] = [0, 1, 0, 0, 9999]
            management_risk_distribution: ClassVar[list] = [0, 0, 0, 1, 9999]
            activity_risk_distribution: ClassVar[list] = [0, 0, 1, 0, 9999]
            dependencies_count = 10000

        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.01)
        assert metrics.outdated_fraction == pytest.approx(0.01)
        assert metrics.legal_risk_fraction == pytest.approx(0.01)
        assert metrics.unmanaged_fraction == pytest.approx(0.01)
        assert metrics.activity_risk_fraction == pytest.approx(0.01)

    def test_all_fractions_return_zero_when_counts_are_zero(self):
        """Test all fraction methods return 0.0 when respective counts are zero."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            vulnerability_risk_distribution: ClassVar[list] = [0, 0, 0, 0, 100]
            freshness_risk_distribution: ClassVar[list] = [0, 0, 0, 50, 50]
            legal_risk_distribution: ClassVar[list] = [0, 0, 0, 50, 50]
            management_risk_distribution: ClassVar[list] = [0, 0, 0, 0, 100]
            activity_risk_distribution: ClassVar[list] = [0, 0, 0, 0, 100]
            dependencies_count = 100

        metrics = TestMetrics()
        assert metrics.vulnerabilities_fraction == pytest.approx(0.0)
        assert metrics.outdated_fraction == pytest.approx(0.0)
        assert metrics.legal_risk_fraction == pytest.approx(0.0)
        assert metrics.unmanaged_fraction == pytest.approx(0.0)
        assert metrics.activity_risk_fraction == pytest.approx(0.0)

    def test_properties_are_cached(self):
        """Test that properties use @cached_property decorator and don't recalculate."""
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        call_count = {"vulnerability": 0, "freshness": 0}

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            dependencies_count = 100

            @property
            def vulnerability_risk_distribution(self):
                call_count["vulnerability"] += 1
                return [5, 10, 8, 3, 74]

            @property
            def freshness_risk_distribution(self):
                call_count["freshness"] += 1
                return [3, 7, 12, 5, 73]

            @property
            def legal_risk_distribution(self):
                return [0, 0, 0, 0, 100]

            @property
            def management_risk_distribution(self):
                return [0, 0, 0, 0, 100]

            @property
            def activity_risk_distribution(self):
                return [0, 0, 0, 0, 100]

        metrics = TestMetrics()

        # Access vulnerabilities_count multiple times
        _ = metrics.vulnerabilities_count
        _ = metrics.vulnerabilities_count
        assert call_count["vulnerability"] == 1  # Should only calculate once

        # Access outdated_count multiple times
        _ = metrics.outdated_count
        _ = metrics.outdated_count
        assert call_count["freshness"] == 1  # Should only calculate once

    def test_cves_with_epss_scores_annotates_known_cves(self):
        """Test cves_with_epss_scores adds epss-score from epss_data for known CVEs."""
        from unittest.mock import patch

        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            @property
            def cves_mapped_to_libraries(self):
                return {
                    "CVE-2023-0001": {"count": 2, "libraries": []},
                    "CVE-2023-0002": {"count": 1, "libraries": []},
                }

        with patch(
            "report_generator.generator.domain.shared.osh_base.epss_data"
        ) as mock_epss:
            mock_epss.epss_scores = {"CVE-2023-0001": 0.4, "CVE-2023-0002": 0.1}
            metrics = TestMetrics()
            result = metrics.cves_with_epss_scores

        assert result["CVE-2023-0001"]["epss-score"] == pytest.approx(0.4)
        assert result["CVE-2023-0002"]["epss-score"] == pytest.approx(0.1)

    def test_cves_with_epss_scores_sets_none_for_unknown_cves(self):
        """Test cves_with_epss_scores sets epss-score to None for CVEs not in epss_data."""
        from unittest.mock import patch

        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            @property
            def cves_mapped_to_libraries(self):
                return {"CVE-2023-9999": {"count": 1, "libraries": []}}

        with patch(
            "report_generator.generator.domain.shared.osh_base.epss_data"
        ) as mock_epss:
            mock_epss.epss_scores = {}
            metrics = TestMetrics()
            result = metrics.cves_with_epss_scores

        assert result["CVE-2023-9999"]["epss-score"] is None

    def test_exploit_probability_calculated_correctly(self):
        """Test exploit_probability uses complement product formula across all CVEs."""
        from unittest.mock import patch

        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            @property
            def cves_mapped_to_libraries(self):
                return {
                    "CVE-2023-0001": {"count": 1, "libraries": []},
                    "CVE-2023-0002": {"count": 2, "libraries": []},
                }

        with patch(
            "report_generator.generator.domain.shared.osh_base.epss_data"
        ) as mock_epss:
            mock_epss.epss_scores = {"CVE-2023-0001": 0.3, "CVE-2023-0002": 0.2}
            metrics = TestMetrics()
            result = metrics.exploit_probability

        # 1 - (1 - 0.3)^1 * (1 - 0.2)^2 = 1 - 0.7 * 0.64 = 1 - 0.448 = 0.552
        assert result == pytest.approx(0.552)

    def test_exploit_probability_skips_cves_without_epss_score(self):
        """Test exploit_probability ignores CVEs where epss-score is None."""
        from unittest.mock import patch

        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            @property
            def cves_mapped_to_libraries(self):
                return {
                    "CVE-2023-0001": {"count": 1, "libraries": []},
                    "CVE-2023-9999": {"count": 5, "libraries": []},  # not in EPSS
                }

        with patch(
            "report_generator.generator.domain.shared.osh_base.epss_data"
        ) as mock_epss:
            mock_epss.epss_scores = {"CVE-2023-0001": 0.5}
            metrics = TestMetrics()
            result = metrics.exploit_probability

        # Only CVE-2023-0001 contributes: 1 - (1 - 0.5)^1 = 0.5
        assert result == pytest.approx(0.5)

    def test_exploit_probability_capped_at_0_9999(self):
        """Test exploit_probability is capped at 0.9999."""
        from unittest.mock import patch

        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            @property
            def cves_mapped_to_libraries(self):
                return {"CVE-2023-0001": {"count": 100, "libraries": []}}

        with patch(
            "report_generator.generator.domain.shared.osh_base.epss_data"
        ) as mock_epss:
            mock_epss.epss_scores = {"CVE-2023-0001": 0.99}
            metrics = TestMetrics()
            result = metrics.exploit_probability

        assert result <= 0.9999

    def test_exploit_probability_is_zero_when_no_cves(self):
        """Test exploit_probability returns 0.0 when there are no CVEs."""
        from unittest.mock import patch

        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            @property
            def cves_mapped_to_libraries(self):
                return {}

        with patch(
            "report_generator.generator.domain.shared.osh_base.epss_data"
        ) as mock_epss:
            mock_epss.epss_scores = {}
            metrics = TestMetrics()
            result = metrics.exploit_probability

        assert result == pytest.approx(0.0)


def _make_component(name, version, risks: dict):
    """Build a CycloneDX-style component dict with sigrid risk properties."""
    risk_key_map = {
        "vulnerability": "sigrid:risk:vulnerability",
        "legal": "sigrid:risk:legal",
        "freshness": "sigrid:risk:freshness",
        "stability": "sigrid:risk:stability",
        "management": "sigrid:risk:management",
        "activity": "sigrid:risk:activity",
    }
    properties = [
        {"name": risk_key_map[k], "value": v}
        for k, v in risks.items()
        if k in risk_key_map
    ]
    return {"name": name, "version": version, "properties": properties}


class TestLibraryRiskLevelsBase:
    """Tests for library_risk_levels via OSHMetricsBase shared logic."""

    def test_get_risk_value_returns_correct_integer(self):
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            pass

        base = TestMetrics()
        props = [{"name": "sigrid:risk:vulnerability", "value": "CRITICAL"}]
        assert base._get_risk_value(props, "sigrid:risk:vulnerability") == 0

        props = [{"name": "sigrid:risk:vulnerability", "value": "HIGH"}]
        assert base._get_risk_value(props, "sigrid:risk:vulnerability") == 1

        props = [{"name": "sigrid:risk:vulnerability", "value": "MEDIUM"}]
        assert base._get_risk_value(props, "sigrid:risk:vulnerability") == 2

        props = [{"name": "sigrid:risk:vulnerability", "value": "LOW"}]
        assert base._get_risk_value(props, "sigrid:risk:vulnerability") == 3

    def test_get_risk_value_returns_no_risk_for_unknown(self):
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            pass

        base = TestMetrics()
        assert base._get_risk_value([], "sigrid:risk:vulnerability") == 4
        props = [{"name": "sigrid:risk:vulnerability", "value": "UNKNOWN"}]
        assert base._get_risk_value(props, "sigrid:risk:vulnerability") == 4

    def test_highest_risk_for_component_uses_worst_category(self):
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            pass

        base = TestMetrics()
        component = _make_component(
            "lib",
            "1.0",
            {
                "vulnerability": "LOW",
                "legal": "CRITICAL",
                "freshness": "MEDIUM",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        assert base._highest_risk_for_component(component) == 0

    def test_highest_risk_for_component_no_risk_when_all_missing(self):
        from report_generator.generator.domain.shared.osh_base import OSHMetricsBase

        class TestMetrics(_StubOSHMetrics, OSHMetricsBase):
            pass

        base = TestMetrics()
        assert base._highest_risk_for_component({"properties": []}) == 4


class TestLibraryRiskLevelsPortfolio:
    """Tests for library_risk_levels on OSHRatingsPortfolioData."""

    def _portfolio_with_raw(self, systems):
        portfolio = OSHRatingsPortfolioData()
        portfolio.__dict__["raw_data"] = {"systems": systems}
        return portfolio

    def test_counts_single_library(self):
        component = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "HIGH",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        portfolio = self._portfolio_with_raw(
            [{"systemName": "sys1", "sbom": {"components": [component]}}]
        )
        result = portfolio.library_risk_levels
        assert result["high"] == 1
        assert result["critical"] == 0

    def test_same_library_across_systems_counted_per_occurrence(self):
        """Same name:version seen in two systems is counted twice (once per occurrence)."""
        component = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "HIGH",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        portfolio = self._portfolio_with_raw(
            [
                {"systemName": "sys1", "sbom": {"components": [component]}},
                {"systemName": "sys2", "sbom": {"components": [component]}},
            ]
        )
        result = portfolio.library_risk_levels
        assert sum(result.values()) == 2

    def test_same_library_with_different_risks_counted_per_occurrence(self):
        """Each component occurrence is counted independently, not deduplicated."""
        low_risk = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "LOW",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        critical_risk = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "CRITICAL",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        portfolio = self._portfolio_with_raw(
            [
                {"systemName": "sys1", "sbom": {"components": [low_risk]}},
                {"systemName": "sys2", "sbom": {"components": [critical_risk]}},
            ]
        )
        result = portfolio.library_risk_levels
        assert result["critical"] == 1
        assert result["low"] == 1
        assert sum(result.values()) == 2

    def test_empty_data_returns_zero_counts(self):
        portfolio = self._portfolio_with_raw([])
        result = portfolio.library_risk_levels
        assert result == {"critical": 0, "high": 0, "medium": 0, "low": 0, "no_risk": 0}

    def test_multiple_distinct_libraries(self):
        components = [
            _make_component(
                "lib-a",
                "1.0",
                {
                    "vulnerability": "CRITICAL",
                    "legal": "LOW",
                    "freshness": "LOW",
                    "stability": "LOW",
                    "management": "LOW",
                    "activity": "LOW",
                },
            ),
            _make_component(
                "lib-b",
                "1.0",
                {
                    "vulnerability": "LOW",
                    "legal": "LOW",
                    "freshness": "LOW",
                    "stability": "LOW",
                    "management": "LOW",
                    "activity": "LOW",
                },
            ),
            _make_component(
                "lib-c",
                "1.0",
                {
                    "vulnerability": "HIGH",
                    "legal": "LOW",
                    "freshness": "LOW",
                    "stability": "LOW",
                    "management": "LOW",
                    "activity": "LOW",
                },
            ),
        ]
        portfolio = self._portfolio_with_raw(
            [{"systemName": "sys1", "sbom": {"components": components}}]
        )
        result = portfolio.library_risk_levels
        assert result["critical"] == 1
        assert result["high"] == 1
        assert result["low"] == 1
        assert sum(result.values()) == 3


class TestLibraryRiskLevelsSystem:
    """Tests for library_risk_levels on OSHData (system level)."""

    def _osh_with_components(self, components):
        from report_generator.generator.domain.system.osh import OSHData

        instance = OSHData()
        instance.__dict__["raw_data"] = {
            "components": components,
            "metadata": {"properties": []},
        }
        return instance

    def test_counts_single_library(self):
        component = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "MEDIUM",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        result = self._osh_with_components([component]).library_risk_levels
        assert result["medium"] == 1
        assert sum(result.values()) == 1

    def test_same_library_counted_per_occurrence(self):
        component = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "HIGH",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        result = self._osh_with_components([component, component]).library_risk_levels
        assert sum(result.values()) == 2

    def test_components_with_different_risks_counted_independently(self):
        low = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "LOW",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        critical = _make_component(
            "requests",
            "2.28.0",
            {
                "vulnerability": "CRITICAL",
                "legal": "LOW",
                "freshness": "LOW",
                "stability": "LOW",
                "management": "LOW",
                "activity": "LOW",
            },
        )
        result = self._osh_with_components([low, critical]).library_risk_levels
        assert result["critical"] == 1
        assert result["low"] == 1
        assert sum(result.values()) == 2

    def test_empty_data_returns_zero_counts(self):
        result = self._osh_with_components([]).library_risk_levels
        assert result == {"critical": 0, "high": 0, "medium": 0, "low": 0, "no_risk": 0}

    def test_no_risk_library(self):
        component = _make_component("lib", "1.0", {})
        result = self._osh_with_components([component]).library_risk_levels
        assert result["no_risk"] == 1

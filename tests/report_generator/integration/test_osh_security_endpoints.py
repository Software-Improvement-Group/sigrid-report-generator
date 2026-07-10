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

"""Live-API tests for the OSH and Security ratings/findings endpoints.

These endpoints return real-time data, so their exact values cannot be pinned to a golden
file (the golden-file suite in test_report_generation.py replays synthetic fixtures instead).
The value these tests add over the unit tests — which mock the API with hand-authored dicts —
is catching **API contract drift**: they hit the real endpoints and assert (A) the response
shape the domain layer parses still exists, (B) the domain values stay within sane invariants,
and (C) the recorded fixtures still match the live shape (so the golden-file suite can't
silently rot).

Requires a live Sigrid token for the reportgeneratordemo tenant; excluded from the default
run via the `integration` marker.
"""

import pytest

from report_generator.generator.context import sigrid_api
from report_generator.generator.domain.portfolio.osh_portfolio import osh_portfolio_data
from report_generator.generator.domain.portfolio.security_portfolio import (
    security_ratings_portfolio_data,
)
from report_generator.generator.domain.system.osh import osh_data
from report_generator.generator.domain.system.security import security_data
from report_generator.generator.utils.constants.severity import SEVERITY_ORDER
from tests.report_generator.integration import _shared

pytestmark = pytest.mark.integration

SYSTEM = "integrationtest-kafka"
RATING_MIN, RATING_MAX = 0.5, 5.5
RISK_LABELS = ("critical", "high", "medium", "low", "no_risk")


@pytest.fixture(autouse=True)
def live_context():
    """Set live context and ensure OSH/Security domain caches never leak between tests."""
    token = _shared.resolve_token()
    if not token:
        pytest.skip(
            "No Sigrid token set (SIGRID_REPORTGENERATORDEMO_TOKEN / SIGRID_TOKEN / SIGRID_CI_TOKEN)"
        )
    _shared.reset_osh_security_domain_caches()
    sigrid_api.reset_context()
    sigrid_api.set_context(
        bearer_token=token,
        customer="reportgeneratordemo",
        system=SYSTEM,
        period=_shared.PERIOD,
    )
    yield
    _shared.reset_osh_security_domain_caches()
    sigrid_api.reset_context()


# --------------------------------------------------------------------------------------
# A. Contract / schema — the fields the domain layer reads must exist in the live response
# --------------------------------------------------------------------------------------


def _property_names(properties: list[dict]) -> set[str]:
    return {p.get("name") for p in properties}


def test_osh_findings_contract():
    sbom = sigrid_api.get_osh_findings()
    assert isinstance(sbom["metadata"]["timestamp"], str)
    rating_props = _property_names(sbom["metadata"]["properties"])
    assert "sigrid:ratings:system" in rating_props
    assert sbom["components"], "expected at least one SBOM component"
    for component in sbom["components"]:
        assert "sigrid:risk:vulnerability" in _property_names(component["properties"])


def test_portfolio_osh_findings_contract():
    data = sigrid_api.get_portfolio_osh_findings()
    assert data["systems"], "expected at least one system"
    for system in data["systems"]:
        assert "systemName" in system
        sbom = system["sbom"]
        assert "sigrid:ratings:system" in _property_names(
            sbom["metadata"]["properties"]
        )
        assert isinstance(sbom["components"], list)


def test_security_findings_contract():
    findings = sigrid_api.get_security_findings()
    assert isinstance(findings, list)
    for finding in findings:
        assert finding["severity"] in SEVERITY_ORDER, (
            f"unknown severity {finding['severity']!r}"
        )


def test_security_ratings_contract():
    ratings = sigrid_api.get_security_ratings()
    assert "rating" in ratings
    assert RATING_MIN <= ratings["rating"] <= RATING_MAX


def test_portfolio_security_ratings_contract():
    ratings = sigrid_api.get_portfolio_security_ratings()
    assert isinstance(ratings, list) and ratings
    for entry in ratings:
        assert "systemName" in entry
        assert (
            entry.get("rating") is None or RATING_MIN <= entry["rating"] <= RATING_MAX
        )


# --------------------------------------------------------------------------------------
# B. Invariants — domain values derived from live data must hold regardless of the day
# --------------------------------------------------------------------------------------


def _assert_valid_distribution(distribution: list[int], total: int):
    assert len(distribution) == 5
    assert all(isinstance(count, int) and count >= 0 for count in distribution)
    assert sum(distribution) == total


def test_system_osh_invariants():
    total = osh_data.dependencies_count
    assert total >= 0
    assert RATING_MIN <= osh_data.system_rating <= RATING_MAX
    for distribution in osh_data.risk_distributions.values():
        _assert_valid_distribution(distribution, total)


def test_portfolio_osh_invariants():
    total = osh_portfolio_data.dependencies_count
    assert total >= 0
    for distribution in osh_portfolio_data.risk_distributions.values():
        _assert_valid_distribution(distribution, total)
    for prop in (
        "system",
        "vulnerability",
        "licenses",
        "freshness",
        "management",
        "activity",
    ):
        assert 0.0 <= osh_portfolio_data.get_score_for_prop(prop) <= RATING_MAX
    assert sum(osh_portfolio_data.library_risk_levels.values()) == total
    assert set(osh_portfolio_data.library_risk_levels) == set(RISK_LABELS)


def test_system_security_invariants():
    rating = security_data.security_rating
    assert rating is None or RATING_MIN <= rating <= RATING_MAX
    for severity in SEVERITY_ORDER:
        assert security_data.count_findings(severity) >= 0


def test_portfolio_security_rating_distribution_invariants():
    percentages = security_ratings_portfolio_data.rating_distribution_percentages
    assert set(percentages) == {"above_market", "market_average", "below_market"}
    assert all(value >= 0 for value in percentages.values())
    total = sum(percentages.values())
    assert total == 0 or 99 <= total <= 101  # rounding of three buckets


# --------------------------------------------------------------------------------------
# C. Freshness guard — the live shape must still contain everything the fixtures assume
# --------------------------------------------------------------------------------------


def _key_paths(obj, prefix="", *, union_lists):
    """Collect the set of dotted key paths in a JSON structure.

    Lists are collapsed to a single "[]" segment. With union_lists=True (the live response),
    paths are unioned across all list elements, so keys present on only some elements — e.g.
    an optional `licenses` on some SBOM components — still count as available.
    """
    paths: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{prefix}.{key}" if prefix else key
            paths.add(child)
            paths |= _key_paths(value, child, union_lists=union_lists)
    elif isinstance(obj, list):
        elements = obj if union_lists else obj[:1]
        for element in elements:
            paths |= _key_paths(element, f"{prefix}[]", union_lists=union_lists)
    return paths


@pytest.mark.parametrize("endpoint", _shared.VOLATILE_ENDPOINTS)
def test_fixture_shape_matches_live(endpoint):
    """Every key path our synthetic fixture assumes must still exist in the live response.

    This ties the pinned golden-file suite to reality: if Sigrid renames or removes a field
    the fixtures (and the domain layer) rely on, this fails loudly instead of the references
    silently going stale. Extra keys in the live response are fine.
    """
    live = getattr(sigrid_api, endpoint)()
    fixture = _shared.load_fixture(endpoint)
    missing = _key_paths(fixture, union_lists=False) - _key_paths(
        live, union_lists=True
    )
    assert not missing, (
        f"Live '{endpoint}' response is missing key paths the fixtures assume: {sorted(missing)}.\n"
        f"The API contract changed — update build_fake_fixtures.py to the new shape, regenerate "
        f"the fixtures, and refresh the references with update_references.py."
    )

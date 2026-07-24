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

import contextlib
import copy
import json
import os
from pathlib import Path
from unittest import mock

from report_generator import presets
from report_generator.generator.context import sigrid_api

PERIOD = ("2026-01-11", "2026-03-08")

INTEGRATION_DIR = Path(__file__).parent
TEMPLATES_DIR = INTEGRATION_DIR / "templates"
REFERENCES_DIR = INTEGRATION_DIR / "references"
FIXTURES_DIR = INTEGRATION_DIR / "fixtures" / "osh_security"

# OSH/Security ratings and findings endpoints return real-time data (a newly found
# vulnerability appears immediately), so they cannot serve as stable golden-file inputs.
# The golden-file suite replays the deterministic fixtures under fixtures/osh_security/
# instead. These are the sigrid_api functions to pin; see build_fake_fixtures.py.
VOLATILE_ENDPOINTS = (
    "get_portfolio_osh_findings",
    "get_osh_findings",
    "get_security_findings",
    "get_security_ratings",
    "get_portfolio_security_ratings",
)

# Domain singletons whose cached data derives from the volatile endpoints. Their caches
# must be cleared when switching between pinned (golden-file) and live (endpoint) tests,
# because module-level singletons persist across tests in a single pytest session.
_OSH_SECURITY_SINGLETON_PATHS = (
    ("report_generator.generator.domain.system.osh", "osh_data"),
    ("report_generator.generator.domain.system.security", "security_data"),
    ("report_generator.generator.domain.portfolio.osh_portfolio", "osh_portfolio_data"),
    (
        "report_generator.generator.domain.portfolio.security_portfolio",
        "security_ratings_portfolio_data",
    ),
    (
        "report_generator.generator.domain.portfolio.security_findings_portfolio",
        "security_findings_portfolio_data",
    ),
    (
        "report_generator.generator.domain.portfolio.security_dashboard_findings_portfolio",
        "security_dashboard_findings_portfolio_data",
    ),
    (
        "report_generator.generator.domain.portfolio.security_dashboard_resolution_times_portfolio",
        "security_dashboard_resolution_times_portfolio_data",
    ),
    (
        "report_generator.generator.domain.portfolio.npr_5333_functional_suitability_portfolio",
        "npr_5333_functional_suitability_portfolio_data",
    ),
)


def load_fixture(endpoint: str) -> object:
    return json.loads((FIXTURES_DIR / f"{endpoint}.json").read_text())


def reset_osh_security_domain_caches() -> None:
    """Drop cached data on the OSH/Security domain singletons (cached_property + lru_cache)."""
    import importlib

    for module_path, attr in _OSH_SECURITY_SINGLETON_PATHS:
        try:
            singleton = getattr(importlib.import_module(module_path), attr)
        except (ImportError, AttributeError):
            continue
        singleton.__dict__.clear()  # cached_property values live in the instance __dict__
        for name in dir(type(singleton)):
            member = getattr(type(singleton), name, None)
            if hasattr(member, "cache_clear"):  # lru_cache-wrapped methods
                member.cache_clear()


def _fixture_stub(endpoint: str):
    payload = load_fixture(endpoint)

    def stub(*_args, **_kwargs):
        # System-parameterized endpoints ignore the requested system and return the same
        # canonical fixture; portfolio endpoints take no system. Deep-copy so downstream
        # mutation never leaks between callers.
        return copy.deepcopy(payload)

    return stub


def pin_volatile_endpoints(monkeypatch) -> None:
    """Replay fixtures for the volatile OSH/Security endpoints (pytest monkeypatch)."""
    reset_osh_security_domain_caches()
    for endpoint in VOLATILE_ENDPOINTS:
        monkeypatch.setattr(sigrid_api, endpoint, _fixture_stub(endpoint))


@contextlib.contextmanager
def pinned_volatile_endpoints():
    """Same as pin_volatile_endpoints, but usable outside pytest (e.g. update_references.py)."""
    reset_osh_security_domain_caches()
    with contextlib.ExitStack() as stack:
        for endpoint in VOLATILE_ENDPOINTS:
            stack.enter_context(
                mock.patch.object(sigrid_api, endpoint, _fixture_stub(endpoint))
            )
        yield


def resolve_token() -> str | None:
    return (
        os.environ.get("SIGRID_REPORTGENERATORDEMO_TOKEN")
        or os.environ.get("SIGRID_TOKEN")
        or os.environ.get("SIGRID_CI_TOKEN")
    )


def system_for_preset(preset_id: str) -> str | None:
    return (
        "integrationtest-kafka" if preset_id in presets.SYSTEM_LEVEL_PRESETS else None
    )

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

"""Generate synthetic OSH/Security fixtures for the integration tests.

The OSH and Security *ratings* and *findings* endpoints return real-time data (a new
vulnerability found today shows up immediately), so their live responses cannot be used as
stable golden-file inputs. Instead the golden-file suite replays these hand-authored, fully
deterministic fixtures — same shape as the real API, but with made-up values that never drift.

These fixtures contain NO real API response data. System *names* are the demo tenant's
(already hard-coded elsewhere in the tests); every rating, finding, and risk value is fake.

Regenerate with:
    python tests/report_generator/integration/build_fake_fixtures.py
Then re-run update_references.py for the affected presets so the references match.
"""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "osh_security"

# Demo-tenant system names (benign identifiers; values below are all synthetic).
SYSTEMS = [
    "integrationtest-zuul",
    "integrationtest-facebookyoga",
    "integrationtest-jruby",
    "integrationtest-webpack",
    "integrationtest-git",
    "integrationtest-bazel",
    "integrationtest-electron",
    "integrationtest-druid",
    "integrationtest-kafka",
    "integrationtest-airflow",
    "integrationtest-vscode",
    "integrationtest-elasticsearch",
]

_RISK_CYCLE = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE", "UNKNOWN"]
_SECURITY_CATEGORY_NAMES = [
    ("a10", "A10:2025 - Mishandling of Exceptional Conditions"),
    ("a1", "A01:2025 - Broken Access Control"),
    ("a2", "A02:2025 - Security Misconfiguration"),
    ("a3", "A03:2025 - Software Supply Chain Failures"),
    ("a4", "A04:2025 - Cryptographic Failures"),
]


def _clamp_rating(value: float) -> float:
    return round(min(max(value, 0.5), 5.5), 3)


def _ratings_properties(system_index: int) -> list[dict]:
    i = system_index
    return [
        {"name": "OSHModelVersion", "value": "2024_OSH_SIG"},
        {
            "name": "sigrid:ratings:system",
            "value": str(_clamp_rating(2.0 + (i % 5) * 0.6)),
        },
        {
            "name": "sigrid:ratings:vulnerability",
            "value": str(_clamp_rating(3.0 + (i % 4) * 0.5)),
        },
        {
            "name": "sigrid:ratings:licenses",
            "value": str(_clamp_rating(4.0 - (i % 3) * 0.5)),
        },
        {
            "name": "sigrid:ratings:freshness",
            "value": str(_clamp_rating(2.5 + (i % 3) * 0.4)),
        },
        {
            "name": "sigrid:ratings:management",
            "value": str(_clamp_rating(3.5 - (i % 4) * 0.3)),
        },
        {
            "name": "sigrid:ratings:activity",
            "value": str(_clamp_rating(2.0 + (i % 5) * 0.5)),
        },
    ]


def _component(system_index: int, component_index: int) -> dict:
    i, j = system_index, component_index

    def risk(offset: int) -> str:
        return _RISK_CYCLE[(i + j + offset) % len(_RISK_CYCLE)]

    version = f"1.{j}.0"
    return {
        "type": "library",
        "bom-ref": f"pkg:maven/com.example/lib-{i}-{j}@{version}?package-id=fake{i:02d}{j:02d}",
        "group": "com.example",
        "name": f"lib-{i}-{j}",
        "version": version,
        "licenses": [{"license": {"name": "Apache-2.0"}}],
        "purl": f"pkg:maven/com.example/lib-{i}-{j}@{version}",
        "properties": [
            {"name": "sigrid:risk:vulnerability", "value": risk(0)},
            {"name": "sigrid:risk:legal", "value": risk(1)},
            {"name": "sigrid:risk:freshness", "value": risk(2)},
            {"name": "sigrid:risk:stability", "value": risk(3)},
            {"name": "sigrid:risk:management", "value": risk(4)},
            {"name": "sigrid:risk:activity", "value": risk(5)},
            {"name": "sigrid:releaseDate", "value": "2024-01-15T00:00:00Z"},
            {"name": "sigrid:next:version", "value": f"1.{j}.1"},
            {
                "name": "sigrid:next:releaseDate",
                "value": f"2024-{(j % 12) + 1:02d}-01T00:00:00Z",
            },
            {"name": "sigrid:latest:version", "value": "2.0.0"},
            {"name": "sigrid:latest:releaseDate", "value": "2026-01-01T00:00:00Z"},
            {
                "name": "sigrid:transitive",
                "value": "DIRECT" if j % 2 == 0 else "TRANSITIVE",
            },
        ],
        "evidence": {"occurrences": [{"location": "build.gradle"}]},
    }


def _sbom(system_index: int, system_name: str, num_components: int = 8) -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:fake{system_index:04d}-0000-0000-0000-000000000000",
        "version": 1,
        "metadata": {
            "timestamp": "2026-03-01T00:00:00Z",
            "component": {"type": "application", "name": system_name},
            "supplier": {"name": "reportgeneratordemo"},
            "properties": _ratings_properties(system_index),
        },
        "components": [_component(system_index, j) for j in range(num_components)],
        # Intentionally no CVE entries: keeps output independent of the (daily-changing)
        # external EPSS feed and of NVD advisories, so the reference stays deterministic.
        "vulnerabilities": [],
    }


def _security_categories(system_index: int) -> list[dict]:
    return [
        {
            "id": cat_id,
            "name": name,
            "adherenceScore": round(0.25 + ((system_index + k) % 3) * 0.25, 2),
            "maxSeverity": ["MEDIUM", "HIGH", "CRITICAL"][(system_index + k) % 3],
        }
        for k, (cat_id, name) in enumerate(_SECURITY_CATEGORY_NAMES)
    ]


def build_portfolio_osh_findings() -> dict:
    return {
        "customer": "reportgeneratordemo",
        "exportDate": "2026-03-08T00:00:00Z",
        "systems": [
            {
                "customerName": "reportgeneratordemo",
                "systemName": name,
                "sbom": _sbom(i, name),
            }
            for i, name in enumerate(SYSTEMS)
        ],
    }


def build_osh_findings() -> dict:
    """Canonical system-level SBOM, returned for any requested system."""
    return _sbom(
        SYSTEMS.index("integrationtest-kafka"),
        "integrationtest-kafka",
        num_components=12,
    )


def build_security_findings() -> list[dict]:
    """Canonical security findings list, returned for any requested system."""
    specs = [
        ("CRITICAL", "CWE-89", "SQL Injection", "core", "src/db/Query.java", 9.1),
        ("HIGH", "CWE-79", "Cross-Site Scripting", "web", "src/web/Render.java", 7.4),
        (
            "MEDIUM",
            "CWE-391",
            "Unchecked Exception",
            "core",
            "src/core/Worker.java",
            6.9,
        ),
        (
            "MEDIUM",
            "CWE-476",
            "NULL Pointer Dereference",
            "core",
            "src/core/Cache.java",
            5.6,
        ),
        ("LOW", "CWE-200", "Information Exposure", "api", "src/api/Error.java", 3.1),
        (
            "INFORMATION",
            "CWE-1004",
            "Sensitive Cookie",
            "web",
            "src/web/Session.java",
            1.0,
        ),
    ]
    return [
        {
            "id": f"fake-finding-{n:04d}",
            "firstSeenAnalysisDate": "2026-01-15",
            "lastSeenAnalysisDate": "2026-03-01",
            "filePath": file_path,
            "startLine": 10 + n,
            "endLine": 10 + n,
            "component": component,
            "type": finding_type,
            "cweId": cwe,
            "severity": severity,
            "impact": severity,
            "exploitability": "MEDIUM",
            "severityScore": score,
            "status": "RAW",
            "toolName": "FakeAnalyzer",
            "weaknessIds": [cwe],
            "isManualFinding": False,
            "isSeverityOverridden": False,
        }
        for n, (severity, cwe, finding_type, component, file_path, score) in enumerate(
            specs, start=1
        )
    ]


def build_security_ratings() -> dict:
    """Canonical system-level model-ratings response, returned for any requested system."""
    return {
        "id": "ow10-2025",
        "name": "OWASP Top 10 (2025)",
        "metadata": {"key": "2026", "modelVersion": "2026_security_sig"},
        "feature": "SECURITY",
        "systemId": 10008,
        "systemName": "integrationtest-kafka",
        "adherenceScore": 0.5,
        "rating": 2.5,
        "categories": _security_categories(8),
    }


def build_portfolio_security_ratings() -> list[dict]:
    return [
        {
            "id": "ow10-2025",
            "name": "OWASP Top 10 (2025)",
            "metadata": {"key": "2026", "modelVersion": "2026_security_sig"},
            "feature": "SECURITY",
            "systemId": 10000 + i,
            "systemName": name,
            "adherenceScore": round(0.3 + (i % 6) * 0.1, 2),
            "rating": _clamp_rating(1.5 + (i % 6) * 0.6),
            "categories": _security_categories(i),
        }
        for i, name in enumerate(SYSTEMS)
    ]


BUILDERS = {
    "get_portfolio_osh_findings": build_portfolio_osh_findings,
    "get_osh_findings": build_osh_findings,
    "get_security_findings": build_security_findings,
    "get_security_ratings": build_security_ratings,
    "get_portfolio_security_ratings": build_portfolio_security_ratings,
}


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    for name, builder in BUILDERS.items():
        path = FIXTURES_DIR / f"{name}.json"
        path.write_text(json.dumps(builder(), indent=2) + "\n")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

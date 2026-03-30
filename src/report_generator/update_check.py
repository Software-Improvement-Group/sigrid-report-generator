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

import configparser
import importlib.metadata
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import platformdirs
import requests

_REMOTE_SETUP_CFG_URL = (
    "https://raw.githubusercontent.com/Software-Improvement-Group/"
    "sigrid-report-generator/refs/heads/main/setup.cfg"
)
_CACHE_DIR = Path(platformdirs.user_cache_dir("report-generator"))
_CACHE_FILE = _CACHE_DIR / "update_check.json"
_CHECK_INTERVAL_DAYS = 7
_REQUEST_TIMEOUT_SECONDS = 3


def check_for_update() -> Optional[str]:
    if os.environ.get("SIGRID_REPORT_GENERATOR_NO_UPDATE_CHECK") == "1":
        return None

    current = _get_current_version()
    should_check, cached_version = _should_check()

    if not should_check:
        if cached_version and _is_newer(cached_version, current):
            return _notification(cached_version, current)
        return None

    latest = _fetch_latest_version()
    _write_cache(latest)

    if _is_newer(latest, current):
        return _notification(latest, current)
    return None


def _should_check() -> tuple[bool, Optional[str]]:
    cache = _read_cache()
    if cache is None:
        return True, None

    last_checked_raw = cache.get("last_checked")
    if not isinstance(last_checked_raw, str):
        return True, None

    try:
        last_checked = datetime.fromisoformat(last_checked_raw)
    except (TypeError, ValueError):
        # Malformed timestamp in cache; treat as cache miss.
        return True, None

    if last_checked.tzinfo is None:
        # Naive datetime cannot be safely compared to aware UTC now; treat as cache miss.
        return True, None
    age_days = (datetime.now(timezone.utc) - last_checked).days
    if age_days < _CHECK_INTERVAL_DAYS:
        return False, cache.get("latest_version")
    return True, None


def _read_cache() -> Optional[dict]:
    if not _CACHE_FILE.exists():
        return None
    try:
        data = json.loads(_CACHE_FILE.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "last_checked" not in data:
        return None
    return data


def _fetch_latest_version() -> str:
    response = requests.get(_REMOTE_SETUP_CFG_URL, timeout=_REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    parser = configparser.ConfigParser()
    parser.read_string(response.text)
    return parser.get("metadata", "version")


def _get_current_version() -> str:
    return importlib.metadata.version("report-generator")


def _is_newer(latest: str, current: str) -> bool:
    latest_parts = tuple(int(x) for x in latest.split("."))
    current_parts = tuple(int(x) for x in current.split("."))
    return latest_parts > current_parts


def _write_cache(latest_version: str) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(
        json.dumps(
            {
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "latest_version": latest_version,
            }
        )
    )


_REPO_URL = "https://github.com/Software-Improvement-Group/sigrid-report-generator"


def _notification(latest: str, current: str) -> str:
    return (
        f"A newer version of report-generator is available: {latest} (you have {current}).\n"
        f"Update with: pip3 install --upgrade git+{_REPO_URL}.git\n"
        f"See: {_REPO_URL}"
    )

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

import json
from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from report_generator.update_check import (
    _fetch_latest_version,
    _is_newer,
    _should_check,
    _write_cache,
    check_for_update,
)

SAMPLE_SETUP_CFG = """\
[metadata]
name = report-generator
version = 2.0.0
"""


@pytest.fixture(autouse=True)
def _isolate_cache(tmp_path, monkeypatch):
    import report_generator.update_check as mod

    monkeypatch.setattr(mod, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(mod, "_CACHE_FILE", tmp_path / "update_check.json")
    monkeypatch.delenv("SIGRID_REPORT_GENERATOR_NO_UPDATE_CHECK", raising=False)


class TestShouldCheck:
    def test_no_cache_file(self):
        assert _should_check() == (True, None)

    def test_corrupt_cache(self, tmp_path):
        (tmp_path / "update_check.json").write_text("not json")
        assert _should_check() == (True, None)

    @freeze_time("2026-03-26 12:00:00")
    def test_fresh_cache(self, tmp_path):
        (tmp_path / "update_check.json").write_text(
            json.dumps(
                {
                    "last_checked": (
                        datetime.now(timezone.utc) - timedelta(days=1)
                    ).isoformat(),
                    "latest_version": "1.5.0",
                }
            )
        )
        assert _should_check() == (False, "1.5.0")

    @freeze_time("2026-03-26 12:00:00")
    def test_stale_cache(self, tmp_path):
        (tmp_path / "update_check.json").write_text(
            json.dumps(
                {
                    "last_checked": (
                        datetime.now(timezone.utc) - timedelta(days=8)
                    ).isoformat(),
                    "latest_version": "1.5.0",
                }
            )
        )
        assert _should_check() == (True, None)


class TestIsNewer:
    def test_higher_version(self):
        assert _is_newer("1.1.0", "1.0.2") is True

    def test_same_version(self):
        assert _is_newer("1.0.2", "1.0.2") is False

    def test_lower_version(self):
        assert _is_newer("1.0.1", "1.0.2") is False

    def test_major_version_bump(self):
        assert _is_newer("2.0.0", "1.9.9") is True


class TestFetchLatestVersion:
    def test_parses_setup_cfg(self, mocker):
        mock_response = mocker.Mock()
        mock_response.text = SAMPLE_SETUP_CFG
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch(
            "report_generator.update_check.requests.get", return_value=mock_response
        )
        assert _fetch_latest_version() == "2.0.0"


class TestWriteCache:
    @freeze_time("2026-03-26 12:00:00")
    def test_writes_cache_file(self, tmp_path):
        _write_cache("1.5.0")
        data = json.loads((tmp_path / "update_check.json").read_text())
        assert data["latest_version"] == "1.5.0"
        assert "2026-03-26" in data["last_checked"]


class TestCheckForUpdate:
    def test_returns_message_when_newer(self, mocker):
        mocker.patch(
            "report_generator.update_check._get_current_version", return_value="1.0.0"
        )
        mock_response = mocker.Mock()
        mock_response.text = SAMPLE_SETUP_CFG
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch(
            "report_generator.update_check.requests.get", return_value=mock_response
        )

        result = check_for_update()
        assert result is not None
        assert "2.0.0" in result
        assert "1.0.0" in result
        assert "pip3 install --upgrade" in result

    def test_returns_none_when_current(self, mocker):
        mocker.patch(
            "report_generator.update_check._get_current_version", return_value="2.0.0"
        )
        mock_response = mocker.Mock()
        mock_response.text = SAMPLE_SETUP_CFG
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch(
            "report_generator.update_check.requests.get", return_value=mock_response
        )

        assert check_for_update() is None

    def test_raises_on_network_error(self, mocker):
        mocker.patch(
            "report_generator.update_check._get_current_version", return_value="1.0.0"
        )
        mocker.patch(
            "report_generator.update_check.requests.get",
            side_effect=ConnectionError("no network"),
        )
        with pytest.raises(ConnectionError):
            check_for_update()

    @freeze_time("2026-03-26 12:00:00")
    def test_uses_cache_within_window(self, tmp_path, mocker):
        (tmp_path / "update_check.json").write_text(
            json.dumps(
                {
                    "last_checked": (
                        datetime.now(timezone.utc) - timedelta(days=1)
                    ).isoformat(),
                    "latest_version": "2.0.0",
                }
            )
        )
        mocker.patch(
            "report_generator.update_check._get_current_version", return_value="1.0.0"
        )
        mock_get = mocker.patch("report_generator.update_check.requests.get")

        result = check_for_update()
        assert result is not None
        assert "2.0.0" in result
        mock_get.assert_not_called()

    def test_env_var_disables_check(self, monkeypatch, mocker):
        monkeypatch.setenv("SIGRID_REPORT_GENERATOR_NO_UPDATE_CHECK", "1")
        mock_get = mocker.patch("report_generator.update_check.requests.get")

        assert check_for_update() is None
        mock_get.assert_not_called()

    def test_writes_cache_after_fetch(self, tmp_path, mocker):
        mocker.patch(
            "report_generator.update_check._get_current_version", return_value="1.0.0"
        )
        mock_response = mocker.Mock()
        mock_response.text = SAMPLE_SETUP_CFG
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch(
            "report_generator.update_check.requests.get", return_value=mock_response
        )

        check_for_update()

        cache_file = tmp_path / "update_check.json"
        assert cache_file.exists()
        data = json.loads(cache_file.read_text())
        assert data["latest_version"] == "2.0.0"

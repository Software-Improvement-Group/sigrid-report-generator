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

import base64
import json
import logging
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

import report_generator.generator.context.config as config
import report_generator.generator.context.sigrid_api as sigrid_api


def _make_jwt(exp: int) -> str:
    """Build a fake JWT (unsigned) with the given ``exp`` claim for testing."""

    def _b64url(data: dict) -> str:
        raw = json.dumps(data).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    header = _b64url({"kid": "test-key", "alg": "RS256"})
    payload = _b64url({"sub": "test-user", "customer": "acme", "exp": exp})
    return f"{header}.{payload}.FAKE_SIGNATURE"


class TestSigridAPI:
    def test_short_sigrid_token_is_invalid(self):
        with pytest.raises(Exception) as excinfo:
            sigrid_api._test_sigrid_token("eyo")
        assert str(excinfo.value).startswith("Invalid Sigrid token")

    def test_random_string_is_invalid_sigrid_token(self):
        with pytest.raises(Exception) as excinfo:
            sigrid_api._test_sigrid_token("sfkskfiurkfshiuwhfibvcgi43hf2o3h893hg34")
        assert str(excinfo.value).startswith("Invalid Sigrid token")

    def test_valid_sigrid_token_is_valid(self):
        try:
            sigrid_api._test_sigrid_token("eyKskfiurkfshiuwhfibvcgi43hf2o3h893hg34")
        except ValueError:
            pytest.fail("This token was expected to be valid")

    def test_expired_sigrid_token_is_invalid(self):
        expired_token = _make_jwt(exp=int(time.time()) - 3600)
        with pytest.raises(ValueError) as excinfo:
            sigrid_api._test_sigrid_token(expired_token)
        assert str(excinfo.value).startswith("Expired Sigrid token")

    def test_unexpired_sigrid_token_is_valid(self):
        unexpired_token = _make_jwt(exp=int(time.time()) + 3600)
        try:
            sigrid_api._test_sigrid_token(unexpired_token)
        except ValueError:
            pytest.fail("This token was expected to be valid")

    def test_token_without_exp_claim_is_not_rejected_as_expired(self):
        # Tokens that are not decodable JWTs (no exp claim) fall back to the
        # format-only check and must remain valid.
        try:
            sigrid_api._test_sigrid_token("eyKskfiurkfshiuwhfibvcgi43hf2o3h893hg34")
        except ValueError:
            pytest.fail("A token without a decodable exp claim should be valid")

    def test_set_context_multiple_times_preserves_previous_values(self):
        sigrid_api.reset_context()

        custom_base_url = "http://localhost:8080"
        sigrid_api.set_context(base_url=custom_base_url)
        assert custom_base_url in config._rest_url

        sigrid_api.set_context(customer="test-customer")
        assert config._customer == "test-customer"
        assert custom_base_url in config._rest_url, (
            "existing context (base_url) should be preserved"
        )

        sigrid_api.reset_context()

    def test_reset_context_not_specified_resets_all_values(self):
        sigrid_api.reset_context()

        sigrid_api.set_context(customer="test-customer", system="test-system")
        assert config._customer == "test-customer"
        assert config._system == "test-system"

        sigrid_api.reset_context()
        assert config._customer is None
        assert config._system is None

    def test_get_period_raises_exception_when_not_set(self):
        sigrid_api.reset_context()

        with pytest.raises(Exception) as excinfo:
            sigrid_api.get_period()
        assert "Reporting period not defined" in str(excinfo.value)

    def test_get_period_returns_set_period(self):
        sigrid_api.reset_context()
        sigrid_api.set_context(period=("2024-01-01", "2024-12-31"))

        start, end = sigrid_api.get_period()

        assert start == "2024-01-01"
        assert end == "2024-12-31"

        sigrid_api.reset_context()

    def test_check_context_raises_error_when_bearer_token_missing(self):
        sigrid_api.reset_context()
        config._bearer_token = None
        config._customer = "test"
        config._rest_url = "http://test"

        with pytest.raises(ValueError) as excinfo:
            sigrid_api._check_context()
        assert "_bearer_token" in str(excinfo.value)

        sigrid_api.reset_context()

    def test_check_context_raises_error_when_customer_missing(self):
        sigrid_api.reset_context()
        config._bearer_token = "test-token"
        config._customer = None
        config._rest_url = "http://test"

        with pytest.raises(ValueError) as excinfo:
            sigrid_api._check_context()
        assert "_customer" in str(excinfo.value)

        sigrid_api.reset_context()

    def test_check_context_raises_error_when_rest_url_missing(self):
        sigrid_api.reset_context()
        config._bearer_token = "test-token"
        config._customer = "test"
        config._rest_url = None

        with pytest.raises(ValueError) as excinfo:
            sigrid_api._check_context()
        assert "_rest_url" in str(excinfo.value)

        sigrid_api.reset_context()

    def test_check_context_passes_when_all_values_set(self):
        sigrid_api.reset_context()
        config._bearer_token = "test-token"
        config._customer = "test"
        config._rest_url = "http://test"

        # Should not raise
        sigrid_api._check_context()

        sigrid_api.reset_context()

    def test_sigrid_access_denied_message_contains_customer_and_url(self):
        exc = sigrid_api.SigridAccessDeniedError(
            "https://sigrid-says.com/rest/...", "my-customer", "my-system"
        )
        msg = str(exc)
        assert "my-customer" in msg
        assert "https://sigrid-says.com/my-customer/my-system" in msg

    def test_sigrid_access_denied_message_with_no_system(self):
        exc = sigrid_api.SigridAccessDeniedError(
            "https://sigrid-says.com/rest/...", "my-customer", None
        )
        msg = str(exc)
        assert "my-customer" in msg
        assert "(none)" in msg
        assert "https://sigrid-says.com/my-customer" in msg

    def test_request_raises_sigrid_access_denied_on_403(self):
        sigrid_api.reset_context()
        config._bearer_token = "eyTesttoken12345678"
        config._customer = "my-customer"
        config._system = "my-system"

        mock_response = MagicMock()
        mock_response.status_code = 403
        http_error = requests.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error

        with patch("requests.request", return_value=mock_response):
            sigrid_api._request.cache_clear()
            with pytest.raises(sigrid_api.SigridAccessDeniedError) as excinfo:
                sigrid_api._request("https://sigrid-says.com/rest/some-endpoint")
            assert "my-customer" in str(excinfo.value)

        sigrid_api._request.cache_clear()
        sigrid_api.reset_context()

    def test_request_returns_none_and_logs_warning_on_204(self, caplog):
        sigrid_api.reset_context()
        config._bearer_token = "eyTesttoken12345678"
        config._customer = "my-customer"
        config._system = "my-system"

        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status.return_value = None

        with patch("requests.request", return_value=mock_response):
            sigrid_api._request.cache_clear()
            with caplog.at_level(logging.WARNING):
                result = sigrid_api._request(
                    "https://sigrid-says.com/rest/some-204-endpoint"
                )
            assert result is None
            assert "204" in caplog.text

        sigrid_api._request.cache_clear()
        sigrid_api.reset_context()

    def test_request_returns_none_on_non_403_http_error(self):
        sigrid_api.reset_context()
        config._bearer_token = "eyTesttoken12345678"
        config._customer = "my-customer"
        config._system = "my-system"

        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = requests.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error

        with patch("requests.request", return_value=mock_response):
            sigrid_api._request.cache_clear()
            result = sigrid_api._request(
                "https://sigrid-says.com/rest/some-other-endpoint"
            )
            assert result is None

        sigrid_api._request.cache_clear()
        sigrid_api.reset_context()

    def _patch_http_status(self, status_code):
        """Return a mocked requests response that raises HTTPError with the given status."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            response=mock_response
        )
        return mock_response

    def test_request_raises_token_invalid_on_401(self):
        # A 401 means the token itself is rejected (mistyped, expired, or revoked).
        sigrid_api.reset_context()
        config._bearer_token = "eyTesttoken12345678"
        config._customer = "my-customer"

        with patch("requests.request", return_value=self._patch_http_status(401)):
            sigrid_api._request.cache_clear()
            with pytest.raises(sigrid_api.SigridTokenInvalidError):
                sigrid_api._request("https://sigrid-says.com/rest/some-endpoint")

        sigrid_api._request.cache_clear()
        sigrid_api.reset_context()

    def test_token_with_dropped_character_in_payload_is_rejected(self):
        # A character dropped while copying corrupts the JWT payload; this is
        # caught offline before any request is made.
        header, payload, signature = _make_jwt(exp=int(time.time()) + 3600).split(".")
        corrupted = f"{header}.{payload[:-1]}.{signature}"

        with pytest.raises(ValueError) as excinfo:
            sigrid_api._test_sigrid_token(corrupted)
        assert "Malformed Sigrid token" in str(excinfo.value)

    def test_intact_three_segment_jwt_passes_structure_check(self):
        # Must not raise: an intact JWT passes the structural check.
        sigrid_api._test_sigrid_token(_make_jwt(exp=int(time.time()) + 3600))

    def test_optional_endpoint_403_is_downgraded_to_request_failure(self, caplog):
        # An unlicensed feature (e.g. security or OSH) returns 403; it must not
        # abort the whole report, only skip its own placeholder.
        sigrid_api.reset_context()
        config._bearer_token = "eyTesttoken12345678"
        config._customer = "my-customer"
        config._system = "my-system"

        with patch("requests.request", return_value=self._patch_http_status(403)):
            sigrid_api._request.cache_clear()
            with caplog.at_level(logging.DEBUG):
                with pytest.raises(sigrid_api.SigridAPIRequestFailedError):
                    sigrid_api.get_security_findings("my-system")
            assert "get_security_findings" in caplog.text

        sigrid_api._request.cache_clear()
        sigrid_api.reset_context()

    def test_critical_endpoint_403_raises_access_denied(self):
        # A core endpoint (maintainability) returning 403 means the token cannot
        # see this customer at all, which is fatal.
        sigrid_api.reset_context()
        config._bearer_token = "eyTesttoken12345678"
        config._customer = "my-customer"

        with patch("requests.request", return_value=self._patch_http_status(403)):
            sigrid_api._request.cache_clear()
            with pytest.raises(sigrid_api.SigridAccessDeniedError):
                sigrid_api.get_portfolio_maintainability()

        sigrid_api._request.cache_clear()
        sigrid_api.reset_context()

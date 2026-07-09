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
import time
from typing import Optional

DEFAULT_BASE_URL = "https://sigrid-says.com"
BASE_ANALYSIS_RESULTS_ENDPOINT = "analysis-results/api/v1"

_bearer_token: Optional[str] = None
_customer: Optional[str] = None
_system: Optional[str] = None
_period: Optional[tuple[str, str]] = None
_rest_url: str = f"{DEFAULT_BASE_URL}/rest"


def _decode_jwt_segment(segment: str) -> dict:
    """Decode one base64url-encoded JWT segment into its JSON object.

    Raises ValueError if the segment is not intact base64url-encoded JSON. A
    base64url segment length is never 1 modulo 4, so that indicates a dropped or
    added character; ``urlsafe_b64decode`` and ``json.loads`` both raise
    subclasses of ValueError on other corruption."""
    if len(segment) % 4 == 1:
        raise ValueError("Invalid base64url segment length.")
    # Base64URL segments in a JWT are unpadded; restore padding before decoding.
    padding = "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment + padding))


def _validate_jwt_structure(token: str) -> None:
    """Verify an intact JWT when the token has the three-segment JWT shape.

    A character dropped while copying corrupts the base64url encoding or the JSON
    of the header/payload, which this detects offline. Tokens that are not
    three-segment JWTs are left for the server to validate; the signature can only
    be verified server-side, so a corrupt signature is only caught at request time
    (HTTP 401)."""
    parts = token.split(".")
    if len(parts) != 3:
        return

    header, payload, signature = parts
    try:
        _decode_jwt_segment(header)
        _decode_jwt_segment(payload)
        if len(signature) % 4 == 1:
            raise ValueError("Invalid base64url signature length.")
    except ValueError as e:
        raise ValueError(
            "Malformed Sigrid token. The token appears corrupted (a character may have been dropped when copying). Copy the full token from sigrid-says.com."
        ) from e


def _token_expiry(token: str) -> Optional[int]:
    """Return the JWT ``exp`` claim (seconds since epoch), or None if the token
    cannot be decoded as a JWT with an integer ``exp`` claim."""
    parts = token.split(".")
    if len(parts) != 3:
        return None

    try:
        payload = _decode_jwt_segment(parts[1])
    except ValueError:
        return None

    exp = payload.get("exp")
    return exp if isinstance(exp, int) else None


def _test_sigrid_token(token: str) -> None:
    if len(token) < 10 or token[0:2] != "ey":
        raise ValueError(
            "Invalid Sigrid token. A token is always longer than 10 characters and starts with 'ey'. You can obtain a token from sigrid-says.com."
        )

    _validate_jwt_structure(token)

    expiry = _token_expiry(token)
    if expiry is not None and expiry < time.time():
        raise ValueError(
            "Expired Sigrid token. This token's expiration date has passed. You can obtain a new token from sigrid-says.com."
        )


def set_context(
    bearer_token: Optional[str] = None,
    customer: Optional[str] = None,
    system: Optional[str] = None,
    period: Optional[tuple[str, str]] = None,
    base_url: Optional[str] = None,
) -> None:
    """Set the context values. Only updates provided values. None values will be ignored (use reset_context instead)."""
    global _bearer_token, _customer, _system, _period, _rest_url

    if bearer_token is not None:
        _test_sigrid_token(bearer_token)
        _bearer_token = bearer_token

    if customer is not None:
        _customer = customer

    if system is not None:
        _system = system

    if period is not None:
        _period = period

    if base_url is not None:
        _rest_url = f"{base_url.rstrip('/')}/rest"


def reset_context() -> None:
    """Reset all context values to their defaults."""
    global _bearer_token, _customer, _system, _period, _rest_url
    _bearer_token = None
    _customer = None
    _system = None
    _period = None
    _rest_url = f"{DEFAULT_BASE_URL}/rest"


def get_customer() -> str:
    if _customer is None:
        raise ValueError("Customer not set. Call set_context() first.")
    return _customer


def get_period() -> tuple[str, str]:
    if _period is None:
        raise Exception("Reporting period not defined")
    return _period


def _check_context() -> None:
    missing_values = []

    if _bearer_token is None:
        missing_values.append("_bearer_token")
    if _customer is None:
        missing_values.append("_customer")
    if _rest_url is None:
        missing_values.append("_rest_url")

    if missing_values:
        raise ValueError(
            f"Context must be set using set_context() before making API calls. "
            f"The following values are not set: {', '.join(missing_values)}"
        )

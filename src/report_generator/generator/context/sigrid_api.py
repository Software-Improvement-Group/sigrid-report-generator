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

import logging
from functools import cache, wraps
from typing import Optional

import requests

from report_generator.generator.context import config
from report_generator.generator.context.config import (
    BASE_ANALYSIS_RESULTS_ENDPOINT,
    DEFAULT_BASE_URL,  # noqa: F401
    _check_context,
    _test_sigrid_token,  # noqa: F401
    get_period,
    reset_context,  # noqa: F401
    set_context,  # noqa: F401
)
from report_generator.generator.utils.constants import MaintMetric
from report_generator.generator.utils.time_series import Period


class SigridAPIRequestFailedError(Exception):
    def __init__(self, function_name, message="API request failed"):
        self.function_name = function_name
        self.message = f"{message} in function '{function_name}'"
        super().__init__(self.message)


class SigridAccessDeniedError(Exception):
    def __init__(
        self,
        url: str,
        customer: str,
        system: Optional[str],
        api_message: Optional[str] = None,
    ):
        self.api_message = api_message
        system_part = f"/{system}" if system else ""
        sigrid_url = f"https://sigrid-says.com/{customer}{system_part}"
        message = "\n".join(
            [
                f"Access denied (403) calling Sigrid API: {url}",
                f"  - Customer used : '{customer}'",
                f"  - System used   : '{system or '(none)'}'",
                f"  - Verify the names are correct: {sigrid_url}",
                "  - Tokens are customer-specific, so ensure your token has access to this customer.",
            ]
        )
        super().__init__(message)


class SigridTokenInvalidError(Exception):
    """Raised when the Sigrid API rejects the token itself (HTTP 401).

    Unlike an access-denied error, this means the token is not accepted at all:
    it is malformed, expired, or has been revoked. No request will succeed, so
    report generation cannot continue."""

    def __init__(self):
        message = "\n".join(
            [
                "Invalid Sigrid token (401 Unauthorized).",
                "  - The token was rejected. It may be mistyped, expired, or revoked.",
                "  - Obtain a new token from sigrid-says.com.",
            ]
        )
        super().__init__(message)


@cache
def _request(url):
    logging.debug(f"Sending request to {url}")
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {config._bearer_token}",
    }
    try:
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        return _handle_http_error(e, url)
    except requests.RequestException as e:
        logging.error(
            f"Failed to make request to Sigrid API endpoint {url}. Error: {e}"
        )
        return None

    if response.status_code == 204:
        logging.warning(
            f"No data returned for {url} (HTTP 204). "
            f"The system may not exist or may not have been analysed yet."
        )
        return None
    return response.json()


def _extract_api_message(response) -> Optional[str]:
    """Return the ``message`` field from a JSON error body, if present. A 403 may carry
    a message such as "The requested endpoint needs at least one of the following
    license(s): security", but the body can also be empty or non-JSON."""
    try:
        message = response.json().get("message")
    except (ValueError, AttributeError):
        return None
    return message if isinstance(message, str) else None


def _handle_http_error(error: requests.HTTPError, url: str):
    """Translate an HTTP error into the appropriate outcome: a fatal token error
    (401), a fatal access-denied error (403), or a logged failure that the caller
    turns into a skipped request (any other status)."""
    status_code = error.response.status_code
    if status_code == 401:
        raise SigridTokenInvalidError() from None
    if status_code == 403:
        raise SigridAccessDeniedError(
            url,
            config._customer,
            config._system,
            api_message=_extract_api_message(error.response),
        ) from None
    logging.error(
        f"Failed to make request to Sigrid API endpoint {url}. Error: {error}"
    )
    return None


def _sigrid_api_request(with_system=False, critical=False):
    """
    Decorator to create functions that call Sigrid API requests, optionally with a system parameter.
    If with_system is set to True, the decorator will first look for the system parameter passed to the function when called.
    If the system parameter is not provided in the function call, it will use the global system value set by set_context.

    When critical is False (the default), the endpoint is optional (e.g. security or open source
    health, which not every customer is licensed for): an access-denied response (HTTP 403) is logged
    and downgraded to a regular request failure so the placeholder is skipped and the rest of the
    report is still produced. When critical is True, a 403 aborts report generation, because a core
    endpoint such as maintainability that returns 403 means the token cannot see this customer at all.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = _call_with_system(func, with_system, args, kwargs)
            except SigridAccessDeniedError as exc:
                if critical:
                    raise
                detail = f" API message: {exc.api_message}" if exc.api_message else ""
                logging.debug(
                    f"Access denied (403) for optional endpoint '{func.__name__}'; "
                    f"skipping it (the feature may not be available for this customer).{detail}"
                )
                raise SigridAPIRequestFailedError(func.__name__) from None

            if result is None:
                raise SigridAPIRequestFailedError(func.__name__)

            return result

        return wrapper

    return decorator


def _call_with_system(func, with_system, args, kwargs):
    if not with_system:
        return func(*args, **kwargs)

    system = args[0] if args else kwargs.pop("system", None) or config._system
    if system is None:
        raise ValueError("System not provided and global _system is not set.")
    return func(system, *args[1:], **kwargs)


def _make_request(endpoint):
    _check_context()
    url = f"{config._rest_url}/{endpoint}"
    return _request(url)


@_sigrid_api_request(critical=True)
def get_portfolio_metadata(hide_deactivated: bool = True):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/system-metadata/{config._customer}?hideDeactivatedSystems={str(hide_deactivated).lower()}"
    return _make_request(endpoint)


@_sigrid_api_request(critical=True)
def get_portfolio_maintainability():
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/maintainability/{config._customer}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_objectives_evaluation(period: Period):
    start = period.start.strftime("%Y-%m-%d")
    end = period.end.strftime("%Y-%m-%d")
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/objectives-evaluation/{config._customer}?startDate={start}&endDate={end}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True, critical=True)
def get_maintainability_ratings(system, include_tech_stats: bool = True):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/maintainability/{config._customer}/{system}?technologyStats={str(include_tech_stats).lower()}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_maintainability_ratings_components(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/maintainability/{config._customer}/{system}/components"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_capabilities(system):
    endpoint = f"analysis-results/capabilities/{config._customer}/{system}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True, critical=True)
def get_system_metadata(system):
    endpoint = (
        f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/system-metadata/{config._customer}/{system}"
    )
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_osh_findings(system, is_vulnerable=False):
    vulnerable = "true" if is_vulnerable else "false"
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/osh-findings/{config._customer}/{system}?vulnerable={vulnerable}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_osh_findings(is_vulnerable=False):
    vulnerable = "true" if is_vulnerable else "false"
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/osh-findings/{config._customer}?vulnerable={vulnerable}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_security_findings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/security-findings/{config._customer}/{system}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_reliability_findings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/reliability-findings/{config._customer}/{system}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_security_dashboard_findings():
    argument = f"&endDate={config._period[1]}" if config._period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/finding-ratios/{config._customer}?feature=security{argument}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_reliability_dashboard_findings():
    argument = f"&endDate={config._period[1]}" if config._period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/finding-ratios/{config._customer}?feature=reliability{argument}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_security_resolution_time_findings():
    argument = f"&endDate={config._period[1]}" if config._period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/resolution-times/{config._customer}?feature=security{argument}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_reliability_resolution_time_findings():
    argument = f"&endDate={config._period[1]}" if config._period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/resolution-times/{config._customer}?feature=reliability{argument}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_security_ratings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/model-ratings/{config._customer}/{system}?feature=SECURITY"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_security_ratings():
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/model-ratings/{config._customer}?feature=SECURITY"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_reliability_ratings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/model-ratings/{config._customer}/{system}?feature=RELIABILITY"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_reliability_ratings():
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/model-ratings/{config._customer}?feature=RELIABILITY"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_architecture_findings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/architecture-quality/{config._customer}/{system}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_architecture_findings():
    endpoint = (
        f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/architecture-quality/{config._customer}"
    )
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_architecture_graph(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/architecture-quality/{config._customer}/{system}/raw"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_maintainability_delta_quality(system, delta_type="NEW_AND_CHANGED_CODE"):
    start, end = get_period()
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/delta-quality/{config._customer}/{system}?type={delta_type}&startDate={start}&endDate={end}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_maintainability_refactoring_candidates(
    system,
    system_property: MaintMetric,
    technology: Optional[str] = None,
    count: Optional[int] = None,
):
    property_name = system_property.to_json_name()

    query_params = []
    if technology is not None:
        query_params.append(f"technology={technology}")
    if count is not None:
        query_params.append(f"count={count}")
    query_string = f"?{'&'.join(query_params)}" if query_params else ""

    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/refactoring-candidates/{config._customer}/{system}/{property_name}{query_string}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_users():
    endpoint = f"auth/api/user-management/{config._customer}/users"
    return _make_request(endpoint)

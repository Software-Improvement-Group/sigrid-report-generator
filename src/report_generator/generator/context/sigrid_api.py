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

from report_generator.generator.utils.constants import MaintMetric
from report_generator.generator.utils.time_series import Period

DEFAULT_BASE_URL = "https://sigrid-says.com"
BASE_ANALYSIS_RESULTS_ENDPOINT = "analysis-results/api/v1"

_bearer_token: Optional[str] = None
_customer: Optional[str] = None
_system: Optional[str] = None
_period: Optional[tuple[str, str]] = None
_rest_url: str = f"{DEFAULT_BASE_URL}/rest"


class SigridAPIRequestFailedError(Exception):
    def __init__(self, function_name, message="API request failed"):
        self.function_name = function_name
        self.message = f"{message} in function '{function_name}'"
        super().__init__(self.message)


class SigridAccessDeniedError(Exception):
    def __init__(self, url: str, customer: str, system: Optional[str]):
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


def _test_sigrid_token(token):
    if len(token) < 10 or token[0:2] != "ey":
        raise ValueError(
            "Invalid Sigrid token. A token is always longer than 10 characters and starts with 'ey'. You can obtain a token from sigrid-says.com. Note that tokens are customer-specific."
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


def reset_context(
    reset_bearer_token: Optional[bool] = None,
    reset_customer: Optional[bool] = None,
    reset_system: Optional[bool] = None,
    reset_period: Optional[bool] = None,
    reset_base_url: Optional[bool] = None,
) -> None:
    """Reset context values. If no parameters are provided, resets all values."""
    global _bearer_token, _customer, _system, _period, _rest_url

    reset_all = all(
        param is None
        for param in [
            reset_bearer_token,
            reset_customer,
            reset_system,
            reset_period,
            reset_base_url,
        ]
    )

    if reset_all or reset_bearer_token:
        _bearer_token = None
    if reset_all or reset_customer:
        _customer = None
    if reset_all or reset_system:
        _system = None
    if reset_all or reset_period:
        _period = None
    if reset_all or reset_base_url:
        _rest_url = f"{DEFAULT_BASE_URL}/rest"


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
            f"Context must be set using sigrid_api.set_context() before making API calls. "
            f"The following values are not set: {', '.join(missing_values)}"
        )


@cache
def _request(url):
    logging.debug(f"Sending request to {url}")
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {_bearer_token}",
    }
    try:
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()
        if response.status_code == 204:
            logging.warning(
                f"No data returned for {url} (HTTP 204). "
                f"The system may not exist or may not have been analysed yet."
            )
            return None
        return response.json()
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            raise SigridAccessDeniedError(url, _customer, _system) from None
        logging.error(
            f"Failed to make request to Sigrid API endpoint {url}. Error: {e}"
        )
        return None
    except requests.RequestException as e:
        logging.error(
            f"Failed to make request to Sigrid API endpoint {url}. Error: {e}"
        )
        return None


def _sigrid_api_request(with_system=False):
    """
    Decorator to create functions that call Sigrid API requests, optionally with a system parameter.
    If with_system is set to True, the decorator will first look for the system parameter passed to the function when called.
    If the system parameter is not provided in the function call, it will use the global system value set by set_context.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if with_system:
                system = args[0] if args else kwargs.pop("system", None) or _system
                if system is None:
                    raise ValueError(
                        "System not provided and global _system is not set."
                    )
                result = func(system, *args[1:], **kwargs)
            else:
                result = func(*args, **kwargs)

            if result is None:
                raise SigridAPIRequestFailedError(func.__name__)

            return result

        return wrapper

    return decorator


def _make_request(endpoint):
    _check_context()
    url = f"{_rest_url}/{endpoint}"
    return _request(url)


@_sigrid_api_request()
def get_portfolio_metadata():
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/system-metadata/{_customer}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_maintainability():
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/maintainability/{_customer}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_objectives_evaluation(period: Period):
    start = period.start.strftime("%Y-%m-%d")
    end = period.end.strftime("%Y-%m-%d")
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/objectives-evaluation/{_customer}?startDate={start}&endDate={end}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_maintainability_ratings(system, include_tech_stats: bool = True):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/maintainability/{_customer}/{system}?technologyStats={str(include_tech_stats).lower()}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_maintainability_ratings_components(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/maintainability/{_customer}/{system}/components"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_capabilities(system):
    endpoint = f"analysis-results/capabilities/{_customer}/{system}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_system_metadata(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/system-metadata/{_customer}/{system}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_osh_findings(system, is_vulnerable=False):
    vulnerable = "true" if is_vulnerable else "false"
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/osh-findings/{_customer}/{system}?vulnerable={vulnerable}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_osh_findings(is_vulnerable=False):
    vulnerable = "true" if is_vulnerable else "false"
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/osh-findings/{_customer}?vulnerable={vulnerable}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_security_findings(system):
    endpoint = (
        f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/security-findings/{_customer}/{system}"
    )
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_security_findings():
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/security-findings/{_customer}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_security_dashboard_findings(system):
    argument = f"&endDate={_period[1]}" if _period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/finding-ratios/{_customer}/{system}?feature=security{argument}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_security_dashboard_findings():
    argument = f"&endDate={_period[1]}" if _period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/finding-ratios/{_customer}?feature=security{argument}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_security_resolution_time_findings(system):
    argument = f"&endDate={_period[1]}" if _period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/resolution-times/{_customer}/{system}?feature=security{argument}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_security_resolution_time_findings():
    argument = f"&endDate={_period[1]}" if _period else ""
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/resolution-times/{_customer}?feature=security{argument}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_security_ratings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/model-ratings/{_customer}/{system}?feature=SECURITY"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_security_ratings():
    endpoint = (
        f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/model-ratings/{_customer}?feature=SECURITY"
    )
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_architecture_findings(system):
    endpoint = (
        f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/architecture-quality/{_customer}/{system}"
    )
    return _make_request(endpoint)


@_sigrid_api_request()
def get_portfolio_architecture_findings():
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/architecture-quality/{_customer}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_architecture_graph(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/architecture-quality/{_customer}/{system}/raw"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_maintainability_delta_quality(system, delta_type="NEW_AND_CHANGED_CODE"):
    start, end = get_period()
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/delta-quality/{_customer}/{system}?type={delta_type}&startDate={start}&endDate={end}"
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

    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/refactoring-candidates/{_customer}/{system}/{property_name}{query_string}"
    return _make_request(endpoint)


@_sigrid_api_request()
def get_users():
    endpoint = f"auth/api/user-management/{_customer}/users"
    return _make_request(endpoint)

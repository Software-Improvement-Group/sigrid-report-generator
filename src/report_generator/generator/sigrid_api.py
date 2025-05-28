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

DEFAULT_BASE_URL = "https://sigrid-says.com"
BASE_ANALYSIS_RESULTS_ENDPOINT = "analysis-results/api/v1"

_bearer_token: Optional[str] = None
_customer: Optional[str] = None
_system: Optional[str] = None
_rest_url: Optional[str] = None


class SigridAPIRequestFailed(Exception):
    def __init__(self, function_name, message="API request failed"):
        self.function_name = function_name
        self.message = f"{message} in function '{function_name}'"
        super().__init__(self.message)


def _test_sigrid_token(token):
    if len(token) < 10 or token[0:2] != "ey":
        raise ValueError(
            "Invalid Sigrid token. A token is always longer than 10 characters and starts with 'ey'. You can obtain a token from sigrid-says.com. Note that tokens are customer-specific.")


def set_context(
        bearer_token: Optional[str] = None,
        customer: Optional[str] = None,
        system: Optional[str] = None,
        base_url: Optional[str] = None
) -> None:
    """Set the context values. Only updates provided values. Sets base_url to default if not provided."""
    global _bearer_token, _customer, _system, _rest_url

    if bearer_token is not None:
        _test_sigrid_token(bearer_token)
        _bearer_token = bearer_token

    if customer is not None:
        _customer = customer

    if system is not None:
        _system = system

    _rest_url = f"{base_url or DEFAULT_BASE_URL.rstrip('/')}/rest"


def reset_context(
        reset_bearer_token: bool = False,
        reset_customer: bool = False,
        reset_system: bool = False,
        reset_base_url: bool = False
) -> None:
    global _bearer_token, _customer, _system, _rest_url

    if reset_bearer_token:
        _bearer_token = None

    if reset_customer:
        _customer = None

    if reset_system:
        _system = None

    if reset_base_url:
        _rest_url = f"{DEFAULT_BASE_URL.rstrip('/')}/rest"


def _check_context():
    missing_values = []

    if _bearer_token is None:
        missing_values.append('_bearer_token')
    if _customer is None:
        missing_values.append('_customer')
    if _rest_url is None:
        missing_values.append('_rest_url')

    if missing_values:
        raise ValueError(f"Context must be set using sigrid_api.set_context() before making API calls. "
                         f"The following values are not set: {', '.join(missing_values)}")


@cache
def _request(url):
    logging.debug(f"Sending request to {url}")
    headers = {
        "Content-type" : "application/json",
        "Authorization": f"Bearer {_bearer_token}"
    }
    try:
        response = requests.request('GET', url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to make request to Sigrid API endpoint {url}. Error: {e}")
        return None


def _sigrid_api_request(with_system=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if with_system:
                system = kwargs.pop('system', None)
                if system is None:
                    if _system is None:
                        raise ValueError("System not provided and global _system is not set.")
                    system = _system
                result = func(system, *args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if result is None:
                raise SigridAPIRequestFailed(func.__name__)

            return result

        return wrapper

    return decorator


def _make_request(endpoint, **kwargs):
    _check_context()
    url = f"{_rest_url}/{endpoint}"
    return _request(url, **kwargs)


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


@_sigrid_api_request(with_system=True)
def get_security_findings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/security-findings/{_customer}/{system}"
    return _make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_architecture_findings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_ENDPOINT}/architecture-quality/{_customer}/{system}"
    return _make_request(endpoint)

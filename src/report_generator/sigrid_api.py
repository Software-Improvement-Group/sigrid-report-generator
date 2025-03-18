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
from functools import cache
from typing import Optional

import requests

BASE_URL = "https://sigrid-says.com/rest"
BASE_ANALYSIS_RESULTS_URL = "analysis-results/api/v1"

_bearer_token: Optional[str] = None
_customer: Optional[str] = None
_system: Optional[str] = None


class SigridAPIRequestFailed(Exception):
    def __init__(self, function_name, message="API request failed"):
        self.function_name = function_name
        self.message = f"{message} in function '{function_name}'"
        super().__init__(self.message)


def _test_sigrid_token(token):
    if len(token) < 10 or token[0:2] != "ey":
        raise ValueError(
            "Invalid Sigrid token. A token is always longer than 10 characters and starts with 'ey'. You can obtain a token from sigrid-says.com. Note that tokens are customer-specific.")


def set_context(bearer_token: str, customer: str, system: str = None):
    _test_sigrid_token(bearer_token)

    global _bearer_token, _customer, _system
    _bearer_token = bearer_token
    _customer = customer
    _system = system


def _check_context():
    if _bearer_token is None or _customer is None:
        raise ValueError("Context must be set using sigrid_api.set_context() before making API calls.")


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


from functools import wraps


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


def make_request(endpoint, **kwargs):
    _check_context()
    url = f"{BASE_URL}/{endpoint}"
    return _request(url, **kwargs)


@_sigrid_api_request(with_system=True)
def get_maintainability_ratings(system, include_tech_stats: bool = True):
    endpoint = f"{BASE_ANALYSIS_RESULTS_URL}/maintainability/{_customer}/{system}?technologyStats={str(include_tech_stats).lower()}"
    return make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_maintainability_ratings_components(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_URL}/maintainability/{_customer}/{system}/components"
    return make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_capabilities(system):
    endpoint = f"analysis-results/capabilities/{_customer}/{system}"
    return make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_metadata(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_URL}/system-metadata/{_customer}"
    return make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_osh_findings(system, is_vulnerable=False):
    vulnerable = "true" if is_vulnerable else "false"
    endpoint = f"{BASE_ANALYSIS_RESULTS_URL}/osh-findings/{_customer}/{system}?vulnerable={vulnerable}"
    return make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_security_findings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_URL}/security-findings/{_customer}/{system}"
    return make_request(endpoint)


@_sigrid_api_request(with_system=True)
def get_architecture_findings(system):
    endpoint = f"{BASE_ANALYSIS_RESULTS_URL}/architecture-quality/{_customer}/{system}"
    return make_request(endpoint)


__all__ = [
    'set_context',
    'get_maintainability_ratings',
    'get_maintainability_ratings_components',
    'get_capabilities',
    'get_metadata',
    'get_osh_findings',
    'get_security_findings',
    'get_architecture_findings',
    'SigridAPIRequestFailed'
]

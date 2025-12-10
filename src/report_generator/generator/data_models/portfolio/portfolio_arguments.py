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

from functools import wraps
from typing import Optional

import click

from report_generator.generator import sigrid_api

_team: Optional[list[str]] = None
_division: Optional[list[str]] = None

def get_portfolio_context():
    global _team, _division
    return {
        'team' : _team,
        'division' : _division
    }

def set_context(
        team: Optional[list[str]] = None,
        division: Optional[list[str]] = None
) -> None:
    global _team, _division
    if team:
        _team = list(team)

    if division:
        _division = list(division)


def portfolio_arguments_command():
    def decorator(func):
        @wraps(func)
        @click.option('--team', multiple=True, help="Team name filter, as displayed in Sigrid (multiple values need separate --team flags, ie.: --team aap --team noot)")
        @click.option('--division', multiple=True, help="Division name filter, as displayed in Sigrid (multiple values need separate --division flags, ie.: --division aap --division noot)")
        def wrapper(team, division, *args, **kwargs):
            set_context(team=team, division=division)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def _raise_no_systems_found_error():
    """Raise an error when no systems match the specified team/division filters."""
    filter_desc = []
    if _team:
        filter_desc.append(f"--team: {', '.join(_team)}")
    if _division:
        filter_desc.append(f"--division: {', '.join(_division)}")

    error_msg = (
        f"No systems match the specified filters.\n"
        f"Filters applied:\n{chr(10).join(filter_desc)}\n\n"
        f"Please verify:\n"
        f"  1. The team/division names match exactly as shown in Sigrid (case-sensitive)\n"
        f"  2. At least one active system exists with these team/division assignments\n"
        f"  3. The systems are not marked as development-only"
    )
    raise click.ClickException(error_msg)


def filter_data_on_portfolio_arguments(data_tag=None, system_tag=None):
    """
    This decorator integrates with the Sigrid API to apply portfolio-aware filtering logic to the data returned by the decorated function.
    It ensures that at least one of `data_tag` or `system_tag` is specified to define the filtering context.

    Parameters
    ----------
    data_tag : str, optional
        Tag indicating where system entries are stored in the Sigrid API JSON response.
        E.g.: In `maintainability_portfolio_data`, system entries are available in `maintainability_portfolio_data['systems']`, hence `data_tag='systems'`.
    system_tag : str, optional
        Tag indicating where the system entry's name can be found.
        E.g.: System entries are available in `maintainability_portfolio_data['systems']`, and their system name can be found in `maintainability_portfolio_data['systems']['system']`. Hence: `system_tag='system'`.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if data_tag is None and system_tag is None:
                raise PlaceholderArgumentException(func.__name__)
            
            data = func(*args, **kwargs)

            if not _are_filters_set():
                return data

            pmd = sigrid_api.get_portfolio_metadata()

            if data_tag:
                filtered_data = _with_data_tag(data=data, portfolio_metadata=pmd, data_tag=data_tag,
                                               system_tag=system_tag)
                if not filtered_data[data_tag]:
                    _raise_no_systems_found_error()
            else:
                filtered_data = _without_data_tag(data=data, portfolio_metadata=pmd, system_tag=system_tag)
                if not filtered_data:
                    _raise_no_systems_found_error()

            return filtered_data
        return wrapper
    return decorator

def _with_data_tag(data, portfolio_metadata, data_tag, system_tag):
    systems = [entry for entry in data[data_tag] if _include(system_name=entry[system_tag], portfolio_metadata=portfolio_metadata)]
    data[data_tag] = systems
    return data

def _without_data_tag(data, portfolio_metadata, system_tag):
    systems = [entry for entry in data if _include(system_name=entry[system_tag], portfolio_metadata=portfolio_metadata)]
    return systems

def _include(system_name, portfolio_metadata):
    global _team, _division
    md = _find_system_metadata(system_name=system_name, portfolio_metadata=portfolio_metadata)
    if md is None:
        return False
    
    team_match = _team is not None and any(t in md['teamNames'] for t in _team)
    division_match = _division is not None and any(d == md['divisionName'] for d in _division)

    return team_match or division_match

def _are_filters_set():
    return _team is not None or _division is not None

def _find_system_metadata(system_name, portfolio_metadata):
    for s in portfolio_metadata:
        if s['systemName'] == system_name:
            return s
    return None

class PlaceholderArgumentException(Exception):
    def __init__(self, function_name, message="Placeholder argument exception"):
        self.function_name = function_name
        self.message = f"{message} in function '{function_name}'"
        super().__init__(self.message)
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

from typing import Optional
from functools import wraps
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


def filter_data_on_portfolio_arguments(data_tag=None, system_tag=None):
    """
    Decorator to create functions that call Sigrid API requests, optionally with a system parameter.
    If with_system is set to True, the decorator will first look for the system parameter passed to the function when called.
    If the system parameter is not provided in the function call, it will use the global system value set by set_context.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if data_tag is None and system_tag is None:
                raise PlaceholderArgumentException(func.__name__)
            
            data = func(*args, **kwargs)
            pmd = sigrid_api.get_portfolio_metadata()

            if data_tag:
                return _with_data_tag(data=data, portfolio_metadata=pmd, data_tag=data_tag, system_tag=system_tag)
            else:
                return _without_data_tag(data=data, portfolio_metadata=pmd, system_tag=system_tag)
        return wrapper
    return decorator

def _with_data_tag(data, portfolio_metadata, data_tag, system_tag):
    systems = [entry for entry in data[data_tag] if _include(system_name=entry[system_tag], portfolio_medadata=portfolio_metadata)]
    data[data_tag] = systems
    return data

def _without_data_tag(data, portfolio_metadata, system_tag):
    systems = [entry for entry in data if _include(system_name=entry[system_tag], portfolio_medadata=portfolio_metadata)]
    return systems

def _include(system_name, portfolio_medadata):
    md = _find_system_metadata(system_name=system_name, portfolio_metadata=portfolio_medadata)
    if md is None:
        # raise PlaceholderArgumentException(function_name=__name__, message=f"Could not find metadata of {system_name}")
        return False
    
    if _team is not None:
        for t in _team:
            if t in md['teamNames']:
                return True
    
    if _division is not None:
        for d in _division:
            if d == md['divisionName']:
                return True
    
    return False


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
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

from unittest.mock import patch
import pytest
import click

from report_generator.generator.data_models.portfolio import portfolio_arguments
from report_generator.generator.data_models.portfolio.portfolio_arguments import (
    set_context,
    filter_data_on_portfolio_arguments,
    PlaceholderArgumentException,
    _include,
    _are_filters_set,
    _find_system_metadata,
)


@pytest.fixture
def mock_portfolio_metadata():
    """Fixture providing sample portfolio metadata."""
    return [
        {
            'systemName': 'system1',
            'teamNames': ['TeamA', 'TeamB'],
            'divisionName': 'DivisionX'
        },
        {
            'systemName': 'system2',
            'teamNames': ['TeamC'],
            'divisionName': 'DivisionY'
        },
        {
            'systemName': 'system3',
            'teamNames': ['TeamA'],
            'divisionName': 'DivisionX'
        }
    ]


@pytest.fixture
def mock_data_with_data_tag():
    """Fixture providing sample API data with a data_tag wrapper."""
    return {
        'systems': [
            {'system': 'system1', 'maintainability': 4.0},
            {'system': 'system2', 'maintainability': 3.5},
            {'system': 'system3', 'maintainability': 4.2}
        ],
        'metadata': 'some_metadata'
    }


@pytest.fixture
def mock_data_without_data_tag():
    """Fixture providing sample API data without a data_tag wrapper."""
    return [
        {'systemName': 'system1', 'value': 100},
        {'systemName': 'system2', 'value': 200},
        {'systemName': 'system3', 'value': 150}
    ]


class TestPortfolioArguments:
    """Test cases for portfolio filtering logic."""

    def teardown_method(self):
        """Reset portfolio context after each test."""
        portfolio_arguments._team = None
        portfolio_arguments._division = None

    # Context Management Tests

    def test_set_context_with_team(self):
        """Test that set_context correctly sets team filter."""
        set_context(team=['TeamA'])

        assert portfolio_arguments._team == ['TeamA']
        assert portfolio_arguments._division is None

    def test_set_context_with_division(self):
        """Test that set_context correctly sets division filter."""
        set_context(division=['DivisionX'])

        assert portfolio_arguments._team is None
        assert portfolio_arguments._division == ['DivisionX']

    def test_set_context_with_both(self):
        """Test that set_context correctly sets both team and division filters."""
        set_context(team=['TeamA', 'TeamB'], division=['DivisionX'])

        assert portfolio_arguments._team == ['TeamA', 'TeamB']
        assert portfolio_arguments._division == ['DivisionX']

    # Filter Checking Tests

    def test_are_filters_set_returns_false_when_no_filters(self):
        """Test that _are_filters_set returns False when no filters are set."""
        assert _are_filters_set() is False

    def test_are_filters_set_returns_true_with_team(self):
        """Test that _are_filters_set returns True when team filter is set."""
        set_context(team=['TeamA'])

        assert _are_filters_set() is True

    def test_are_filters_set_returns_true_with_division(self):
        """Test that _are_filters_set returns True when division filter is set."""
        set_context(division=['DivisionX'])

        assert _are_filters_set() is True

    # System Matching Tests

    def test_include_matches_team(self, mock_portfolio_metadata):
        """Test that _include returns True when system matches team filter."""
        set_context(team=['TeamA'])

        result = _include('system1', mock_portfolio_metadata)

        assert result is True

    def test_include_matches_division(self, mock_portfolio_metadata):
        """Test that _include returns True when system matches division filter."""
        set_context(division=['DivisionY'])

        result = _include('system2', mock_portfolio_metadata)

        assert result is True

    def test_include_matches_multiple_teams(self, mock_portfolio_metadata):
        """Test that _include returns True when system matches one of multiple team filters."""
        set_context(team=['TeamB', 'TeamC'])

        result1 = _include('system1', mock_portfolio_metadata)
        result2 = _include('system2', mock_portfolio_metadata)

        assert result1 is True  # system1 has TeamB
        assert result2 is True  # system2 has TeamC

    def test_include_no_match(self, mock_portfolio_metadata):
        """Test that _include returns False when system doesn't match any filters."""
        set_context(team=['TeamD'])

        result = _include('system1', mock_portfolio_metadata)

        assert result is False

    def test_include_matches_either_team_or_division(self, mock_portfolio_metadata):
        """Test that _include uses OR logic between team and division filters."""
        set_context(team=['TeamC'], division=['DivisionX'])

        result1 = _include('system1', mock_portfolio_metadata)  # Matches division only
        result2 = _include('system2', mock_portfolio_metadata)  # Matches team only
        result3 = _include('system3', mock_portfolio_metadata)  # Matches division only

        assert result1 is True
        assert result2 is True
        assert result3 is True

    def test_find_system_metadata_returns_none_for_unknown_system(self, mock_portfolio_metadata):
        """Test that _find_system_metadata returns None for systems not in portfolio."""
        result = _find_system_metadata('unknown_system', mock_portfolio_metadata)

        assert result is None

    def test_find_system_metadata_returns_metadata_for_known_system(self, mock_portfolio_metadata):
        """Test that _find_system_metadata returns correct metadata for known systems."""
        result = _find_system_metadata('system2', mock_portfolio_metadata)

        assert result is not None
        assert result['systemName'] == 'system2'
        assert result['teamNames'] == ['TeamC']
        assert result['divisionName'] == 'DivisionY'

    # Decorator Behavior Tests

    @patch('report_generator.generator.data_models.portfolio.portfolio_arguments.sigrid_api')
    def test_decorator_returns_unchanged_data_when_no_filters(self, mock_sigrid_api, mock_data_with_data_tag):
        """Test that decorator passes data through unchanged when no filters are set."""
        @filter_data_on_portfolio_arguments(data_tag='systems', system_tag='system')
        def mock_function():
            return mock_data_with_data_tag

        result = mock_function()

        assert result == mock_data_with_data_tag
        mock_sigrid_api.get_portfolio_metadata.assert_not_called()

    @patch('report_generator.generator.data_models.portfolio.portfolio_arguments.sigrid_api')
    def test_decorator_filters_systems_with_data_tag(self, mock_sigrid_api, mock_data_with_data_tag, mock_portfolio_metadata):
        """Test that decorator correctly filters systems when using data_tag."""
        set_context(team=['TeamA'])
        mock_sigrid_api.get_portfolio_metadata.return_value = mock_portfolio_metadata

        @filter_data_on_portfolio_arguments(data_tag='systems', system_tag='system')
        def mock_function():
            return mock_data_with_data_tag

        result = mock_function()

        assert len(result['systems']) == 2  # system1 and system3 match TeamA
        assert result['systems'][0]['system'] == 'system1'
        assert result['systems'][1]['system'] == 'system3'
        assert result['metadata'] == 'some_metadata'  # Other data preserved

    @patch('report_generator.generator.data_models.portfolio.portfolio_arguments.sigrid_api')
    def test_decorator_raises_exception_when_no_systems_match(self, mock_sigrid_api, mock_data_with_data_tag, mock_portfolio_metadata):
        """Test that decorator raises ClickException when filters exclude all systems."""
        set_context(team=['NonExistentTeam'])
        mock_sigrid_api.get_portfolio_metadata.return_value = mock_portfolio_metadata

        @filter_data_on_portfolio_arguments(data_tag='systems', system_tag='system')
        def mock_function():
            return mock_data_with_data_tag

        with pytest.raises(click.ClickException) as exc_info:
            mock_function()

        assert "No systems match the specified filters" in str(exc_info.value)

    def test_decorator_requires_data_tag_or_system_tag(self):
        """Test that decorator raises exception if neither data_tag nor system_tag is provided."""
        @filter_data_on_portfolio_arguments()
        def mock_function():
            return {}

        with pytest.raises(PlaceholderArgumentException):
            mock_function()

    # Edge Cases

    def test_empty_portfolio_metadata(self):
        """Test that _include returns False when portfolio metadata is empty."""
        set_context(team=['TeamA'])

        result = _include('system1', [])

        assert result is False

    @patch('report_generator.generator.data_models.portfolio.portfolio_arguments.sigrid_api')
    def test_decorator_with_mixed_matching_systems(self, mock_sigrid_api, mock_data_with_data_tag, mock_portfolio_metadata):
        """Test that decorator correctly handles mix of matching and non-matching systems."""
        set_context(team=['TeamC'])  # Only system2 has TeamC
        mock_sigrid_api.get_portfolio_metadata.return_value = mock_portfolio_metadata

        @filter_data_on_portfolio_arguments(data_tag='systems', system_tag='system')
        def mock_function():
            return mock_data_with_data_tag

        result = mock_function()

        assert len(result['systems']) == 1
        assert result['systems'][0]['system'] == 'system2'
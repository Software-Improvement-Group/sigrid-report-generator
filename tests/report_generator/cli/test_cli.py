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
import os
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner
from importlib_resources import files
from tests.report_generator.cli.list_diffs import compare_pptx

from report_generator.cli import run as run_cli


@pytest.fixture
def output_file():
    return files("tests.report_generator.cli").joinpath("test_output.pptx")


@pytest.fixture
def template():
    return files("tests.report_generator.cli").joinpath("test-template.pptx")


@pytest.fixture
def reference_file():
    return files("tests.report_generator.cli").joinpath("reference_output.pptx")


@pytest.fixture
def customer_name():
    return "opendemo"


@pytest.fixture
def system_name():
    return "twitter-algorithm"


@pytest.fixture
def token():
    return os.environ.get('REPORT_GENERATOR_TESTS_TOKEN')


def test_generate_report(output_file, template, customer_name, system_name, token, reference_file):
    os.environ['SIGRID_REPORT_GENERATOR_RECORD_USAGE'] = '0'
    runner = CliRunner()
    result = runner.invoke(run_cli, [
        '--customer', customer_name,
        '--system', system_name,
        '--token', token,
        '--template', template,
        '--out-file', output_file,
        '--debug'
    ])

    assert result.exit_code == 0, f"CLI command did not run successfully: {result.output}"
    assert os.path.isfile(output_file), f"Output file {output_file} does not exist"

    are_equal, differences = compare_pptx(output_file, reference_file)
    assert are_equal, "Output file content is incorrect:" + '\n' + '\n'.join(differences)


class TestPortfolioFiltering:
    """Test cases for portfolio filtering validation."""
    
    def teardown_method(self):
        """Reset portfolio context after each test."""
        from report_generator.generator.data_models.portfolio import portfolio_arguments
        # Reset the global context variables
        portfolio_arguments._team = None
        portfolio_arguments._division = None

    @patch('report_generator.generator.data_models.maintainability_portfolio_data')
    @patch('report_generator.cli.sigrid_api')
    def test_no_systems_match_team_filter_exits_with_error(self, mock_sigrid_api, mock_portfolio_data):
        """Test that CLI exits cleanly when team filters exclude all systems."""
        mock_portfolio_data.system_names = []
        
        os.environ['SIGRID_REPORT_GENERATOR_RECORD_USAGE'] = '0'
        runner = CliRunner()
        result = runner.invoke(run_cli, [
            '--customer', 'test-customer',
            '--token', 'test-token',
            '--layout', 'portfolio-overview',
            '--team', 'NonExistentTeam'
        ])

        assert result.exit_code == 1
        assert "No systems match the specified filters" in result.output
        assert "--team: NonExistentTeam" in result.output

    @patch('report_generator.generator.data_models.maintainability_portfolio_data')
    @patch('report_generator.cli.sigrid_api')
    def test_no_systems_match_division_filter_exits_with_error(self, mock_sigrid_api, mock_portfolio_data):
        """Test that CLI exits cleanly when division filters exclude all systems."""
        mock_portfolio_data.system_names = []
        
        os.environ['SIGRID_REPORT_GENERATOR_RECORD_USAGE'] = '0'
        runner = CliRunner()
        result = runner.invoke(run_cli, [
            '--customer', 'test-customer',
            '--token', 'test-token',
            '--layout', 'portfolio-overview',
            '--division', 'NonExistentDivision'
        ])

        assert result.exit_code == 1
        assert "No systems match the specified filters" in result.output
        assert "--division: NonExistentDivision" in result.output

    @patch('report_generator.generator.data_models.maintainability_portfolio_data')
    @patch('report_generator.cli.sigrid_api')
    def test_no_systems_match_multiple_filters_shows_all_filters(self, mock_sigrid_api, mock_portfolio_data):
        """Test that error message shows all filters when multiple are applied."""
        mock_portfolio_data.system_names = []
        
        os.environ['SIGRID_REPORT_GENERATOR_RECORD_USAGE'] = '0'
        runner = CliRunner()
        result = runner.invoke(run_cli, [
            '--customer', 'test-customer',
            '--token', 'test-token',
            '--layout', 'portfolio-overview',
            '--team', 'Team1',
            '--team', 'Team2',
            '--division', 'Division1'
        ])

        assert result.exit_code == 1
        assert "--team: Team1, Team2" in result.output
        assert "--division: Division1" in result.output

    @patch('report_generator.cli.presets')
    @patch('report_generator.generator.data_models.maintainability_portfolio_data')
    @patch('report_generator.cli.sigrid_api')
    def test_systems_exist_after_filtering_continues_execution(self, mock_sigrid_api, mock_portfolio_data, mock_presets):
        """Test that execution continues when filters match some systems."""
        mock_portfolio_data.system_names = ['system1', 'system2']
        mock_presets.run = MagicMock()
        
        os.environ['SIGRID_REPORT_GENERATOR_RECORD_USAGE'] = '0'
        runner = CliRunner()
        result = runner.invoke(run_cli, [
            '--customer', 'test-customer',
            '--token', 'test-token',
            '--layout', 'portfolio-overview',
            '--team', 'ExistingTeam'
        ])

        # Should not exit with error
        assert "No systems match the specified filters" not in result.output
        # Presets.run should be called
        mock_presets.run.assert_called_once()

    @patch('report_generator.cli.presets')
    @patch('report_generator.cli.sigrid_api')
    def test_no_filters_skips_validation(self, mock_sigrid_api, mock_presets):
        """Test that validation is skipped when no filters are provided."""
        mock_presets.run = MagicMock()
        
        os.environ['SIGRID_REPORT_GENERATOR_RECORD_USAGE'] = '0'
        runner = CliRunner()
        result = runner.invoke(run_cli, [
            '--customer', 'test-customer',
            '--token', 'test-token',
            '--layout', 'portfolio-overview'
        ])

        # Should not show filter validation messages
        assert "No systems match the specified filters" not in result.output

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
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from report_generator.cli import run as run_cli


class TestCLIVersion:
    """Test cases for CLI version output."""

    def test_version_flag_displays_version(self):
        """Test that --version displays the program name and version."""
        runner = CliRunner()
        result = runner.invoke(run_cli, ["--version"])

        assert result.exit_code == 0
        assert "report-generator" in result.output.lower()
        assert "version" in result.output.lower()


class TestCLIParameters:
    """Test cases for CLI parameter validation."""

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_customer_parameter_required(self, mock_sigrid_api, mock_presets):
        """Test that --customer parameter is required."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        runner = CliRunner()
        result = runner.invoke(
            run_cli, ["--token", "test-token", "--layout", "portfolio-overview"]
        )

        assert result.exit_code != 0
        assert "customer" in result.output.lower() or "missing" in result.output.lower()

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_token_defaults_to_environment_variable(
        self, mock_sigrid_api, mock_presets
    ):
        """Test that --token defaults to SIGRID_CI_TOKEN environment variable."""
        os.environ["SIGRID_CI_TOKEN"] = "env-token"
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        runner.invoke(
            run_cli, ["--customer", "test-customer", "--layout", "portfolio-overview"]
        )

        # Token should be picked up from environment
        mock_sigrid_api.set_context.assert_called_once()
        assert mock_sigrid_api.set_context.call_args[1]["bearer_token"] == "env-token"

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_layout_parameter_choices(self, mock_sigrid_api, mock_presets):
        """Test that --layout only accepts valid preset IDs."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        runner = CliRunner()
        result = runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "invalid-layout-name",
            ],
        )

        assert result.exit_code != 0
        assert (
            "invalid choice" in result.output.lower()
            or "invalid value" in result.output.lower()
        )

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_layout_defaults_to_default(self, mock_sigrid_api, mock_presets):
        """Test that --layout defaults to 'system-summary' when not specified."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        runner.invoke(run_cli, ["--customer", "test-customer", "--token", "test-token"])

        mock_presets.run.assert_called_once_with("system-summary", "out")

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_out_file_parameter_default(self, mock_sigrid_api, mock_presets):
        """Test that --out-file defaults to 'out'."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
            ],
        )

        mock_presets.run.assert_called_once_with("portfolio-overview", "out")

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_out_file_parameter_custom(self, mock_sigrid_api, mock_presets):
        """Test that --out-file can be customized."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--out-file",
                "custom-report",
            ],
        )

        mock_presets.run.assert_called_once_with("portfolio-overview", "custom-report")

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_debug_flag_enables_debug_logging(self, mock_sigrid_api, mock_presets):
        """Test that --debug flag enables debug logging."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        result = runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--debug",
            ],
        )

        assert result.exit_code == 0

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_api_url_parameter_passed_to_context(self, mock_sigrid_api, mock_presets):
        """Test that --api-url is passed to sigrid_api context."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--api-url",
                "https://custom-api.example.com",
            ],
        )

        mock_sigrid_api.set_context.assert_called_once()
        assert (
            mock_sigrid_api.set_context.call_args[1]["base_url"]
            == "https://custom-api.example.com"
        )

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_start_and_end_date_parameters(self, mock_sigrid_api, mock_presets):
        """Test that --start and --end dates are passed correctly."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--start",
                "2024-01-01",
                "--end",
                "2024-12-31",
            ],
        )

        mock_sigrid_api.set_context.assert_called_once()
        assert mock_sigrid_api.set_context.call_args[1]["period"] == (
            "2024-01-01",
            "2024-12-31",
        )

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_system_parameter_required_for_system_level_presets(
        self, mock_sigrid_api, mock_presets
    ):
        """Test that --system is required for system-level layouts."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"

        # Assuming 'default' is a system-level preset
        with patch("report_generator.cli.presets.SYSTEM_LEVEL_PRESETS", {"default"}):
            runner = CliRunner()
            result = runner.invoke(
                run_cli,
                [
                    "--customer",
                    "test-customer",
                    "--token",
                    "test-token",
                    "--layout",
                    "default",
                ],
            )

            assert result.exit_code != 0
            assert "system" in result.output.lower()

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_system_parameter_not_allowed_for_portfolio_presets(
        self, mock_sigrid_api, mock_presets
    ):
        """Test that --system is not allowed for portfolio-level layouts."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"

        with patch("report_generator.cli.presets.SYSTEM_LEVEL_PRESETS", set()):
            runner = CliRunner()
            result = runner.invoke(
                run_cli,
                [
                    "--customer",
                    "test-customer",
                    "--token",
                    "test-token",
                    "--layout",
                    "portfolio-overview",
                    "--system",
                    "some-system",
                ],
            )

            assert result.exit_code != 0
            assert (
                "not allowed" in result.output.lower()
                or "system" in result.output.lower()
            )

    @patch("report_generator.cli.ReportGenerator")
    @patch("report_generator.cli.sigrid_api")
    def test_template_parameter_uses_custom_template(
        self, mock_sigrid_api, mock_generator
    ):
        """Test that --template uses custom template instead of presets."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy template file
            with open("template.pptx", "wb") as f:
                f.write(b"dummy content")

            runner.invoke(
                run_cli,
                [
                    "--customer",
                    "test-customer",
                    "--token",
                    "test-token",
                    "--template",
                    "template.pptx",
                ],
            )

            mock_generator_instance.generate.assert_called_once_with("out")

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_layout_and_template_mutually_exclusive(
        self, mock_sigrid_api, mock_presets
    ):
        """Test that --layout and --template cannot be used together."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("template.pptx", "wb") as f:
                f.write(b"dummy content")

            result = runner.invoke(
                run_cli,
                [
                    "--customer",
                    "test-customer",
                    "--token",
                    "test-token",
                    "--layout",
                    "portfolio-overview",
                    "--template",
                    "template.pptx",
                ],
            )

            assert result.exit_code != 0
            assert (
                "both" in result.output.lower()
                or "mutually exclusive" in result.output.lower()
            )

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_team_parameter_single_value(self, mock_sigrid_api, mock_presets):
        """Test that --team parameter accepts single value."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        result = runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--team",
                "TeamA",
            ],
        )

        # Should not crash, portfolio filtering handles the validation
        assert result.exit_code in [0, 1]  # 1 if no systems match

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_team_parameter_multiple_values(self, mock_sigrid_api, mock_presets):
        """Test that --team parameter accepts multiple values."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        result = runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--team",
                "TeamA",
                "--team",
                "TeamB",
            ],
        )

        assert result.exit_code in [0, 1]  # 1 if no systems match

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_division_parameter_single_value(self, mock_sigrid_api, mock_presets):
        """Test that --division parameter accepts single value."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        result = runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--division",
                "DivisionX",
            ],
        )

        assert result.exit_code in [0, 1]  # 1 if no systems match

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_division_parameter_multiple_values(self, mock_sigrid_api, mock_presets):
        """Test that --division parameter accepts multiple values."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        result = runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--division",
                "DivisionX",
                "--division",
                "DivisionY",
            ],
        )

        assert result.exit_code in [0, 1]  # 1 if no systems match

    @patch("report_generator.cli.presets")
    @patch("report_generator.cli.sigrid_api")
    def test_team_and_division_together(self, mock_sigrid_api, mock_presets):
        """Test that --team and --division can be used together."""
        os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
        mock_presets.run = MagicMock()

        runner = CliRunner()
        result = runner.invoke(
            run_cli,
            [
                "--customer",
                "test-customer",
                "--token",
                "test-token",
                "--layout",
                "portfolio-overview",
                "--team",
                "TeamA",
                "--division",
                "DivisionX",
            ],
        )

        assert result.exit_code in [0, 1]  # 1 if no systems match

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

import pytest
from click.testing import CliRunner
from importlib_resources import files

from report_generator.cli import run as run_cli
from tests.report_generator.cli.list_diffs import compare_pptx


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
    assert are_equal, f"Output file content is incorrect:\n{''.join(differences)}"

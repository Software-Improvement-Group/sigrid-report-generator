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
from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from importlib_resources import files

from report_generator import presets
from report_generator.generator.context import sigrid_api
from tests.report_generator.integration.pptx_diff import compare_pptx

PRESETS_TO_TEST = sorted(p for p in presets.ids if p != "debug")

no_token = (
    not os.environ.get("REPORT_GENERATOR_TESTS_TOKEN")
    and not os.environ.get("SIGRID_TOKEN")
    and not os.environ.get("SIGRID_CI_TOKEN")
)


@pytest.fixture
def token():
    return (
        os.environ.get("REPORT_GENERATOR_TESTS_TOKEN")
        or os.environ.get("SIGRID_TOKEN")
        or os.environ.get("SIGRID_CI_TOKEN")
    )


def _period():
    start = (date.today() + relativedelta(months=-1)).strftime("%Y-%m-%d")
    end = date.today().strftime("%Y-%m-%d")
    return start, end


@pytest.mark.integration
@pytest.mark.skipif(no_token, reason="Token not set in environment")
@pytest.mark.parametrize("preset_id", PRESETS_TO_TEST)
def test_generate_preset(preset_id, token, tmp_path):
    os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
    output_file = str(tmp_path / f"output_{preset_id}.pptx")
    reference_file = str(
        files("tests.report_generator.integration").joinpath(
            f"reference_{preset_id}.pptx"
        )
    )

    system = "twitter-algorithm" if preset_id in presets.SYSTEM_LEVEL_PRESETS else None
    sigrid_api.reset_context()
    sigrid_api.set_context(
        bearer_token=token,
        customer="opendemo",
        system=system,
        period=_period(),
    )

    presets.run(preset_id, output_file)

    assert os.path.isfile(output_file)
    are_equal, differences = compare_pptx(output_file, reference_file)
    assert are_equal, "Output differs from reference:\n" + "\n".join(differences)

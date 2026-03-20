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
import warnings

import pytest
from freezegun import freeze_time
from importlib_resources import files

from report_generator import presets
from report_generator.generator.context import sigrid_api
from tests.report_generator.integration.pptx_diff import compare_pptx

PRESETS_TO_TEST = sorted(p for p in presets.ids if p != "debug")
PERIOD = ("2026-01-11", "2026-03-8")

no_token = (
    not os.environ.get("REPORT_GENERATOR_TESTS_TOKEN")
    and not os.environ.get("SIGRID_TOKEN")
    and not os.environ.get("SIGRID_CI_TOKEN")
)


@pytest.mark.integration
@pytest.mark.skipif(no_token, reason="Token not set in environment")
@pytest.mark.parametrize("preset_id", PRESETS_TO_TEST)
@freeze_time(PERIOD[1])
def test_generate_preset(preset_id, tmp_path):
    token = (
        os.environ.get("REPORT_GENERATOR_TESTS_TOKEN")
        or os.environ.get("SIGRID_TOKEN")
        or os.environ.get("SIGRID_CI_TOKEN")
    )
    os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"
    output_file = str(tmp_path / f"output_{preset_id}.pptx")
    reference_file = str(
        files("tests.report_generator.integration").joinpath(
            f"reference_{preset_id}.pptx"
        )
    )

    if not os.path.isfile(reference_file):
        warnings.warn(
            f"Reference file missing for preset '{preset_id}'. "
            f"Generate it with: python tests/report_generator/integration/update_references.py {preset_id} --token <TOKEN>",
            stacklevel=2,
        )
        return

    system = "integrationtest-kafka" if preset_id in presets.SYSTEM_LEVEL_PRESETS else None
    sigrid_api.reset_context()
    sigrid_api.set_context(
        bearer_token=token,
        customer="reportgeneratordemo",
        system=system,
        period=PERIOD,
    )

    presets.run(preset_id, output_file)

    assert os.path.isfile(output_file)

    are_equal, differences = compare_pptx(output_file, reference_file)
    assert are_equal, "Output differs from reference:\n" + "\n".join(differences)

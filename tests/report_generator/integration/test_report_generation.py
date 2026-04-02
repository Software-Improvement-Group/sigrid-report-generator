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
from freezegun import freeze_time

from report_generator import presets
from report_generator.generator.context import sigrid_api
from report_generator.report_generator import ReportGenerator
from tests.report_generator.integration import _shared
from tests.report_generator.integration.pptx_diff import compare_pptx

PRESETS_TO_TEST = sorted(p for p in presets.ids if p != "debug")


@pytest.mark.parametrize("preset_id", PRESETS_TO_TEST)
def test_template_exists_for_each_preset(preset_id):
    template_path = _shared.TEMPLATES_DIR / f"{preset_id}.pptx"
    assert template_path.is_file(), (
        f"Template missing: {template_path}\n"
        f"Copy the template for preset '{preset_id}' into {_shared.TEMPLATES_DIR}/"
    )


@pytest.mark.integration
@pytest.mark.parametrize("preset_id", PRESETS_TO_TEST)
@freeze_time(_shared.PERIOD[1])
def test_generate_preset(preset_id, tmp_path):
    token = _shared.resolve_token()
    assert token, "Sigrid API token not set in environment. Set SIGRID_REPORTGENERATORDEMO_TOKEN, SIGRID_TOKEN, or SIGRID_CI_TOKEN"
    os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"

    template_file = _shared.TEMPLATES_DIR / f"{preset_id}.pptx"
    output_file = tmp_path / f"output_{preset_id}.pptx"
    reference_file = _shared.REFERENCES_DIR / f"reference_{preset_id}.pptx"

    assert template_file.is_file(), f"Template missing: {template_file}"
    assert reference_file.is_file(), (
        f"Reference missing: {reference_file}\n"
        f"Generate it with: python tests/report_generator/integration/update_references.py {preset_id} --token <TOKEN>"
    )

    sigrid_api.reset_context()
    sigrid_api.set_context(
        bearer_token=token,
        customer="reportgeneratordemo",
        system=_shared.system_for_preset(preset_id),
        period=_shared.PERIOD,
    )

    report_generator = ReportGenerator(str(template_file))
    report_generator.generate(str(output_file))

    assert output_file.is_file()

    are_equal, differences = compare_pptx(str(output_file), str(reference_file))
    assert are_equal, "Output differs from reference:\n" + "\n".join(differences)

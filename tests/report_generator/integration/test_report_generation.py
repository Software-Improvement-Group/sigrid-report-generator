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
from pathlib import Path

import pytest
from freezegun import freeze_time

from report_generator import presets
from report_generator.generator.context import sigrid_api
from report_generator.report_generator import ReportGenerator
from tests.report_generator.integration.pptx_diff import compare_pptx

PRESETS_TO_TEST = sorted(p for p in presets.ids if p != "debug")
PERIOD = ("2026-01-11", "2026-03-8")

INTEGRATION_DIR = Path(__file__).parent
TEMPLATES_DIR = INTEGRATION_DIR / "templates"
REFERENCES_DIR = INTEGRATION_DIR / "references"

no_token = (
    not os.environ.get("REPORT_GENERATOR_TESTS_TOKEN")
    and not os.environ.get("SIGRID_TOKEN")
    and not os.environ.get("SIGRID_CI_TOKEN")
)


@pytest.mark.parametrize("preset_id", PRESETS_TO_TEST)
def test_template_exists_for_each_preset(preset_id):
    template_path = TEMPLATES_DIR / f"{preset_id}.pptx"
    assert template_path.is_file(), (
        f"Template missing: {template_path}\n"
        f"Copy the template for preset '{preset_id}' into {TEMPLATES_DIR}/"
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

    template_file = TEMPLATES_DIR / f"{preset_id}.pptx"
    output_file = tmp_path / f"output_{preset_id}.pptx"
    reference_file = REFERENCES_DIR / f"reference_{preset_id}.pptx"

    assert template_file.is_file(), f"Template missing: {template_file}"
    assert reference_file.is_file(), (
        f"Reference missing: {reference_file}\n"
        f"Generate it with: python tests/report_generator/integration/update_references.py {preset_id} --token <TOKEN>"
    )

    system = (
        "integrationtest-kafka" if preset_id in presets.SYSTEM_LEVEL_PRESETS else None
    )
    sigrid_api.reset_context()
    sigrid_api.set_context(
        bearer_token=token,
        customer="reportgeneratordemo",
        system=system,
        period=PERIOD,
    )

    report_generator = ReportGenerator(str(template_file))
    report_generator.generate(str(output_file))

    assert output_file.is_file()

    are_equal, differences = compare_pptx(str(output_file), str(reference_file))
    assert are_equal, "Output differs from reference:\n" + "\n".join(differences)

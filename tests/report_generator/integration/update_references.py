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

"""Regenerate a single integration-test reference file.

Usage:
    python tests/report_generator/integration/update_references.py <preset_id> --token <TOKEN>

Run from the repo root with the package installed (pip install -e .).
Only update one preset at a time — review the diff carefully before committing.
"""

import argparse
import os
import sys
from pathlib import Path

from freezegun import freeze_time

from report_generator import presets
from report_generator.generator.context import sigrid_api

PERIOD = ("2026-01-11", "2026-03-8")

INTEGRATION_DIR = Path(__file__).parent
VALID_PRESET_IDS = sorted(p for p in presets.ids if p != "debug")


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate a single integration-test reference .pptx file."
    )
    parser.add_argument(
        "preset_id",
        choices=VALID_PRESET_IDS,
        help="Preset to regenerate (one of: " + ", ".join(VALID_PRESET_IDS) + ")",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("SIGRID_TOKEN")
        or os.environ.get("SIGRID_CI_TOKEN")
        or os.environ.get("REPORT_GENERATOR_TESTS_TOKEN"),
        help=(
            "Sigrid bearer token (defaults to $SIGRID_TOKEN / $SIGRID_CI_TOKEN / "
            "$REPORT_GENERATOR_TESTS_TOKEN)"
        ),
    )
    args = parser.parse_args()

    if not args.token:
        print(
            "Error: no token provided. Pass --token or set $SIGRID_TOKEN, "
            "$SIGRID_CI_TOKEN, or $REPORT_GENERATOR_TESTS_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(1)

    os.environ["SIGRID_REPORT_GENERATOR_RECORD_USAGE"] = "0"

    system = (
        "integrationtest-kafka" if args.preset_id in presets.SYSTEM_LEVEL_PRESETS else None
    )
    sigrid_api.set_context(
        bearer_token=args.token,
        customer="reportgeneratordemo",
        system=system,
        period=PERIOD,
    )

    reference_path = str(INTEGRATION_DIR / f"reference_{args.preset_id}.pptx")
    print(f"Generating {reference_path} ...")
    with freeze_time(PERIOD[1]):
        presets.run(args.preset_id, reference_path)

    print(
        f"\n"
        f"WARNING  Reference updated: reference_{args.preset_id}.pptx\n"
        f"\n"
        f"Before committing, carefully review what changed:\n"
        f"  python -m tests.report_generator.integration.pptx_diff \\\n"
        f"      reference_{args.preset_id}.pptx <previous_backup>\n"
        f"\n"
        f"Only commit if ALL differences are expected (e.g. template update, new data).\n"
        f"Unexpected changes mean something broke."
    )


if __name__ == "__main__":
    main()

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

from report_generator import presets

PERIOD = ("2026-01-11", "2026-03-8")

INTEGRATION_DIR = Path(__file__).parent
TEMPLATES_DIR = INTEGRATION_DIR / "templates"
REFERENCES_DIR = INTEGRATION_DIR / "references"


def resolve_token() -> str | None:
    return (
        os.environ.get("SIGRID_REPORTGENERATORDEMO_TOKEN")
        or os.environ.get("SIGRID_TOKEN")
        or os.environ.get("SIGRID_CI_TOKEN")
    )


def system_for_preset(preset_id: str) -> str | None:
    return (
        "integrationtest-kafka" if preset_id in presets.SYSTEM_LEVEL_PRESETS else None
    )

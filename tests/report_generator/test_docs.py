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

from pathlib import Path

import pytest

from report_generator.generator.placeholders import placeholders as all_placeholders

FILENAME = "docs/placeholder descriptions.md"
PROJECT_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if p.name == "report-generator"
)
DOC_PATH = PROJECT_ROOT / FILENAME


def test_placeholder_documentation_is_up_to_date() -> None:
    doc_path = Path(DOC_PATH)
    assert doc_path.is_file(), (
        f"Expected documentation file '{doc_path}' is missing. "
        "Run generate_placeholder_docs.py to create it."
    )

    content = doc_path.read_text(encoding="utf-8")

    missing = [ph.key for ph in all_placeholders if ph.key not in content]

    if missing:
        placeholders = ", ".join(sorted(missing))
        pytest.fail(
            f"The placeholder documentation is out of date. "
            f"Regenerate it using generate_placeholder_docs.py; "
            f"missing docs for placeholder(s): {placeholders}"
        )

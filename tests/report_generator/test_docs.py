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
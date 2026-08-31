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

from collections.abc import Callable

from importlib_resources import files

from report_generator import ReportGenerator


def _generate_report(template_name: str, output_path: str) -> None:
    template = files("report_generator.presets.templates").joinpath(template_name)
    report_generator = ReportGenerator(str(template))
    report_generator.generate(output_path)


def generate_debug_docx(output_path: str) -> None:
    _generate_report("debug-template.docx", output_path)


def generate_system_snapshot(output_path: str) -> None:
    _generate_report("system-snapshot.pptx", output_path)


def generate_modernization_report(output_path: str) -> None:
    _generate_report("modernization.pptx", output_path)


def generate_objectives_report(output_path: str) -> None:
    _generate_report("objectives.pptx", output_path)


def generate_refactoring_candidates_report(output_path: str) -> None:
    _generate_report("refactoring-candidates.pptx", output_path)


def generate_system_maintainability_one_pager(output_path: str) -> None:
    _generate_report("system-maintainability-one-pager.pptx", output_path)


def generate_portfolio_change(output_path: str) -> None:
    _generate_report("portfolio-change.pptx", output_path)


def generate_portfolio_metrics(output_path: str) -> None:
    _generate_report("portfolio-metrics.pptx", output_path)


def generate_hygiene_report(output_path: str) -> None:
    _generate_report("hygiene-report.pptx", output_path)


def generate_portfolio_snapshot(output_path: str) -> None:
    _generate_report("portfolio-snapshot.pptx", output_path)


def generate_npr_5333_overview(output_path: str) -> None:
    _generate_report("npr-5333-overview.pptx", output_path)


def generate_system_snapshot_whitelabel(output_path: str) -> None:
    _generate_report("system-snapshot-whitelabel.pptx", output_path)


_preset_reports: dict[str, Callable[[str], None]] = {
    "system-snapshot": generate_system_snapshot,
    "system-snapshot-whitelabel": generate_system_snapshot_whitelabel,
    "debug": generate_debug_docx,
    "modernization": generate_modernization_report,
    "objectives": generate_objectives_report,
    "refactoring-candidates": generate_refactoring_candidates_report,
    "system-maintainability-one-pager": generate_system_maintainability_one_pager,
    "portfolio-metrics": generate_portfolio_metrics,
    "portfolio-change": generate_portfolio_change,
    "hygiene-report": generate_hygiene_report,
    "portfolio-snapshot": generate_portfolio_snapshot,
    "npr-5333-overview": generate_npr_5333_overview,
}

# Old preset names kept for backwards compatibility. TODO: Remove once users have migrated.
DEPRECATED_PRESET_ALIASES: dict[str, str] = {
    "system-summary": "system-snapshot",
    "itdd-technical-debt": "system-snapshot",
    "portfolio-overview": "portfolio-change",
    "portfolio-baseline-report": "portfolio-snapshot",
    "system-summary-whitelabel": "system-snapshot-whitelabel",
}

SYSTEM_LEVEL_PRESETS = {
    "system-snapshot",
    "system-snapshot-whitelabel",
    "debug",
    "refactoring-candidates",
    "system-maintainability-one-pager",
}

ids = set(_preset_reports.keys()) | set(DEPRECATED_PRESET_ALIASES.keys())


def resolve_preset_id(preset_id: str) -> str:
    return DEPRECATED_PRESET_ALIASES.get(preset_id, preset_id)


def run(preset_id: str, output_path: str) -> None:
    preset_id = resolve_preset_id(preset_id)
    if preset_id not in _preset_reports:
        raise ValueError(f"Unsupported preset: {preset_id}")

    _preset_reports[preset_id](output_path)

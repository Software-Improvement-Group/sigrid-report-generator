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

from typing import Callable

from importlib_resources import files

from report_generator.generator import ReportGenerator


def _generate_report(template_name: str, output_path: str) -> None:
    template = files("report_generator.presets.templates").joinpath(template_name)
    report_generator = ReportGenerator(str(template))
    report_generator.generate(output_path)


def generate_debug_docx(output_path: str) -> None:
    _generate_report("debug-template.docx", output_path)


def generate_debug_pptx(output_path: str) -> None:
    _generate_report("debug-template.pptx", output_path)


def generate_itdd_light(output_path: str) -> None:
    _generate_report("default-template.pptx", output_path)
    
    
def generate_itdd_system_technical_debt_report(output_path: str) -> None:
    _generate_report("itdd-technical-debt.pptx", output_path)


def generate_modernization_report(output_path: str) -> None:
    _generate_report("modernization.pptx", output_path)


_preset_reports: dict[str, Callable[[str], None]] = {
    'default'               : generate_itdd_light,
    'word-debug'            : generate_debug_docx,
    'debug'                 : generate_debug_pptx,
    'itdd-technical-debt'   : generate_itdd_system_technical_debt_report,
    'modernization'         : generate_modernization_report
}

ids = set(_preset_reports.keys())


def run(preset_id: str, output_path: str) -> None:
    if preset_id not in ids:
        raise ValueError(f"Unsupported preset: {preset_id}")

    _preset_reports[preset_id](output_path)

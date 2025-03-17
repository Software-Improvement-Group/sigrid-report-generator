from typing import Callable

from importlib_resources import files

from report_generator import ReportGenerator


def _generate_report(template_name: str, output_path: str) -> None:
    template = files("presets.templates").joinpath(template_name)
    report_generator = ReportGenerator(str(template))
    report_generator.generate(output_path)


def generate_debug_docx(output_path: str) -> None:
    _generate_report("debug-template.docx", output_path)


def generate_debug_pptx(output_path: str) -> None:
    _generate_report("debug-template.pptx", output_path)


def generate_itdd_light(output_path: str) -> None:
    _generate_report("default-template.pptx", output_path)


_preset_reports: dict[str, Callable[[str], None]] = {
    'default'   : generate_itdd_light,
    'word-debug': generate_debug_docx,
    'debug'     : generate_debug_pptx
}

ids = set(_preset_reports.keys())


def run(preset_id: str, output_path: str) -> None:
    if preset_id not in ids:
        raise ValueError(f"Unsupported preset: {preset_id}")

    _preset_reports[preset_id](output_path)

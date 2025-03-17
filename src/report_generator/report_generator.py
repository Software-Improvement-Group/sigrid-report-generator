from report_generator.placeholders import placeholders as default_placeholders, PlaceholderCollection
from report_generator.report import Report


class ReportGenerator:
    def __init__(self, template_path: str):
        self.placeholders: PlaceholderCollection = default_placeholders
        self.report: Report = Report.from_template(template_path)

    def register_additional_placeholders(self, placeholders: PlaceholderCollection) -> None:
        self.placeholders.update(placeholders)

    def generate(self, output_path: str) -> None:
        for placeholder in self.placeholders:
            placeholder.resolve(self.report)

        self.report.save(output_path)

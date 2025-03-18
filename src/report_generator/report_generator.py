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

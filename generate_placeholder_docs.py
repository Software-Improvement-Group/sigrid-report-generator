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

from typing import List, Optional, Set

import pandas as pd

from report_generator.generator.placeholders import Placeholder, placeholders as all_placeholders
from report_generator.generator.placeholders.base import ParameterList, PlaceholderDocType
from report_generator.generator.report import ReportType

FILENAME = "docs/placeholder_documentation.md"
PARAM_RANGE_REPRESENTATIONS ={
    '1, 2, 3, 4, 5'                : '1-5',
    '1, 2, 3, 4, 5, 6, 7, 8, 9, 10': '1-10',
}

class MarkdownElement:
    def __init__(self, content):
        self.content = content

    def __str__(self):
        return self.content + '\n\n'


class Header(MarkdownElement):
    def __init__(self, content: str, level=2):
        super().__init__('#' * level + ' ' + content)


class Paragraph(MarkdownElement):
    def __init__(self, content: str):
        super().__init__(content)

class Table(MarkdownElement):
    def __init__(self, data: pd.DataFrame):
        data.fillna("")

        if 'Parameters' in data.columns and data['Parameters'].str.strip().eq('').all():
            data = data.drop(columns=['Parameters'])

        super().__init__(data.to_markdown(index=False))


class Document:
    def __init__(self):
        self.elements: List[MarkdownElement] = []

    def add(self, element: MarkdownElement):
        self.elements.append(element)

    def __str__(self):
        return ''.join(str(element) for element in self.elements)

def placeholders_to_table(placeholders, skip_columns: Set[str] = None) -> pd.DataFrame:
    data = [get_placeholder_row_data(placeholder, skip_columns) for placeholder in placeholders]

    df = pd.DataFrame(data)
    df = df.sort_values(by='Key').reset_index(drop=True)
    return df


def get_placeholder_doc(placeholder_class: Placeholder) -> Optional[str]:
    doc = placeholder_class.__doc__
    if doc and not doc.startswith('Placeholder('):
        return doc

    for parent in placeholder_class.__bases__:
        if issubclass(parent, Placeholder):
            return get_placeholder_doc(parent)

    return None

def get_placeholder_row_data(placeholder: Placeholder, skip_columns: Set[str] = None) -> dict:
    if skip_columns is None:
        skip_columns = []

    all_data = {
        'Key'        : placeholder.key,
        'Supports'   : supports_to_representation(placeholder),
        'Description': get_placeholder_doc(placeholder),
        'Parameters' : parameterlist_to_representation(
            placeholder.allowed_parameters) if placeholder.is_parameterized() else ''
    }

    return {key: value for key, value in all_data.items() if key not in skip_columns}

def parameterlist_to_representation(parameter_list: ParameterList) -> str:
    as_string = ', '.join(str(param) for param in parameter_list)
    return PARAM_RANGE_REPRESENTATIONS.get(as_string, as_string)


def supports_to_representation(placeholder: Placeholder) -> str:
    support_mappings = {
        ReportType.PRESENTATION: "PPTX",
        ReportType.DOCUMENT    : "DOCX",
    }

    supported_types = [support_mappings[report_type] for report_type in support_mappings if placeholder.supports(report_type)]

    return ', '.join(supported_types)

def generate_documentation():
    doc = Document()
    doc.add(Header("Report Template Placeholders"))

    doc.add(Header("Text Placeholders"))
    doc.add(Paragraph(
        "Use these placeholders anywhere in your PowerPoint/Word template. `report-generator` will replace them with their actual value."))
    text_placeholders = [placeholder for placeholder in all_placeholders if
                         placeholder.__doc_type__ == PlaceholderDocType.TEXT]
    doc.add(Table(placeholders_to_table(text_placeholders, skip_columns={"Supports"})))

    doc.add(Header("Chart Placeholders"))
    doc.add(Paragraph("These placeholders, generally placed off-screen, only serve to identify a slide on which a specific chart is placed. If you want to use this chart, be sure to copy both the chart and the placeholder from a standard template and then modify its layout BUT NOT its structure or chart type."))
    chart_placeholders = [placeholder for placeholder in all_placeholders if
                          placeholder.__doc_type__ == PlaceholderDocType.CHART]
    doc.add(Table(placeholders_to_table(chart_placeholders)))

    doc.add(Header("Other Placeholders"))
    other_placeholders = [placeholder for placeholder in all_placeholders if
                          placeholder.__doc_type__ == PlaceholderDocType.OTHER]
    doc.add(Table(placeholders_to_table(other_placeholders)))

    return str(doc)


def write_markdown_file(content, filename):
    with open(filename, "w") as f:
        f.write(content)
    print(f"Placeholder documentation has been generated in '{filename}'")


if __name__ == "__main__":
    markdown_content = generate_documentation()
    write_markdown_file(markdown_content, FILENAME)
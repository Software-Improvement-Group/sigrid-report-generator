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

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Union

from docx import Document
from pptx import Presentation


class ReportType(Enum):
    DOCUMENT = "document"
    PRESENTATION = "presentation"

    @property
    def extension(self):
        if self == ReportType.DOCUMENT:
            return "docx"
        elif self == ReportType.PRESENTATION:
            return "pptx"


@dataclass
class Report:
    content: Union[Document, Presentation]
    type: ReportType

    @classmethod
    def from_template(cls, template_path: str) -> 'Report':
        if template_path.endswith('.docx'):
            return cls(Document(template_path), ReportType.DOCUMENT)
        elif template_path.endswith('.pptx'):
            return cls(Presentation(template_path), ReportType.PRESENTATION)
        else:
            raise ValueError(f"Unsupported file format: {template_path.split('.')[-1]}")

    def save(self, output_path: str) -> None:
        if not output_path.endswith(f".{self.type.extension}"):
            output_path = f"{output_path}.{self.type.extension}"

        self.content.save(output_path)
        logging.info(f"Generated report saved to {output_path}")

    def __str__(self) -> str:
        return f"Report({self.type.value}, {self.content.__class__.__name__})"

    def __getattr__(self, name):
        return getattr(self.content, name)

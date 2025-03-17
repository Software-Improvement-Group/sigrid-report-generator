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
        else:
            return None


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

    def __str__(self) -> str:
        return f"Report({self.type.value}, {self.content.__class__.__name__})"

    def __getattr__(self, name):
        return getattr(self.content, name)

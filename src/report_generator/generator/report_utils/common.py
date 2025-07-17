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
from dataclasses import dataclass
from typing import Optional, Union
from xmlrpc.client import Boolean

from docx.enum.dml import MSO_THEME_COLOR as MSO_THEME_COLOR_DOCX
from docx.shared import RGBColor as DocxRGBColor
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.text.run import Font as DocxFont, Run as DocxRun
from pptx.dml.color import RGBColor as PptxRGBColor
from pptx.enum.dml import MSO_THEME_COLOR as MSO_THEME_COLOR_PPTX
from pptx.text.text import Font as PptxFont, _Paragraph as _PptxParagraph, _Run as _PptxRun

CommonParagraph = Union[_PptxParagraph, DocxParagraph]
CommonRun = Union[_PptxRun, DocxRun]
CommonFont = Union[PptxFont, DocxFont]
MSO_THEME_COLOR_COMMON = Union[MSO_THEME_COLOR_PPTX, MSO_THEME_COLOR_DOCX]
CommonRGBColor = Union[PptxRGBColor, DocxRGBColor]


@dataclass
class FontColor:
    rgb: Optional[CommonRGBColor] = None
    theme_color: Optional[MSO_THEME_COLOR_COMMON] = None
    brightness: Optional[float] = None


@dataclass
class FontProperties:
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    name: Optional[str] = None
    size: Optional[int] = None
    underline: Optional[bool] = None
    color: FontColor = None


def merge_runs_with_same_formatting(paragraph: CommonParagraph):
    """
    Merges consecutive runs with the same formatting in a paragraph.
    PowerPoint/Word sometimes arbitrarily splits text into runs, even with identical formatting.
    This can split placeholders across multiple runs (e.g., "AAP_", "NOOT", "_MIES").
    This function combines such runs to enable effective replacement.
    """
    run_idx = 0
    while run_idx < len(paragraph.runs) - 1:
        current_run = paragraph.runs[run_idx]
        next_run = paragraph.runs[run_idx + 1]

        if has_same_formatting(current_run, next_run):
            combine_runs(current_run, next_run)
        else:
            run_idx += 1


def has_same_formatting(run_a: CommonRun, run_b: CommonRun) -> Boolean:
    return get_font_properties(run_a) == get_font_properties(run_b)


def get_font_properties(run: CommonRun) -> Optional[FontProperties]:
    font = run.font

    if not font:
        return None

    props = FontProperties(
        bold=font.bold,
        italic=font.italic,
        name=font.name,
        size=font.size,
        underline=font.underline,
    )

    # Accessing the color property has side effects in pptx, so we check if it exists first
    if not font.fill.type or not font.color.type:
        return props

    color = font.color

    props.color = FontColor(
        rgb=color.rgb if hasattr(color, 'rgb') else None,
        theme_color=(color.theme_color if hasattr(color, 'theme_color')
                                          and color.theme_color is not MSO_THEME_COLOR_PPTX.NOT_THEME_COLOR
                                          and color.theme_color is not MSO_THEME_COLOR_DOCX.NOT_THEME_COLOR
                     else None),
        brightness=color.brightness if hasattr(color, 'brightness') else None
    )

    return props


def apply_font_properties(run: CommonRun, font_props: FontProperties):
    font = run.font
    if font_props.bold is not None:
        font.bold = font_props.bold
    if font_props.italic is not None:
        font.italic = font_props.italic
    if font_props.name is not None:
        font.name = font_props.name
    if font_props.size is not None:
        font.size = font_props.size
    if font_props.underline is not None:
        font.underline = font_props.underline
    if font_props.color.rgb is not None:
        font.color.rgb = font_props.color.rgb
    if font_props.color.theme_color is not None:
        font.color.theme_color = font_props.color.theme_color
    if font_props.color.brightness is not None and run.font.color.type is not None:
        font.color.brightness = font_props.color.brightness


def combine_runs(base: CommonRun, suffix: CommonRun):
    base.text = base.text + suffix.text
    r_to_remove = suffix._r
    r_to_remove.getparent().remove(r_to_remove)
    return

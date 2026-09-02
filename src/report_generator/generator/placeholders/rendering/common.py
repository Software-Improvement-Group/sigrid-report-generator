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

from docx.enum.dml import MSO_THEME_COLOR as MSO_THEME_COLOR_DOCX
from docx.shared import RGBColor as DocxRGBColor
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.text.run import Font as DocxFont
from docx.text.run import Run as DocxRun
from pptx.dml.color import RGBColor as PptxRGBColor
from pptx.enum.dml import MSO_THEME_COLOR as MSO_THEME_COLOR_PPTX

# noinspection PyProtectedMember
from pptx.text.text import (
    Font as PptxFont,
)
from pptx.text.text import (
    _Paragraph as _PptxParagraph,
)
from pptx.text.text import (
    _Run as _PptxRun,
)

CommonParagraph = _PptxParagraph | DocxParagraph
CommonRun = _PptxRun | DocxRun
CommonFont = PptxFont | DocxFont
MSO_THEME_COLOR_COMMON = MSO_THEME_COLOR_PPTX | MSO_THEME_COLOR_DOCX
CommonRGBColor = PptxRGBColor | DocxRGBColor


@dataclass
class FontColor:
    rgb: CommonRGBColor | None = None
    theme_color: MSO_THEME_COLOR_COMMON | None = None
    brightness: float | None = None


@dataclass
class FontProperties:
    bold: bool | None = None
    italic: bool | None = None
    name: str | None = None
    size: int | None = None
    underline: bool | None = None
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


def has_same_formatting(run_a: CommonRun, run_b: CommonRun) -> bool:
    return get_font_properties(run_a) == get_font_properties(run_b)


_SIMPLE_FONT_ATTRS = ("bold", "italic", "name", "size", "underline")


def get_font_properties(run: CommonRun) -> FontProperties | None:
    font = run.font

    if not font:
        return None

    props = FontProperties(**{attr: getattr(font, attr) for attr in _SIMPLE_FONT_ATTRS})

    # Accessing the color property has side effects in pptx, so we check if it exists first
    if font.fill.type and font.color.type:
        props.color = _resolve_font_color(font.color)

    return props


def _resolve_font_color(color) -> FontColor:
    return FontColor(
        rgb=color.rgb if hasattr(color, "rgb") else None,
        theme_color=(
            color.theme_color
            if hasattr(color, "theme_color")
            and color.theme_color is not MSO_THEME_COLOR_PPTX.NOT_THEME_COLOR
            and color.theme_color is not MSO_THEME_COLOR_DOCX.NOT_THEME_COLOR
            else None
        ),
        brightness=color.brightness if hasattr(color, "brightness") else None,
    )


def apply_font_properties(run: CommonRun, font_props: FontProperties):
    font = run.font
    for attr in _SIMPLE_FONT_ATTRS:
        value = getattr(font_props, attr)
        if value is not None:
            setattr(font, attr, value)
    if font_props.color is not None:
        _apply_font_color(font, font_props.color)


def _apply_font_color(font, color: FontColor):
    if color.rgb is not None:
        font.color.rgb = color.rgb
    if color.theme_color is not None:
        font.color.theme_color = color.theme_color
    if color.brightness is not None and font.color.type is not None:
        font.color.brightness = color.brightness


def combine_runs(base: CommonRun, suffix: CommonRun):
    base.text = base.text + suffix.text
    # noinspection PyProtectedMember
    r_to_remove = suffix._r
    r_to_remove.getparent().remove(r_to_remove)
    return

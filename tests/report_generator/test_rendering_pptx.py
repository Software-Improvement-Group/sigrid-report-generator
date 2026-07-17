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

from pptx import Presentation
from pptx.util import Inches

from report_generator.generator.placeholders.rendering import pptx as render


def _presentation_with_paragraphs(*lines):
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    textbox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(4))
    text_frame = textbox.text_frame
    text_frame.paragraphs[0].text = lines[0]
    for line in lines[1:]:
        text_frame.add_paragraph().text = line
    return presentation


def _add_slide_with_text(presentation, text):
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    textbox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(4))
    textbox.text_frame.paragraphs[0].text = text
    return slide


def _slide_texts(presentation):
    return [
        shape.text_frame.text
        for slide in presentation.slides
        for shape in slide.shapes
        if shape.has_text_frame
    ]


def test_delete_slides_with_placeholder_removes_only_matching_slide():
    presentation = Presentation()
    _add_slide_with_text(presentation, "keep this SYSTEM_PY slide")
    _add_slide_with_text(presentation, "drop this SECURITY_RATING slide")
    _add_slide_with_text(presentation, "keep this one too")

    render.delete_slides_with_placeholder(presentation, "SECURITY_RATING")

    remaining = _slide_texts(presentation)
    assert len(list(presentation.slides)) == 2
    assert "keep this SYSTEM_PY slide" in remaining
    assert "keep this one too" in remaining
    assert all("SECURITY_RATING" not in text for text in remaining)


def test_delete_slides_with_placeholder_is_idempotent():
    presentation = Presentation()
    _add_slide_with_text(presentation, "drop this SECURITY_RATING slide")
    _add_slide_with_text(presentation, "keep this one")

    render.delete_slides_with_placeholder(presentation, "SECURITY_RATING")
    render.delete_slides_with_placeholder(presentation, "SECURITY_RATING")

    assert len(list(presentation.slides)) == 1


def test_delete_slides_with_placeholder_matches_chart_or_table_shape_name():
    presentation = Presentation()
    slide = _add_slide_with_text(presentation, "no key in the text here")
    slide.shapes[0].name = "SECURITY_CHART"
    _add_slide_with_text(presentation, "keep this one")

    render.delete_slides_with_placeholder(presentation, "SECURITY_CHART")

    assert len(list(presentation.slides)) == 1
    assert "keep this one" in _slide_texts(presentation)


def test_delete_slides_with_placeholder_no_match_keeps_all_slides():
    presentation = Presentation()
    _add_slide_with_text(presentation, "slide one")
    _add_slide_with_text(presentation, "slide two")

    render.delete_slides_with_placeholder(presentation, "MISSING_KEY")

    assert len(list(presentation.slides)) == 2


def test_finds_placeholder_in_every_paragraph_of_same_text_frame():
    presentation = _presentation_with_paragraphs(
        "rebuild value of SYSTEM_PY person years",
        "no placeholder here",
        "or SYSTEM_PY person years (PY)",
    )

    paragraphs = render.find_text_in_presentation(presentation, "SYSTEM_PY")

    assert len(paragraphs) == 2
    assert all("SYSTEM_PY" in p.text for p in paragraphs)


def test_update_replaces_placeholder_across_paragraphs():
    presentation = _presentation_with_paragraphs(
        "rebuild value of SYSTEM_PY person years",
        "or SYSTEM_PY person years (PY)",
    )

    paragraphs = render.find_text_in_presentation(presentation, "SYSTEM_PY")
    render.update_many_paragraphs(paragraphs, "SYSTEM_PY", "42.0")

    texts = [p.text for p in render.find_text_in_presentation(presentation, "42.0")]
    assert len(texts) == 2
    assert all("SYSTEM_PY" not in text for text in texts)


def test_find_shapes_with_text_deduplicates_shared_shape():
    presentation = _presentation_with_paragraphs(
        "SYSTEM_PY one",
        "SYSTEM_PY two",
    )

    shapes = render.find_shapes_with_text(presentation, "SYSTEM_PY")

    assert len(shapes) == 1


def test_search_text_is_matched_literally_not_as_regex():
    # "42.0" must not match "4250": the dot is a literal, not a wildcard.
    presentation = _presentation_with_paragraphs("value is 4250 today")

    assert render.find_text_in_presentation(presentation, "42.0") == []

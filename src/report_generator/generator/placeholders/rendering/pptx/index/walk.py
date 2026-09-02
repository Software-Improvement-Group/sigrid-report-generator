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

from dataclasses import dataclass, field

from pptx.enum.shapes import MSO_SHAPE_TYPE

from .records import ParagraphRecord, PresentationIndex, SlideIndex


def _is_graphic_frame(shape) -> bool:
    return "GraphicFrame" in type(shape).__name__


@dataclass
class _ShapeWalk:
    records: list[ParagraphRecord] = field(default_factory=list)
    shape_names: set[str] = field(default_factory=set)
    top_level_shape: object = None

    def descend_from(self, top_level_shape) -> None:
        self.top_level_shape = top_level_shape
        self.descend(top_level_shape)

    def descend(self, shape) -> None:
        """Deliberately descends through the proxy API rather than the underlying XML: several
        placeholders locate their target by walking back up `paragraph._parent`, and those
        parent links only exist on proxies that were built by descending the same way.
        """
        self.shape_names.add(shape.name.strip())
        if _is_graphic_frame(shape):
            self._collect_table_cells(shape)
        else:
            self._collect_paragraphs(shape)
            self._descend_into_group(shape)

    def _collect_table_cells(self, shape) -> None:
        if not shape.has_table:
            return
        for cell in shape.table.iter_cells():
            self._record(cell.text_frame.paragraphs[0], text_owner=cell)

    def _collect_paragraphs(self, shape) -> None:
        if not shape.has_text_frame:
            return
        for paragraph in shape.text_frame.paragraphs:
            self._record(paragraph, text_owner=paragraph)

    def _descend_into_group(self, shape) -> None:
        if shape.shape_type != MSO_SHAPE_TYPE.GROUP:
            return
        for nested_shape in shape.shapes:
            self.descend(nested_shape)

    def _record(self, paragraph, text_owner) -> None:
        self.records.append(
            ParagraphRecord(
                paragraph=paragraph,
                text_owner=text_owner,
                text=text_owner.text,
                top_level_shape=self.top_level_shape,
            )
        )


def slide_index(slide) -> SlideIndex:
    top_level_shapes = list(slide.shapes)
    walk = _ShapeWalk()
    for shape in top_level_shapes:
        walk.descend_from(shape)
    return SlideIndex(
        slide=slide,
        paragraphs=walk.records,
        shape_names_including_nested=walk.shape_names,
        top_level_shapes=top_level_shapes,
    )


def _records_by_paragraph_element(
    records: list[ParagraphRecord],
) -> dict[object, list[ParagraphRecord]]:
    grouped: dict[object, list[ParagraphRecord]] = {}
    for record in records:
        # noinspection PyProtectedMember
        grouped.setdefault(record.paragraph._p, []).append(record)
    return grouped


def presentation_index(presentation) -> PresentationIndex:
    slides = [slide_index(slide) for slide in presentation.slides]
    paragraphs = [record for slide in slides for record in slide.paragraphs]
    return PresentationIndex(
        slides=slides,
        paragraphs=paragraphs,
        slide_index_by_element={slide.slide.element: slide for slide in slides},
        records_by_paragraph_element=_records_by_paragraph_element(paragraphs),
    )

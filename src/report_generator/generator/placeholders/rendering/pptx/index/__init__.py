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

"""Where the text in a presentation is, answered from one cached traversal.

Locating a placeholder used to walk the whole presentation, once per placeholder key. This
package walks it once and answers every later lookup from the result.
"""

# noinspection PyProtectedMember
from pptx.text.text import _Paragraph

from . import cache, walk
from .records import ParagraphRecord, PresentationIndex, SlideIndex

__all__ = [
    "ParagraphRecord",
    "PresentationIndex",
    "SlideIndex",
    "for_presentation",
    "for_slide",
    "invalidate",
    "matches",
    "matching_paragraphs",
    "note_text_changed",
    "word_bounded_pattern",
]


def for_presentation(presentation) -> PresentationIndex:
    return cache.index_for(presentation, lambda: walk.presentation_index(presentation))


def for_slide(slide) -> SlideIndex:
    """A slide that has been detached from the slide id list is no longer reachable from the
    presentation, so it will not be in the index. Walking it is the honest answer -- returning
    nothing would silently claim the slide has no text.
    """
    presentation = slide.part.package.presentation_part.presentation
    index = cache.index_for(slide, lambda: walk.presentation_index(presentation))
    return index.slide_index_by_element.get(slide.element) or walk.slide_index(slide)


def note_text_changed(paragraph: _Paragraph) -> None:
    """Cheaper than invalidating: the document structure has not changed, only the text of one
    paragraph, and a later lookup may search for the text that was just written.
    """
    index = cache.cached_index(paragraph)
    if index is None:
        return
    # noinspection PyProtectedMember
    for record in index.records_by_paragraph_element.get(paragraph._p, ()):
        record.text = record.text_owner.text


def invalidate(anchor) -> None:
    """Every helper that removes a slide, a shape or a table row must call this: cached records
    would otherwise point at detached elements, and writing through them fails silently
    rather than loudly.
    """
    cache.invalidate(anchor)


def matches(text: str, search_text: str) -> bool:
    """Whether the search text occurs in the text as a whole word, treated literally."""
    return cache.matches_word_bounded(text, search_text)


def matching_paragraphs(records, search_text):
    return [
        record.paragraph
        for record in records
        if cache.matches_word_bounded(record.text, search_text)
    ]


def word_bounded_pattern(search_text: str):
    """The cached compiled ``\\bsearch_text\\b`` pattern, for callers that need to locate or
    replace a match rather than just test whether one exists.
    """
    return cache.word_bounded_pattern(search_text)

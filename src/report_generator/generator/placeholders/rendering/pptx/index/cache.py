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
"""Caches one document traversal for the currently open document.

Locating a placeholder used to walk the whole document, and a report resolves over a thousand
placeholder keys, so the walk ran a thousand times. The walk itself is cheap (tens of
milliseconds); repeating it was not. This module keeps the result of a single walk so every
subsequent lookup is a scan over cached records instead of a fresh traversal.

Only one report is generated at a time, so a single slot suffices: indexing a different
document simply replaces the cached entry. The entry holds a strong reference to the document's
``Package``, so it is compared by identity rather than by ``id()`` -- there is no risk of an
``id()`` being reused by another object while we still hold the reference.

Any proxy that exposes ``.part.package`` works as an anchor -- a presentation, a slide, a shape,
a table or a paragraph. That matters because the callers reach this module from all of those, and
because at runtime the object handed to the rendering layer is a ``Report`` rather than a
presentation (it delegates attribute access to the wrapped document).

Only the PowerPoint path uses this. The Word path walks a much smaller document and is not on
any hot path, so it is left alone.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Entry:
    package_kept_alive: Any
    index: Any


_entry: _Entry | None = None


def _package_of(anchor) -> Any:
    return anchor.part.package


def index_for(anchor, build: Callable[[], Any]) -> Any:
    """Return the cached index for the anchor's document, building it on first use."""
    global _entry
    package = _package_of(anchor)

    if _entry is not None and _entry.package_kept_alive is package:
        return _entry.index

    index = build()
    _entry = _Entry(package_kept_alive=package, index=index)
    return index


def cached_index(anchor) -> Any | None:
    """Return the already-built index for the anchor's document, or None if there is none.

    Used by the refresh hooks, which are best-effort by nature: if nothing has been indexed
    there is nothing to go stale. A proxy that is not attached to a document has no part at
    all -- also nothing to refresh, rather than a failure.
    """
    try:
        package = _package_of(anchor)
    except AttributeError:
        return None

    if _entry is not None and _entry.package_kept_alive is package:
        return _entry.index
    return None


def invalidate(anchor) -> None:
    """Drop the cached index for the anchor's document.

    Called by every helper that changes document *structure* -- removing a slide, a shape or a
    table row, or adding a paragraph. Rebuilding costs a single walk, and structural changes
    happen a handful of times per report, so there is no need to prune individual records.
    """
    global _entry
    if _entry is not None and _entry.package_kept_alive is _package_of(anchor):
        _entry = None


def clear() -> None:
    """Drop the cached index. Test seam."""
    global _entry
    _entry = None


@dataclass
class _PatternCache:
    """Compiled word-boundary patterns per search text.

    ``re`` memoises compiled patterns internally but only keeps a few hundred, and a report
    searches for more than a thousand distinct keys, so it would thrash.
    """

    patterns: dict[str, re.Pattern] = field(default_factory=dict)

    def word_bounded(self, search_text: str) -> re.Pattern:
        pattern = self.patterns.get(search_text)
        if pattern is None:
            pattern = re.compile(rf"\b{re.escape(search_text)}\b")
            self.patterns[search_text] = pattern
        return pattern


_patterns = _PatternCache()


def matches_word_bounded(text: str, search_text: str) -> bool:
    """Whether search_text occurs in text as a whole word, treated literally.

    The substring test is a cheap pre-filter: ``\\bX\\b`` can only match where ``X`` occurs, so
    skipping the regex when the substring is absent cannot change the outcome.
    """
    return search_text in text and bool(
        _patterns.word_bounded(search_text).search(text)
    )

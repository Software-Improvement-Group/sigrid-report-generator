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
"""Caches one document traversal per open document.

Locating a placeholder used to walk the whole document, and a report resolves over a thousand
placeholder keys, so the walk ran a thousand times. The walk itself is cheap (tens of
milliseconds); repeating it was not. This module keeps the result of a single walk so every
subsequent lookup is a scan over cached records instead of a fresh traversal.

Entries are keyed on ``id()`` of the document's ``Package`` and hold a strong reference to it.
Weak keys look tempting but would never be collected: the cached records hold document proxies
whose parent chain reaches the package, so the value keeps the key alive. The strong reference
also guarantees the package outlives its entry, so its ``id()`` can never be reused by another
object while we are still keyed on it. Capacity is therefore bounded explicitly instead.

Any proxy that exposes ``.part.package`` works as an anchor -- a presentation, a slide, a shape,
a table or a paragraph. That matters because the callers reach this module from all of those, and
because at runtime the object handed to the rendering layer is a ``Report`` rather than a
presentation (it delegates attribute access to the wrapped document).

Only the PowerPoint path uses this. The Word path walks a much smaller document and is not on
any hot path, so it is left alone.
"""

import re
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# One report is generated at a time, so a single entry is enough for a ~100% hit rate. The
# second slot keeps the cache useful if two documents are ever interleaved.
_CAPACITY = 2


@dataclass
class _Entry:
    package: Any  # strong reference: keeps the key's id() from being reused
    index: Any


_entries: OrderedDict[int, _Entry] = OrderedDict()


def _package_of(anchor) -> Any:
    return anchor.part.package


def index_for(anchor, build: Callable[[], Any]) -> Any:
    """Return the cached index for the anchor's document, building it on first use."""
    package = _package_of(anchor)
    key = id(package)

    entry = _entries.get(key)
    if entry is not None:
        _entries.move_to_end(key)
        return entry.index

    index = build()
    _entries[key] = _Entry(package=package, index=index)
    _entries.move_to_end(key)
    while len(_entries) > _CAPACITY:
        _entries.popitem(last=False)
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

    entry = _entries.get(id(package))
    return entry.index if entry else None


def invalidate(anchor) -> None:
    """Drop the cached index for the anchor's document.

    Called by every helper that changes document *structure* -- removing a slide, a shape or a
    table row, or adding a paragraph. Rebuilding costs a single walk, and structural changes
    happen a handful of times per report, so there is no need to prune individual records.
    """
    _entries.pop(id(_package_of(anchor)), None)


def clear() -> None:
    """Drop every cached index. Test seam."""
    _entries.clear()


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

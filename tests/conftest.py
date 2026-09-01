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

from unittest.mock import ANY, patch

import pytest

from report_generator.generator.context import portfolio_filters
from report_generator.generator.placeholders.rendering import traversal_cache

# `filter_data_on_portfolio_arguments` unconditionally excludes inactive/development-only
# systems, which requires portfolio metadata. `ANY` matches any systemName lookup, so every
# system is treated as active unless a test provides its own portfolio metadata mock.
_DEFAULT_ACTIVE_METADATA = [
    {"systemName": ANY, "active": True, "isDevelopmentOnly": False}
]


@pytest.fixture(autouse=True)
def _default_active_portfolio_metadata(request):
    """Integration tests hit (or replay pinned fixtures of) the real Sigrid API and must
    see real portfolio metadata, so this default is skipped for them."""
    if request.node.get_closest_marker("integration"):
        yield
        return

    with patch.object(
        portfolio_filters.sigrid_api,
        "get_portfolio_metadata",
        return_value=_DEFAULT_ACTIVE_METADATA,
    ):
        yield


@pytest.fixture(autouse=True)
def _clear_traversal_cache():
    """The cache holds a strong reference per document and has room for only a few, so a leaked
    entry (a mock presentation, say) would keep later tests from exercising the warm index."""
    traversal_cache.clear()
    yield
    traversal_cache.clear()

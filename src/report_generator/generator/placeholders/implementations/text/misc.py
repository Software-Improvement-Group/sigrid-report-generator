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

from .base import text_placeholder

from datetime import date

@text_placeholder()
def security_days_since_mythos_disclosure():
    """Number of days elapsed since Anthropic's initial Mythos disclosure on April 7, 2026."""
    return str((date.today() - date(2026, 4, 7)).days)
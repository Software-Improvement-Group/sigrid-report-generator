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

from typing import Set, Type

from .base import Placeholder
from .misc import placeholders as misc_placeholders
from .table import placeholders as table_placeholders
from .text import placeholders as text_placeholders

PlaceholderCollection = Set[Type[Placeholder]]

placeholders: PlaceholderCollection = text_placeholders | misc_placeholders | table_placeholders

from .text import text_placeholder, parameterized_text_placeholder

__all__ = ['Placeholder', 'text_placeholder', 'parameterized_text_placeholder', 'PlaceholderCollection', 'placeholders']

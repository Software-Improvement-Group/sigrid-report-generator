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

from report_generator.generator.placeholders.implementations.base import MultiParameterList, Placeholder
from report_generator.generator.placeholders.implementations.charts import (
    placeholders as chart_placeholders,
)
from report_generator.generator.placeholders.implementations.images import (
    placeholders as image_placeholders,
)
from report_generator.generator.placeholders.implementations.misc import (
    placeholders as misc_placeholders,
)
from report_generator.generator.placeholders.implementations.table import (
    placeholders as table_placeholders,
)
from report_generator.generator.placeholders.implementations.text import (
    parameterized_text_placeholder,
    text_placeholder,
)
from report_generator.generator.placeholders.implementations.text import (
    placeholders as text_placeholders,
)

PlaceholderCollection = set[type[Placeholder]]

placeholders: PlaceholderCollection = (
    text_placeholders
    | misc_placeholders
    | table_placeholders
    | image_placeholders
    | chart_placeholders
)

__all__ = [
    "MultiParameterList",
    "Placeholder",
    "PlaceholderCollection",
    "parameterized_text_placeholder",
    "placeholders",
    "text_placeholder",
]

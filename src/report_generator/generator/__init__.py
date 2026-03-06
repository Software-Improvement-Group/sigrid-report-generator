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

from functools import reduce

from . import domain, placeholders
from .context import sigrid_api
from .domain import data_model_arguments
from .placeholders import rendering
from .report_generator import ReportGenerator


def compose_options(*decorators):
    """
    Composes multiple decorators into a single decorator.
    Applied in reverse order so the first in the list is the outermost wrapper.
    """
    def composition(func):
        return reduce(lambda f, dec: dec(f), reversed(decorators), func)
    return composition

_generator_arguments_aggregate = [
    data_model_arguments
]

generator_arguments = compose_options(*_generator_arguments_aggregate)
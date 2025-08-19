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

from report_generator.generator.data_models import *
from .base import text_placeholder


@text_placeholder()
def objectives_period_start():
    """The start date of the period on which objectives are being reported."""
    return objectives_data.comparison_period.start.strftime("%B %Y")


@text_placeholder()
def objectives_period_end():
    """The end date of the period on which objectives are being reported."""
    return objectives_data.comparison_period.end.strftime("%B %Y")

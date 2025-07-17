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
def system_name():
    """The name of the system as defined in Sigrid Metadata, capitalized."""
    return system_metadata.display_name


@text_placeholder()
def customer_name():
    """The name of the customer as defined in Sigrid, capitalized."""
    return maintainability_data.customer_name

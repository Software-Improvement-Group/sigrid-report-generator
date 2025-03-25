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

from report_generator.generator.placeholders.text.implementations import _to_json_name

class TestPlaceholders:

    def test_to_json_name(self):
        assert _to_json_name("UNIT_SIZE") == "unitSize"
        assert _to_json_name("DUPLICATION") == "duplication"

        assert _to_json_name("duplication") == "duplication"
        assert _to_json_name("UnIt_sIze") == "unitSize"
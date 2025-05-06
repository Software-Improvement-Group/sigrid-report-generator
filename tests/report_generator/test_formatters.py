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

from report_generator.generator.formatters import *


class TestFormatter:

    def test_calc_stars_works(self):
        assert formatters.calculate_stars(1.5) == "★★☆☆☆"
        assert formatters.calculate_stars(1.499999) == "★☆☆☆☆"
        assert formatters.calculate_stars(4.5) == "★★★★★"
        assert formatters.calculate_stars(7.5) == "★★★★★"
        assert formatters.calculate_stars(-3) == ""

        formatters.use_sig_sterren()
        assert formatters.calculate_stars(1.5) == "HHIII"
        assert formatters.calculate_stars(1.499999) == "HIIII"
        assert formatters.calculate_stars(4.5) == "HHHHH"
        assert formatters.calculate_stars(7.5) == "HHHHH"
        assert formatters.calculate_stars(-3) == ""

    def test_maintainability_round(self):
        assert formatters.maintainability_round(1.50000) == "1.5"

        assert formatters.maintainability_round(1.499999) == "1.4"
        assert formatters.maintainability_round(5.4) == "5.4"

        assert formatters.maintainability_round(3.284) == "3.2"

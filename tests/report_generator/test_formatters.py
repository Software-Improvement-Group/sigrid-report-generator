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
from report_generator.generator.formatters import formatters


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

    def test_star_rating_round(self):
        assert formatters.star_rating_round(1.50000) == "1.5"

        assert formatters.star_rating_round(1.499999) == "1.4"
        assert formatters.star_rating_round(5.4) == "5.4"

        assert formatters.star_rating_round(3.284) == "3.2"

    def test_format_diff(self):
        assert formatters.format_diff(None, None) == ""
        assert formatters.format_diff(None, 1.0) == ""
        assert formatters.format_diff(1.0, None) == ""
        assert formatters.format_diff(1.0, 1.0) == "="
        assert formatters.format_diff(1.0, 1.2) == "+ 0.2"
        assert formatters.format_diff(1.2, 1.0) == "- 0.2"


class TestMaintainabilityPortfolioFormatting:
    """Test cases for maintainability portfolio text formatting with edge cases."""

    def test_format_maintainability_statement_with_normal_values(self):
        """Test formatting with normal values."""
        from report_generator.generator.placeholders.implementations.text import _format_maintainability_statement
        
        result = _format_maintainability_statement(5, 10, "above 4 stars")
        assert "5" in result
        assert "(50%)" in result
        assert "above 4 stars" in result

    def test_format_maintainability_statement_singular(self):
        """Test formatting uses singular form correctly."""
        from report_generator.generator.placeholders.implementations.text import _format_maintainability_statement
        
        result = _format_maintainability_statement(1, 10, "above 4 stars")
        assert "is 1" in result
        assert "system" in result
        assert "scores" in result

    def test_format_short_maintainability_statement_with_normal_values(self):
        """Test short formatting with normal values."""
        from report_generator.generator.placeholders.implementations.text import _format_short_maintainability_statement
        
        result = _format_short_maintainability_statement(3, 10, "above 4 stars")
        assert "About 3" in result
        assert "(30%)" in result
        assert "above 4 stars" in result

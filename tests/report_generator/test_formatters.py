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
from report_generator.generator.placeholders.formatting import formatters


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

    def test_normalize_percentages(self):
        # Values already summing to 100 are unchanged.
        assert formatters.normalize_percentages([25.0, 25.0, 50.0]) == [
            25.0,
            25.0,
            50.0,
        ]

    def test_normalize_percentages_rescales_to_100(self):
        result = formatters.normalize_percentages([70.0, 17.0, 6.0, 10.0])
        assert abs(sum(result) - 100.0) < 1e-9
        # Proportions are preserved.
        assert abs(result[0] / result[1] - 70.0 / 17.0) < 1e-9

    def test_normalize_percentages_all_zero(self):
        assert formatters.normalize_percentages([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]

    def test_build_sigrid_link(self):
        assert (
            formatters.build_sigrid_link("acme", "my-system", "security")
            == "https://sigrid-says.com/acme/my-system/-/security"
        )


class TestMaintainabilityPortfolioFormatting:
    """Test cases for maintainability portfolio text formatting with edge cases."""

    def test_format_maintainability_statement_with_normal_values(self):
        """Test formatting with normal values."""
        from report_generator.generator.placeholders.implementations.text.maintainability_portfolio import (
            _format_maintainability_statement,
        )

        result = _format_maintainability_statement(5, 10, "above 4 stars")
        assert "5" in result
        assert "(50%)" in result
        assert "above 4 stars" in result

    def test_format_maintainability_statement_singular(self):
        """Test formatting uses singular form correctly."""
        from report_generator.generator.placeholders.implementations.text.maintainability_portfolio import (
            _format_maintainability_statement,
        )

        result = _format_maintainability_statement(1, 10, "above 4 stars")
        assert "is 1" in result
        assert "system" in result
        assert "scores" in result

    def test_format_short_maintainability_statement_with_normal_values(self):
        """Test short formatting with normal values."""
        from report_generator.generator.placeholders.implementations.text.maintainability_portfolio import (
            _format_short_maintainability_statement,
        )

        result = _format_short_maintainability_statement(3, 10, "above 4 stars")
        assert "About 3" in result
        assert "(30%)" in result
        assert "above 4 stars" in result


class TestSplitDaysIntoBuckets:
    def test_basic_bucketing(self):
        # buckets: total, <10, <20, >=20
        assert formatters.split_days_into_buckets(
            days=[5, 12, 7, 25, 19, 3], buckets=[10, 20]
        ) == [
            6,  # total
            3,  # <10: 5, 7, 3
            2,  # <20: 12, 19
            1,  # >=20: 25
        ]

    def test_empty_days(self):
        assert formatters.split_days_into_buckets(days=[], buckets=[5, 10]) == [
            0,  # total
            0,  # <5
            0,  # <10
            0,  # >=10
        ]

    def test_empty_buckets(self):
        # All values should go into "> last bucket"
        assert formatters.split_days_into_buckets(days=[1, 2, 3], buckets=[]) == [
            3,  # total
            3,  # all values fall into final bucket
        ]

    def test_random_order_values_in_buckets(self):
        assert formatters.split_days_into_buckets(
            days=[4, 12, 7, 25, 19, 3], buckets=[5, 20, 10]
        ) == [
            6,  # total
            2,  # <5: 3, 4
            1,  # <10: 7
            2,  # <20: 12, 19
            1,  # >=20: 25
        ]

from report_generator.formatters import *


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

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

from report_generator.generator.domain import maintainability_portfolio_data
from report_generator.generator.placeholders.formatting.formatters import star_rating_round
from .base import text_placeholder


def _format_percentage(percentage):
    if percentage < 1:
        percentage = "<1"
    return f"{percentage}%"


def _format_maintainability_statement(amount, number_of_systems, postfix):
    perc = _format_percentage(int(100 * amount / number_of_systems))
    return f"There {'are' if amount > 1 else 'is'} {amount} ({perc}) {'systems' if amount > 1 else 'system'} that {'score' if amount > 1 else 'scores'} {postfix}."


def _format_short_maintainability_statement(amount, number_of_systems, postfix):
    perc = _format_percentage(int(100 * amount / number_of_systems))
    return f"About {amount} ({perc}) {'systems' if amount > 1 else 'system'} {'score' if amount > 1 else 'scores'} {postfix}"


@text_placeholder()
def portfolio_period_start_date():
    """The portfolio reporting period's start date in yyyy-mm-dd format."""
    return maintainability_portfolio_data.period[0]


@text_placeholder()
def portfolio_period_end_date():
    """The portfolio reporting period's end date in yyyy-mm-dd format."""
    return maintainability_portfolio_data.period[1]


@text_placeholder()
def portfolio_period_maint_summary():
    """The portfolio maintainability summary at the period's end date."""
    stats = maintainability_portfolio_data.statistics
    res = []
    if stats['maintainability']['5-star'] + stats['maintainability']['4-star'] > 0:
        res.append(
            _format_maintainability_statement(stats['maintainability']['5-star'] + stats['maintainability']['4-star'],
                                              stats['maintainability']['number-of-systems'],
                                              "above market average (≥ 4 stars)"))
    if stats['maintainability']['3-star'] > 0:
        res.append(_format_maintainability_statement(stats['maintainability']['3-star'],
                                                     stats['maintainability']['number-of-systems'],
                                                     "market average (3 stars)"))
    if stats['maintainability']['2-star'] + stats['maintainability']['1-star'] > 0:
        res.append(
            _format_maintainability_statement(stats['maintainability']['2-star'] + stats['maintainability']['1-star'],
                                              stats['maintainability']['number-of-systems'],
                                              "below market average (≤ 2 stars)"))
    return "\n".join(res)


@text_placeholder()
def portfolio_period_maint_short_summary():
    """The portfolio maintainability short summary at the period's end date."""
    stats = maintainability_portfolio_data.statistics
    processed_stats = {
        'above-market-average': stats['maintainability']['5-star'] + stats['maintainability']['4-star'],
        'market-average'      : stats['maintainability']['3-star'],
        'below-market-average': stats['maintainability']['2-star'] + stats['maintainability']['1-star']
    }
    postfixes = {
        'above-market-average': "above market average on maintainability",
        'market-average'      : "market average on maintainability",
        'below-market-average': "below market average on maintainability"
    }
    key = max(processed_stats, key=processed_stats.get)
    res = _format_short_maintainability_statement(processed_stats[key], stats['maintainability']['number-of-systems'],
                                                  postfixes[key])
    return res


@text_placeholder()
def portfolio_period_maint_change_summary():
    """The portfolio maintainability change summary, given the period's start and end dates."""
    stats = maintainability_portfolio_data.statistics
    res = []
    if stats['maintainability-change']['biggest-increase']:
        key = next(iter(stats['maintainability-change']['biggest-increase']))
        res.append(
            f"The largest increase in maintainability rating was experienced by {key} ({int(10 * stats['maintainability-change']['biggest-increase'][key]) / 10}).")
    if stats['maintainability-change']['biggest-decrease']:
        key = next(iter(stats['maintainability-change']['biggest-decrease']))
        res.append(
            f"The largest decrease in maintainability rating was experienced by {key} ({int(10 * stats['maintainability-change']['decrease'][key]) / 10}).")
    if res:
        return "\n".join(res)
    return "The portfolio remained stable during the measured period."


@text_placeholder()
def portfolio_period_maint_change_short_summary():
    """The portfolio maintainability change short summary, given the period's start and end dates."""
    stats = maintainability_portfolio_data.statistics
    start_avg = int(stats['maintainability']['start-average'] * 10) / 10
    end_avg = int(stats['maintainability']['end-average'] * 10) / 10
    diff = int((end_avg - start_avg) * 10) / 10
    if abs(diff) < 0.01:
        return f"The portfolio remained stable ({end_avg}) during the measured period"
    return f"The portfolio's maintainability has {'increased' if start_avg < end_avg else 'decreased'} (with {diff} to {end_avg}) during the measured period"


@text_placeholder()
def portfolio_maint_above_market():
    """Percentage of systems scoring above market average (≥3.5 stars)."""
    distribution = maintainability_portfolio_data.get_rating_distribution_percentages
    return distribution['above_market']


@text_placeholder()
def portfolio_maint_avg_rating():
    """Volume-weighted average maintainability rating across all systems in the portfolio."""
    return star_rating_round(maintainability_portfolio_data.weighted_average_rating)


@text_placeholder()
def portfolio_maint_market_average():
    """Percentage of systems scoring market average (2.5-3.5 stars)."""
    distribution = maintainability_portfolio_data.get_rating_distribution_percentages
    return distribution['market_average']


@text_placeholder()
def portfolio_maint_below_market():
    """Percentage of systems scoring below market average (<2.5 stars)."""
    distribution = maintainability_portfolio_data.get_rating_distribution_percentages
    return distribution['below_market']


@text_placeholder()
def portfolio_maint_increased():
    """Percentage of systems that have seen an increase in maintainability."""
    stats = maintainability_portfolio_data.statistics
    total = stats['maintainability-change']['systems-increased'] + stats['maintainability-change']['systems-stable'] + \
            stats['maintainability-change']['systems-decreased']
    if total == 0:
        return 0
    return round(100 * stats['maintainability-change']['systems-increased'] / total)


@text_placeholder()
def portfolio_maint_stable():
    """Percentage of systems that have remained stable in maintainability."""
    stats = maintainability_portfolio_data.statistics
    total = stats['maintainability-change']['systems-increased'] + stats['maintainability-change']['systems-stable'] + \
            stats['maintainability-change']['systems-decreased']
    if total == 0:
        return 0
    return round(100 * stats['maintainability-change']['systems-stable'] / total)


@text_placeholder()
def portfolio_maint_decreased():
    """Percentage of systems that have seen a decrease in maintainability."""
    stats = maintainability_portfolio_data.statistics
    total = stats['maintainability-change']['systems-increased'] + stats['maintainability-change']['systems-stable'] + \
            stats['maintainability-change']['systems-decreased']
    if total == 0:
        return 0
    return round(100 * stats['maintainability-change']['systems-decreased'] / total)


@text_placeholder()
def portfolio_maint_biggest_changes():
    """Descriptive summary of the biggest maintainability changes in the portfolio."""
    stats = maintainability_portfolio_data.statistics
    res = []
    biggest_increase = stats['maintainability-change']['biggest-increase']
    if biggest_increase:
        system = next(iter(biggest_increase.keys()))
        diff = biggest_increase[system]
        res.append(
            f"The largest increase in maintainability rating was experienced by {system} ({int(diff * 10) / 10} stars).")
    biggest_decrease = stats['maintainability-change']['biggest-decrease']
    if biggest_decrease:
        system = next(iter(biggest_decrease.keys()))
        diff = biggest_decrease[system]
        res.append(
            f"The largest decrease in maintainability rating was experienced by {system} ({int(diff * 10) / 10} stars).")
    if res:
        return " ".join(res)
    return ""


@text_placeholder()
def portfolio_maint_largest_increase_system():
    """Name of the system with the largest increase in maintainability rating."""
    stats = maintainability_portfolio_data.statistics
    biggest_increase = stats['maintainability-change']['biggest-increase']
    if biggest_increase:
        return next(iter(biggest_increase.keys()))
    return None


@text_placeholder()
def portfolio_maint_largest_increase_stars():
    """Star rating increase of the system with the largest improvement."""
    stats = maintainability_portfolio_data.statistics
    biggest_increase = stats['maintainability-change']['biggest-increase']
    if biggest_increase:
        system = next(iter(biggest_increase.keys()))
        return biggest_increase[system]
    return 0


@text_placeholder()
def portfolio_maint_largest_decrease_system():
    """Name of the system with the largest decrease in maintainability rating."""
    stats = maintainability_portfolio_data.statistics
    biggest_decrease = stats['maintainability-change']['biggest-decrease']
    if biggest_decrease:
        return next(iter(biggest_decrease.keys()))
    return None


@text_placeholder()
def portfolio_maint_largest_decrease_stars():
    """Star rating decrease of the system with the largest decline."""
    stats = maintainability_portfolio_data.statistics
    biggest_decrease = stats['maintainability-change']['biggest-decrease']
    if biggest_decrease:
        system = next(iter(biggest_decrease.keys()))
        return biggest_decrease[system]
    return 0


@text_placeholder()
def portfolio_relative_volume_change():
    """Whether the overall portfolio volume increased or decreased."""
    stats = maintainability_portfolio_data.statistics
    total_change = stats['volume-change']['total-end'] - stats['volume-change']['total-start']
    return 'increase' if total_change >= 0 else 'decrease'


@text_placeholder()
def portfolio_volume_change():
    """The absolute change in portfolio volume in person months."""
    stats = maintainability_portfolio_data.statistics
    total_change = stats['volume-change']['total-end'] - stats['volume-change']['total-start']
    if abs(total_change) > 12:
        return f"{round(abs(total_change / 12), 1)} person years"
    return f"{round(abs(total_change), 1)} person months"


@text_placeholder()
def portfolio_system_biggest_volume_change():
    """Name of the system with the biggest volume change."""
    stats = maintainability_portfolio_data.statistics
    return stats['volume-change']['biggest-change-system']


@text_placeholder()
def portfolio_relative_biggest_volume_change():
    """Whether the biggest volume change was an increase or decrease."""
    stats = maintainability_portfolio_data.statistics
    amount = stats['volume-change']['biggest-change-amount']
    return 'an increase' if amount >= 0 else 'a decrease'


@text_placeholder()
def portfolio_system_pm_biggest_volume_change():
    """The volume change amount for the system with the biggest change."""
    stats = maintainability_portfolio_data.statistics
    amount = stats['volume-change']['biggest-change-amount']
    if amount > 12:
        return f"{round(abs(amount / 12), 1)} person years"
    return f"{round(abs(amount), 1)} person months"


@text_placeholder()
def portfolio_test_code_low():
    """Percentage of systems with test code ratio < 50%."""
    distribution = maintainability_portfolio_data.test_code_ratio_distribution_percentages
    return distribution['low']


@text_placeholder()
def portfolio_test_code_medium():
    """Percentage of systems with test code ratio between 50% and 100%."""
    distribution = maintainability_portfolio_data.test_code_ratio_distribution_percentages
    return distribution['medium']


@text_placeholder()
def portfolio_test_code_high():
    """Percentage of systems with test code ratio ≥ 100%."""
    distribution = maintainability_portfolio_data.test_code_ratio_distribution_percentages
    return distribution['high']


@text_placeholder()
def portfolio_relative_test_code_difference():
    """Whether the overall test code ratio increased or decreased."""
    stats = maintainability_portfolio_data.statistics
    total_change = stats['test-code-ratio-change']['total-end'] - stats['test-code-ratio-change']['total-start']
    return 'an increase' if total_change >= 0 else 'a decrease'


@text_placeholder()
def portfolio_test_code_difference():
    """The percentage difference in test code ratio."""
    stats = maintainability_portfolio_data.statistics
    total_start = stats['test-code-ratio-change']['total-start']
    total_end = stats['test-code-ratio-change']['total-end']

    if total_start == 0:
        return 0

    percentage_change = ((total_end - total_start) / total_start) * 100
    if percentage_change > 0:
        return f"+{round(percentage_change, 1)}"
    return f"-{round(abs(percentage_change), 1)}"


@text_placeholder()
def portfolio_test_code_increase():
    """Percentage of systems that have seen an increase in test code ratio."""
    stats = maintainability_portfolio_data.statistics
    total = stats['test-code-ratio-change']['systems-increased'] + stats['test-code-ratio-change']['systems-stable'] + \
            stats['test-code-ratio-change']['systems-decreased']
    if total == 0:
        return 0
    return round(100 * stats['test-code-ratio-change']['systems-increased'] / total)


@text_placeholder()
def portfolio_test_code_decrease():
    """Percentage of systems that have seen a decrease in test code ratio."""
    stats = maintainability_portfolio_data.statistics
    total = stats['test-code-ratio-change']['systems-increased'] + stats['test-code-ratio-change']['systems-stable'] + \
            stats['test-code-ratio-change']['systems-decreased']
    if total == 0:
        return 0
    return round(100 * stats['test-code-ratio-change']['systems-decreased'] / total)


@text_placeholder()
def portfolio_test_code_biggest_changes():
    """Descriptive summary of the biggest test code ratio changes in the portfolio."""
    stats = maintainability_portfolio_data.statistics
    res = []
    biggest_increase = stats['test-code-ratio-change']['biggest-increase']
    if biggest_increase:
        system = next(iter(biggest_increase.keys()))
        diff = biggest_increase[system]
        percentage_change = round(diff * 100, 1)
        res.append(f"The largest increase in test code ratio was experienced by {system} (+{percentage_change}%).")
    biggest_decrease = stats['test-code-ratio-change']['biggest-decrease']
    if biggest_decrease:
        system = next(iter(biggest_decrease.keys()))
        diff = biggest_decrease[system]
        percentage_change = round(abs(diff) * 100, 1)
        res.append(f"The largest decrease in test code ratio was experienced by {system} (-{percentage_change}%).")
    if res:
        return " ".join(res)
    return ""

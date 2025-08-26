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

from datetime import datetime

from report_generator.generator.constants import MaintMetric
from report_generator.generator.data_models import maintainability_portfolio_data
from report_generator.generator.formatters import smart_remarks
from report_generator.generator.formatters.formatters import calculate_stars, format_diff, maintainability_round
from .base import parameterized_text_placeholder, text_placeholder


def _format_percentage(percentage):
    if percentage < 1:
        percentage = "<1"
    return f"{percentage}%"


def _format_maintainability_statement(amount, number_of_systems, postfix):
    perc = _format_percentage(int(100*(amount)/number_of_systems))
    return f"There {'are' if amount > 1 else 'is'} {amount} ({perc}) {'systems' if amount > 1 else 'system'} that {'score' if amount > 1 else 'scores'} {postfix}."


def _format_short_maintainability_statement(amount, number_of_systems, postfix):
    perc = _format_percentage(int(100*(amount)/number_of_systems))
    return f"About {amount} ({perc}) {'systems' if amount > 1 else 'system'} {'score' if amount > 1 else 'scores'} {postfix}"


def _get_portfolio_stats():
    system_names = maintainability_portfolio_data.system_names
    stats = {'1-star' : 0, '2-star' : 0, '3-star' : 0, '4-star' : 0, '5-star' : 0, 'number-of-systems' : 0}
    for system_name in system_names:
        md = maintainability_portfolio_data.find_system_metadata(system_name)
        if not md['active'] or md['isDevelopmentOnly']:
            continue
        snapshot = maintainability_portfolio_data.end_snapshot(system_name)
        if snapshot['maintainability'] < 1.5:
            stats['1-star'] += 1
        elif snapshot['maintainability'] < 2.5:
            stats['2-star'] += 1
        elif snapshot['maintainability'] < 3.5:
            stats['3-star'] += 1
        elif snapshot['maintainability'] < 4.5:
            stats['4-star'] += 1
        else:
            stats['5-star'] += 1
        stats['number-of-systems'] += 1
    return stats

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
    stats = _get_portfolio_stats()
    res = []
    if stats['5-star'] + stats['4-star'] > 0:
        res.append(_format_maintainability_statement(stats['5-star'] + stats['4-star'], stats['number-of-systems'], "above market average (≥ 4 stars)"))
    if stats['3-star'] > 0:
        res.append(_format_maintainability_statement(stats['3-star'], stats['number-of-systems'], "market average (3 stars)"))
    if stats['2-star'] + stats['1-star'] > 0:
        res.append(_format_maintainability_statement(stats['2-star']+stats['1-star'], stats['number-of-systems'], "below market average (≤ 2 stars)"))
    return "\n".join(res)


@text_placeholder()
def portfolio_period_maint_short_summary():
    """The portfolio maintainability short summary at the period's end date."""
    stats = _get_portfolio_stats()
    processed_stats = {
        'above-market-average' : stats['5-star'] + stats['4-star'],
        'market-average' : stats['3-star'],
        'below-market-average' : stats['2-star'] + stats['1-star']
    }
    postfixes = {
        'above-market-average' : "above market average on maintainability",
        'market-average' : "above market average on maintainability",
        'below-market-average' : "below market average on maintainability"
    }
    key = max(processed_stats, key=processed_stats.get)
    res = _format_short_maintainability_statement(processed_stats[key], stats['number-of-systems'], postfixes[key])
    return res
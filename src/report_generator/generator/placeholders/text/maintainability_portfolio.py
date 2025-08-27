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

from report_generator.generator.data_models import maintainability_portfolio_data
from report_generator.generator.formatters.formatters import calculate_star_rating_integer
from .base import text_placeholder


def _format_percentage(percentage):
    if percentage < 1:
        percentage = "<1"
    return f"{percentage}%"


def _format_maintainability_statement(amount, number_of_systems, postfix):
    perc = _format_percentage(int(100*amount/number_of_systems))
    return f"There {'are' if amount > 1 else 'is'} {amount} ({perc}) {'systems' if amount > 1 else 'system'} that {'score' if amount > 1 else 'scores'} {postfix}."


def _format_short_maintainability_statement(amount, number_of_systems, postfix):
    perc = _format_percentage(int(100*amount/number_of_systems))
    return f"About {amount} ({perc}) {'systems' if amount > 1 else 'system'} {'score' if amount > 1 else 'scores'} {postfix}"


def _get_maintainability_stats(stats):
    system_names = maintainability_portfolio_data.system_names
    stats['maintainability'] = {'1-star' : 0, '2-star' : 0, '3-star' : 0, '4-star' : 0, '5-star' : 0, 'number-of-systems' : 0}
    for system_name in system_names:
        md = maintainability_portfolio_data.find_system_metadata(system_name)
        if not md['active'] or md['isDevelopmentOnly']:
            continue
        star_rating_integer = calculate_star_rating_integer(maintainability_portfolio_data.end_snapshot(system_name)['maintainability'])
        stats['maintainability'][f"{star_rating_integer}-star"] += 1
        stats['maintainability']['number-of-systems'] += 1


def _get_maintainability_change_stats(stats):
    system_names = maintainability_portfolio_data.system_names
    stats['maintainability-change'] = {'increase' : {}, 'decrease' : {}}
    differences = {}
    for system_name in system_names:
        md = maintainability_portfolio_data.find_system_metadata(system_name)
        if not md['active'] or md['isDevelopmentOnly']:
            continue
        start_snapshot = maintainability_portfolio_data.start_snapshot(system_name)
        end_snapshot = maintainability_portfolio_data.end_snapshot(system_name)
        if start_snapshot['maintainabilityDate'] == end_snapshot['maintainabilityDate'] or datetime.strptime(start_snapshot['maintainabilityDate'], "%Y-%m-%d") < datetime.strptime(maintainability_portfolio_data.period[0], "%Y-%m-%d"):
            differences[system_name] = None
        else:
            differences[system_name] = end_snapshot['maintainability']-start_snapshot['maintainability']
    
    largest_decrease_system = min((k for k, v in differences.items() if v is not None), key=differences.get)
    largest_increase_system = max((k for k, v in differences.items() if v is not None), key=differences.get)

    if differences[largest_decrease_system] < 0:
        stats['maintainability-change']['decrease'] = {largest_decrease_system : differences[largest_decrease_system]}
    if differences[largest_increase_system] > 0:
        stats['maintainability-change']['increase'] = {largest_increase_system : differences[largest_increase_system]}


def __get_maintainability_average_stats(stats):
    system_names = maintainability_portfolio_data.system_names
    start_maintainability_ratings = []
    start_volumes = []
    end_maintainability_ratings = []
    end_volumes = []
    for system_name in system_names:
        md = maintainability_portfolio_data.find_system_metadata(system_name)
        if not md['active'] or md['isDevelopmentOnly']:
            continue
        start_snapshot = maintainability_portfolio_data.start_snapshot(system_name)
        end_snapshot = maintainability_portfolio_data.end_snapshot(system_name)
        if datetime.strptime(start_snapshot['maintainabilityDate'], "%Y-%m-%d") < datetime.strptime(maintainability_portfolio_data.period[0], "%Y-%m-%d"):
            start_maintainability_ratings.append(start_snapshot['maintainability'])
            start_volumes.append(start_snapshot['volumeInPersonMonths'])
        end_maintainability_ratings.append(end_snapshot['maintainability'])
        end_volumes.append(end_snapshot['volumeInPersonMonths'])
    stats['maintainability']['start-average'] = sum(x * y for x, y in zip(start_maintainability_ratings, start_volumes)) / sum(start_volumes) 
    stats['maintainability']['end-average'] = sum(x * y for x, y in zip(end_maintainability_ratings, end_volumes)) / sum(end_volumes) 


def _get_portfolio_stats():
    stats = {}
    _get_maintainability_stats(stats)
    _get_maintainability_change_stats(stats)
    __get_maintainability_average_stats(stats)
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
    if stats['maintainability']['5-star'] + stats['maintainability']['4-star'] > 0:
        res.append(_format_maintainability_statement(stats['maintainability']['5-star'] + stats['maintainability']['4-star'], stats['maintainability']['number-of-systems'], "above market average (≥ 4 stars)"))
    if stats['maintainability']['3-star'] > 0:
        res.append(_format_maintainability_statement(stats['maintainability']['3-star'], stats['maintainability']['number-of-systems'], "market average (3 stars)"))
    if stats['maintainability']['2-star'] + stats['maintainability']['1-star'] > 0:
        res.append(_format_maintainability_statement(stats['maintainability']['2-star']+stats['maintainability']['1-star'], stats['maintainability']['number-of-systems'], "below market average (≤ 2 stars)"))
    return "\n".join(res)


@text_placeholder()
def portfolio_period_maint_short_summary():
    """The portfolio maintainability short summary at the period's end date."""
    stats = _get_portfolio_stats()
    processed_stats = {
        'above-market-average' : stats['maintainability']['5-star'] + stats['maintainability']['4-star'],
        'market-average' : stats['maintainability']['3-star'],
        'below-market-average' : stats['maintainability']['2-star'] + stats['maintainability']['1-star']
    }
    postfixes = {
        'above-market-average' : "above market average on maintainability",
        'market-average' : "market average on maintainability",
        'below-market-average' : "below market average on maintainability"
    }
    key = max(processed_stats, key=processed_stats.get)
    res = _format_short_maintainability_statement(processed_stats[key], stats['maintainability']['number-of-systems'], postfixes[key])
    return res


@text_placeholder()
def portfolio_period_maint_change_summary():
    """The portfolio maintainability change summary, given the period's start and end dates."""
    stats = _get_portfolio_stats()
    res = []
    if stats['maintainability-change']['increase']:
        key = next(iter(stats['maintainability-change']['increase']))
        res.append(f"The largest increase in maintainability rating was experienced by {key} ({int(10*stats['maintainability-change']['increase'][key])/10}).")
    if stats['maintainability-change']['decrease']:
        key = next(iter(stats['maintainability-change']['decrease']))
        res.append(f"The largest decrease in maintainability rating was experienced by {key} ({int(10*stats['maintainability-change']['decrease'][key])/10}).")
    if res:
        return "\n".join(res)
    return "The portfolio remained stable during the measured period."


@text_placeholder()
def portfolio_period_maint_change_short_summary():
    """The portfolio maintainability change short summary, given the period's start and end dates."""
    start_avg = int(_get_portfolio_stats()['maintainability']['start-average']*10)/10
    end_avg = int(_get_portfolio_stats()['maintainability']['end-average']*10)/10
    diff = int((end_avg-start_avg)*10)/10
    if abs(diff) < 0.01:
        return f"The portfolio remained stable ({end_avg}) during the measured period"
    return f"The portfolio's maintainability has {'increased' if start_avg<end_avg else 'decreased'} ({diff} to {end_avg}) during the measured period"
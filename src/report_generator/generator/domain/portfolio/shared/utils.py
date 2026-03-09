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

from typing import Callable, Dict, Iterable, Optional, Tuple

from report_generator.generator.context import sigrid_api


def system_names_helper(data, tag):
    return [x[tag] for x in data]


def get_system_helper(system, data, tag):
    for s in data:
        if s[tag] == system:
            return s
    return None


def get_system_metadata(portfolio_metadata, system):
    for s in portfolio_metadata:
        if s['systemName'] == system:
            return s
    return None


def categorize_rating(rating):
    """Categorize a rating into market segments."""
    if rating >= 3.5:
        return 'above_market'
    elif rating >= 2.5:
        return 'market_average'
    else:
        return 'below_market'


def _calculate_percentages(counts, total):
    """Calculate percentages from counts."""
    if total == 0:
        return {'above_market': 0, 'market_average': 0, 'below_market': 0}

    return {
        'above_market'  : round(100 * counts['above_market'] / total),
        'market_average': round(100 * counts['market_average'] / total),
        'below_market'  : round(100 * counts['below_market'] / total)
    }


def is_month_in_period(month: Optional[str], period: Tuple[str, str]) -> bool:
    if not month:
        return False
    period_start, period_end = period

    month_ym = month[:7]
    period_start_ym = period_start[:7]
    period_end_ym = period_end[:7]

    return period_start_ym <= month_ym <= period_end_ym


def get_volume(system_name: str) -> float:
    portfolio_data = sigrid_api.get_portfolio_maintainability()
    systems = portfolio_data.get('systems', []) if isinstance(portfolio_data, dict) else []
    for system in systems:
        if system.get('system') == system_name:
            return system.get('volumeInPersonMonths', 0)
    return 0


def get_rating_and_volume_from_system(
        system: Dict,
        rating_extractor: Callable[[Dict], Optional[float]],
        system_name_key: str = 'systemName'
) -> Tuple[Optional[float], float]:
    rating = rating_extractor(system)
    system_name = system.get(system_name_key)

    if rating is None or system_name is None:
        return None, 0

    volume = get_volume(system_name)
    return rating, volume


def calculate_weighted_average_rating(
        data_source: Iterable,
        get_rating_and_volume_func: Callable[[any], Tuple[Optional[float], float]]
) -> float:
    total_weighted_rating = 0
    total_volume = 0

    for item in data_source:
        rating, volume = get_rating_and_volume_func(item)

        if rating is None or volume == 0:
            continue

        total_weighted_rating += rating * volume
        total_volume += volume

    if total_volume > 0:
        return total_weighted_rating / total_volume
    return 0.0


def get_rating_distribution_percentages(
        data_source: Iterable,
        rating_extractor: Callable[[any], Optional[float]]
) -> Dict[str, int]:
    counts = {'above_market': 0, 'market_average': 0, 'below_market': 0}
    total = 0

    for item in data_source:
        rating = rating_extractor(item)
        if rating is None:
            continue

        category = categorize_rating(rating)
        counts[category] += 1
        total += 1

    return _calculate_percentages(counts, total)

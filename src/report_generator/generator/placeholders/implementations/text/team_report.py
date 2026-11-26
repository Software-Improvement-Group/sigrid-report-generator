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

from report_generator.generator.context.portfolio_filters import get_filter_values
from report_generator.generator.domain import team_report_data
from report_generator.generator.placeholders.formatting.formatters import (
    Sentiment,
    market_average_sentiment,
    star_rating_round,
)

from .base import text_placeholder

_DUTCH_MONTHS = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)


def _dutch_date(date: str) -> str:
    year, month, day = (int(part) for part in date.split("-"))
    return f"{day} {_DUTCH_MONTHS[month - 1]} {year}"


def _stars(rating: float) -> str:
    return star_rating_round(rating) if rating > 0 else ""


def _delta_text(was_rating: float, is_rating: float) -> str:
    """Compare two ratings as shown (truncated to one decimal): Gelijk, Hoger or Lager."""
    if was_rating <= 0 or is_rating <= 0:
        return ""
    was_shown = float(star_rating_round(was_rating))
    is_shown = float(star_rating_round(is_rating))
    if is_shown == was_shown:
        return "Gelijk"
    return "Hoger" if is_shown > was_shown else "Lager"


def _market_text(rating: float) -> str:
    """Compare a rating as shown (truncated to one decimal) with market average: Onder, Op or Boven."""
    if rating <= 0:
        return ""
    return {
        Sentiment.NEGATIVE: "Onder",
        Sentiment.NEUTRAL: "Op",
        Sentiment.POSITIVE: "Boven",
    }[market_average_sentiment(float(star_rating_round(rating)))]


def _objectives_text(feature: str) -> str:
    met = team_report_data.objectives_met(feature)
    if met is None:
        return ""
    return "Ja" if met else "Nee"


@text_placeholder()
def team_name():
    """The name of the team from the filter parameter."""
    teams = get_filter_values("team")
    return teams[0] if teams else "Team"


@text_placeholder()
def team_report_period():
    """The reporting period, e.g. 1 januari 2026 - 11 november 2026."""
    start, end = team_report_data.period
    return f"{_dutch_date(start)} - {_dutch_date(end)}"


def _placeholder(key: str, doc: str, value):
    value.__doc__ = doc
    return text_placeholder(custom_key=key)(value)


def _module_placeholders(
    module: str, label: str, feature: str, rating_at, has_history: bool = True
):
    """The Was, Is, Delta, Markt and Doel placeholders of one row of the team's rating table.

    rating_at(date) is the team's average rating on that date; modules without history
    (has_history=False) always give their current rating, and leave Was and Delta empty.
    """

    def rating_was():
        return rating_at(team_report_data.period[0]) if has_history else 0

    def rating_is():
        return rating_at(team_report_data.period[1])

    def delta():
        was = rating_was()
        return _delta_text(was, rating_is()) if was > 0 else ""

    return {
        _placeholder(
            f"{module}_WAS",
            f"The team's average {label} rating at the start of the period.",
            lambda: _stars(rating_was()),
        ),
        _placeholder(
            f"{module}_IS",
            f"The team's average {label} rating at the end of the period.",
            lambda: _stars(rating_is()),
        ),
        _placeholder(
            f"{module}_DELTA",
            f"Gelijk, Hoger or Lager: the team's {label} rating at the end of the period compared to the start.",
            delta,
        ),
        _placeholder(
            f"{module}_MARKT",
            f"Onder, Op or Boven market average for the team's {label} rating at the end of the period.",
            lambda: _market_text(rating_is()),
        ),
        _placeholder(
            f"{module}_DOEL",
            f"Ja or Nee: the team's {label} objectives are met at the end of the period.",
            lambda: _objectives_text(feature),
        ),
    }


_RATING_TABLE_PLACEHOLDERS = {
    *_module_placeholders(
        "MAINTAINABILITY",
        "maintainability",
        "MAINTAINABILITY",
        lambda date: team_report_data.maintainability_rating(date),
    ),
    *_module_placeholders(
        "ARCHITECTURE",
        "architecture",
        "ARCHITECTURE_QUALITY",
        lambda date: team_report_data.architecture_rating(date),
    ),
    *_module_placeholders(
        "OPEN_SOURCE_HEALTH",
        "open source health",
        "OPEN_SOURCE_HEALTH",
        lambda date: team_report_data.open_source_health_rating,
        has_history=False,
    ),
    *_module_placeholders(
        "SECURITY",
        "security",
        "SECURITY",
        lambda date: team_report_data.security_rating(date),
    ),
}

# Placeholders are found by scanning module attributes, so the generated ones need a name here.
globals().update(
    {placeholder.key.lower(): placeholder for placeholder in _RATING_TABLE_PLACEHOLDERS}
)

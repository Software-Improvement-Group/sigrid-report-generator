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

import logging
import math
import re

from report_generator.generator.utils.constants.sentiment import Sentiment
from report_generator.generator.utils.star_rating import calculate_star_rating_integer

_USE_SIG_STERREN = False


def use_sig_sterren(enabled: bool = True) -> None:
    """
    Enable the use of SIG sterren notation for star ratings.

    This function sets the global flag _USE_SIG_STERREN to True, which causes
    the calculate_stars function to return star ratings using the H/I notation
    (HIIII, HHIII, etc.) instead of the default ★/☆ notation.

    For internal SIG use only.
    """
    global _USE_SIG_STERREN
    _USE_SIG_STERREN = enabled


def calculate_stars(maintainability_rating: float) -> str:
    sig_sterren_ratings = ("HIIII", "HHIII", "HHHII", "HHHHI", "HHHHH")
    star_ratings = ("★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★")

    ratings = sig_sterren_ratings if _USE_SIG_STERREN else star_ratings

    if maintainability_rating < 0.1:
        return ""
    star_rating = calculate_star_rating_integer(maintainability_rating)
    return ratings[star_rating - 1]


def print_star() -> str:
    if _USE_SIG_STERREN:
        return "H"
    return "★"


def maintainability_round(rating) -> str:
    logging.warning(
        "maintainability_round is deprecated and will be removed, use star_rating_round instead"
    )
    return star_rating_round(rating)


def star_rating_round(rating) -> str:
    if isinstance(rating, str):
        rating = float(rating)

    return "N/A" if rating < 0.1 else str(math.floor(rating * 10) / 10)


def ratio_to_percentage(ratio) -> str:
    if isinstance(ratio, str):
        ratio = float(ratio)

    return f"{round(ratio * 100, 1)}%" if ratio < 1 else f"{int(ratio * 100)}%"


def format_diff(old_rating: float, new_rating: float) -> str:
    if not old_rating or not new_rating:
        return ""

    diff = new_rating - old_rating
    if diff >= 0.1:
        return f"+ {diff:.1f}"
    elif diff <= -0.1:
        return f"- {abs(diff):.1f}"
    else:
        return "="


def sentiment_for_range(value: float, neutral_range: tuple[float, float]) -> Sentiment:
    """Classify a value relative to a neutral range: negative below the range,
    positive at/above its upper bound, neutral within the [low, high) band."""
    low, high = neutral_range
    if value < low:
        return Sentiment.NEGATIVE
    if value >= high:
        return Sentiment.POSITIVE
    return Sentiment.NEUTRAL


def delta_sentiment(delta: float) -> Sentiment:
    # Deltas round to 2 decimals; >= 0.01 is an increase, <= -0.01 a decrease.
    return sentiment_for_range(round(delta, 2), (0, 0.01))


def market_average_sentiment(score: float) -> Sentiment:
    return sentiment_for_range(score, (2.5, 3.5))


def format_signed_delta(delta: float) -> str:
    rounded = round(delta, 2)
    sentiment = delta_sentiment(delta)
    if sentiment == Sentiment.POSITIVE:
        return f"+{rounded:.2f}"
    if sentiment == Sentiment.NEGATIVE:
        return f"-{abs(rounded):.2f}"
    return "="


def format_market_average(score: float) -> str:
    """Return whether a star rating is below, at, or above market average as
    'below' (< 2.5), 'average' (2.5 - 3.4) or 'above' (>= 3.5)."""
    return {
        Sentiment.NEGATIVE: "below",
        Sentiment.NEUTRAL: "average",
        Sentiment.POSITIVE: "above",
    }[market_average_sentiment(score)]


def from_json_name(json_name: str) -> str:
    """Convert a camelCase JSON field name to a human-readable label."""
    words = re.sub(r"([A-Z])", r" \1", json_name).strip()
    return words[0].upper() + words[1:]


def split_days_into_buckets(days: list[int], buckets: list[int]) -> list[int]:
    # Sort buckets ascendingly
    buckets = sorted(buckets)

    # Initialize counters (one per bucket, plus one for > last bucket)
    counts = [0] * (len(buckets) + 1)

    # Iterate through each day value and place into bucket
    for value in days:
        placed = False

        for i, b in enumerate(buckets):
            if value < b:
                counts[i] += 1
                placed = True
                break

        # If not placed in any bucket, belongs in > last bucket
        if not placed:
            counts[-1] += 1

    # Prepend total number of values
    return [len(days), *counts]


def format_percentage_excluding_100_percent(percentage: float) -> str:
    if percentage < 0.01:
        return "< 1%"
    if percentage > 0.99:
        return ">99%"
    return f"{percentage:.0%}"


def build_sigrid_link(customer: str, system_name: str, path: str) -> str:
    return f"https://sigrid-says.com/{customer}/{system_name}/-/{path}"

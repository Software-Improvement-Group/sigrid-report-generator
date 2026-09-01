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

import pytest

from report_generator.generator.placeholders.rendering.pptx import colors
from report_generator.generator.utils.constants.sentiment import Sentiment


@pytest.mark.parametrize(
    "rating, expected",
    [
        (0.0, colors.NA_STAR_COLOR),
        (0.09, colors.NA_STAR_COLOR),
        (0.1, colors.ONE_STAR_COLOR),
        (1.49, colors.ONE_STAR_COLOR),
        (1.5, colors.TWO_STAR_COLOR),
        (2.5, colors.THREE_STAR_COLOR),
        (3.5, colors.FOUR_STAR_COLOR),
        (4.49, colors.FOUR_STAR_COLOR),
        (4.5, colors.FIVE_STAR_COLOR),
        (5.5, colors.FIVE_STAR_COLOR),
    ],
)
def test_rating_band_bounds_are_exclusive(rating, expected):
    assert colors.determine_rating_color(rating) == expected


@pytest.mark.parametrize(
    "ratio, expected",
    [
        (0.0, colors.ONE_STAR_COLOR),
        (0.01, colors.ONE_STAR_COLOR),
        (0.011, colors.TWO_STAR_COLOR),
        (0.15, colors.TWO_STAR_COLOR),
        (0.16, colors.THREE_STAR_COLOR),
        (0.5, colors.THREE_STAR_COLOR),
        (0.51, colors.FOUR_STAR_COLOR),
        (1.5, colors.FOUR_STAR_COLOR),
        (1.51, colors.FIVE_STAR_COLOR),
    ],
)
def test_test_code_ratio_band_bounds_are_inclusive(ratio, expected):
    assert colors.test_code_ratio_color(ratio) == expected


def test_sentiment_color_maps_sentiment_to_color():
    assert colors.sentiment_color(Sentiment.POSITIVE) == colors.FIVE_STAR_COLOR
    assert colors.sentiment_color(Sentiment.NEGATIVE) == colors.ONE_STAR_COLOR
    assert colors.sentiment_color(Sentiment.NEUTRAL) == colors.SIG_BLUE_COLOR


def test_interpolate_color_spans_the_whole_ramp():
    ramp = [colors.ONE_STAR_COLOR, colors.FIVE_STAR_COLOR]

    assert colors.interpolate_color(ramp, 0) == colors.ONE_STAR_COLOR
    assert colors.interpolate_color(ramp, 1) == colors.FIVE_STAR_COLOR
    assert colors.interpolate_color(ramp, 1.5) == colors.FIVE_STAR_COLOR


def test_interpolate_color_picks_the_band_the_position_falls_in():
    ramp = [colors.ONE_STAR_COLOR, colors.THREE_STAR_COLOR, colors.FIVE_STAR_COLOR]

    assert colors.interpolate_color(ramp, 0.5) == colors.THREE_STAR_COLOR
    partway = colors.interpolate_color(ramp, 0.75)
    assert colors.THREE_STAR_COLOR[0] > partway[0] > colors.FIVE_STAR_COLOR[0]

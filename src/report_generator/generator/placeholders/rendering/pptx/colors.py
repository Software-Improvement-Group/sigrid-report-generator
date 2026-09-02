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

import bisect

from pptx.dml.color import RGBColor

from report_generator.generator.utils.constants.sentiment import Sentiment

NA_STAR_COLOR = RGBColor(0x91, 0x90, 0x92)
ONE_STAR_COLOR = RGBColor(0xE0, 0x6C, 0x4F)
TWO_STAR_COLOR = RGBColor(0xE8, 0x99, 0x36)
THREE_STAR_COLOR = RGBColor(0xE9, 0xC3, 0x43)
FOUR_STAR_COLOR = RGBColor(0x68, 0xC0, 0x6B)
FIVE_STAR_COLOR = RGBColor(0x3C, 0x88, 0x42)
_STAR_COLORS = (
    ONE_STAR_COLOR,
    TWO_STAR_COLOR,
    THREE_STAR_COLOR,
    FOUR_STAR_COLOR,
    FIVE_STAR_COLOR,
)

SIG_BLUE_COLOR = RGBColor(0x24, 0x35, 0x49)
SIG_GREY_COLOR = RGBColor(0xDF, 0xE2, 0xE7)

RATING_POS_CHANGE_RANGE_COLORS = [RGBColor(0xD9, 0xEE, 0xDD), FIVE_STAR_COLOR]
RATING_NEG_CHANGE_RANGE_COLORS = [RGBColor(0xF3, 0xDD, 0xD7), ONE_STAR_COLOR]
VOLUME_POS_CHANGE_RANGE_COLORS = [
    RGBColor(0xEB, 0xF3, 0xF5),
    RGBColor(0x71, 0xB6, 0xC9),
]
VOLUME_NEG_CHANGE_RANGE_COLORS = [
    RGBColor(0xFA, 0xF1, 0xE1),
    RGBColor(0xE8, 0x99, 0x36),
]

SENTIMENT_COLORS = {
    Sentiment.NEGATIVE: ONE_STAR_COLOR,
    Sentiment.NEUTRAL: SIG_BLUE_COLOR,
    Sentiment.POSITIVE: FIVE_STAR_COLOR,
}

# Exclusive upper bounds: a rating of exactly 1.5 is two stars.
_RATING_BAND_BOUNDS = (0.1, 1.5, 2.5, 3.5, 4.5)
_RATING_BAND_COLORS = (NA_STAR_COLOR, *_STAR_COLORS)

# Inclusive upper bounds: a ratio of exactly 0.15 is two stars.
_TEST_CODE_RATIO_BAND_BOUNDS = (0.01, 0.15, 0.5, 1.5)


def determine_rating_color(rating) -> RGBColor:
    """The star colour of a rating. A rating below 0.1 is shown as not applicable."""
    return _RATING_BAND_COLORS[bisect.bisect_right(_RATING_BAND_BOUNDS, rating)]


def test_code_ratio_color(ratio) -> RGBColor:
    return _STAR_COLORS[bisect.bisect_left(_TEST_CODE_RATIO_BAND_BOUNDS, ratio)]


def sentiment_color(sentiment: Sentiment) -> RGBColor:
    return SENTIMENT_COLORS[sentiment]


def interpolate_color(colors, t) -> RGBColor:
    """The colour at position `t` (0 to 1) along a gradient through `colors`."""
    position = t * (len(colors) - 1)
    lower_index = int(position)
    if lower_index >= len(colors) - 1:
        return colors[-1]

    lower, upper = colors[lower_index], colors[lower_index + 1]
    fraction = position - lower_index
    return RGBColor(
        *(
            int(lower[channel] + (upper[channel] - lower[channel]) * fraction)
            for channel in range(3)
        )
    )

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

from report_generator.generator.placeholders import rendering
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
    EndDatePortfolioTreemapPlaceholder,
    PeriodPortfolioTreemapPlaceholder,
    _PeriodChangeStyle,
)


class TestCodePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the test-to-production code ratio of the individual systems.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""

    key = "PORTFOLIO_PERIOD_TEST_CODE"

    @classmethod
    def value(cls, parameter):
        portfolio = cls.create_portfolio()

        def f(t):
            return portfolio[t]["end_date_data"]["testCodeRatio"]

        return cls.create_end_date_portfolio_treemap(
            grouping=parameter.lower(),
            rating_func=f,
            rating_rounding_func=formatters.ratio_to_percentage,
            determine_color_function=cls.test_code_ratio_color,
        )


class TestCodeChangePortfolioTreemapPlaceholder(PeriodPortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the change in test code volume change (%) of the individual systems during the specified period.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""

    key = "PORTFOLIO_PERIOD_TEST_CODE_CHANGE"

    @classmethod
    def value(cls, parameter):
        return cls.create_period_portfolio_treemap(
            grouping=parameter.lower(),
            metric="testCodeRatio",
            style=_PeriodChangeStyle(
                rendering.pptx.RATING_POS_CHANGE_RANGE_COLORS,
                rendering.pptx.RATING_NEG_CHANGE_RANGE_COLORS,
                is_percentage=True,
            ),
        )

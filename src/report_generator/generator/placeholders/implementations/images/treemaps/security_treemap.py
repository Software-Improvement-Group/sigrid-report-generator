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

from report_generator.generator.domain import (
    security_ratings_portfolio_data,
)
from report_generator.generator.placeholders import rendering
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
    EndDatePortfolioTreemapPlaceholder,
    PeriodPortfolioTreemapPlaceholder,
    _PeriodChangeStyle,
)


class SecurityRatingsPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the security rating of the individual systems.
    Leave parameter empty to apply the default/provided grouping."""

    key = "PORTFOLIO_PERIOD_SECURITY_RATINGS{parameter}"

    @classmethod
    def value(cls, parameter):
        return cls.create_end_date_portfolio_treemap(
            grouping=cls._dimension_from_parameter(parameter).lower(),
            rating_func=cls.safe_rating_func(
                security_ratings_portfolio_data.get_system, "rating"
            ),
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )


class SecurityRatingsChangePortfolioTreemapPlaceholder(
    PeriodPortfolioTreemapPlaceholder
):
    """Creates a portfolio treemap where the color is determined by the change in security rating of the individual systems during the specified period.
    Leave parameter empty to apply the default/provided grouping."""

    key = "PORTFOLIO_PERIOD_SECURITY_RATINGS_CHANGE{parameter}"

    @classmethod
    def value(cls, parameter):
        return cls.create_period_portfolio_treemap_from_differences(
            grouping=cls._dimension_from_parameter(parameter).lower(),
            difference_provider=security_ratings_portfolio_data.get_difference,
            style=_PeriodChangeStyle(
                rendering.pptx.RATING_POS_CHANGE_RANGE_COLORS,
                rendering.pptx.RATING_NEG_CHANGE_RANGE_COLORS,
            ),
        )

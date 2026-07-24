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
    architecture_portfolio_data,
)
from report_generator.generator.placeholders import rendering
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
    EndDatePortfolioTreemapPlaceholder,
    PeriodPortfolioTreemapPlaceholder,
    _PeriodChangeStyle,
)


class ArchitecturePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the architecture quality rating of the individual systems."""

    key = "PORTFOLIO_PERIOD_ARCHITECTURE_GROUPED_BY_{parameter}"

    @classmethod
    def value(cls, parameter):
        def f(t):
            return (
                architecture_portfolio_data.get_system(t)["ratings"]["architecture"]
                if architecture_portfolio_data.get_system(t)
                else 0
            )

        return cls.create_end_date_portfolio_treemap(
            grouping=parameter.lower(),
            rating_func=f,
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )


class ArchitectureRatingsChangePortfolioTreemapPlaceholder(
    PeriodPortfolioTreemapPlaceholder
):
    """Creates a portfolio treemap where the color is determined by the change in architecture quality rating of the individual systems during the specified period."""

    key = "PORTFOLIO_PERIOD_ARCHITECTURE_RATINGS_CHANGE_GROUPED_BY_{parameter}"

    @classmethod
    def value(cls, parameter):
        return cls.create_period_portfolio_treemap_from_differences(
            grouping=parameter.lower(),
            difference_provider=architecture_portfolio_data.get_difference,
            style=_PeriodChangeStyle(
                rendering.pptx.RATING_POS_CHANGE_RANGE_COLORS,
                rendering.pptx.RATING_NEG_CHANGE_RANGE_COLORS,
            ),
        )

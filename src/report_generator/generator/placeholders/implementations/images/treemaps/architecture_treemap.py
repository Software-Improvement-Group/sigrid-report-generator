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
    MultiParameterList,
    PeriodPortfolioTreemapPlaceholder,
    _PeriodChangeStyle,
)
from report_generator.generator.utils.constants import ArchMetric


class ArchitecturePortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the architecture quality rating of the individual systems.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""
    key = "PORTFOLIO_PERIOD_ARCHITECTURE"

    @classmethod
    def value(cls, parameter):
        return cls.create_end_date_portfolio_treemap(
            grouping=parameter.lower(),
            rating_func=cls.safe_rating_func(
                architecture_portfolio_data.get_system, "ratings", "architecture"
            ),
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )


class ArchitectureRatingsChangePortfolioTreemapPlaceholder(
    PeriodPortfolioTreemapPlaceholder
):
    """Creates a portfolio treemap where the color is determined by the change in architecture quality rating of the individual systems during the specified period.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""

    key = "PORTFOLIO_PERIOD_ARCHITECTURE_RATINGS_CHANGE"

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


class ArchitectureMetricPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the rating of a
    single architecture metric (e.g. component coupling) of the individual systems.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""

    key = "PORTFOLIO_PERIOD_ARCH_{parameter}"
    allowed_parameters = MultiParameterList(ArchMetric)

    @classmethod
    def value(cls, metric, grouping):
        metric_key = metric.to_json_name()

        def f(t):
            return architecture_portfolio_data.get_property_rating(t, metric_key)

        return cls.create_end_date_portfolio_treemap(
            grouping=grouping.lower(),
            rating_func=f,
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )


class ArchitectureMetricChangePortfolioTreemapPlaceholder(
    PeriodPortfolioTreemapPlaceholder
):
    """Creates a portfolio treemap where the color is determined by the change in the
    rating of a single architecture metric (e.g. component coupling) of the
    individual systems during the specified period.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""

    key = "PORTFOLIO_PERIOD_ARCH_{parameter}_RATINGS_CHANGE"
    allowed_parameters = MultiParameterList(ArchMetric)

    @classmethod
    def value(cls, metric, grouping):
        metric_key = metric.to_json_name()

        def difference_provider(system_name):
            return architecture_portfolio_data.get_property_difference(
                system_name, metric_key
            )

        return cls.create_period_portfolio_treemap_from_differences(
            grouping=grouping.lower(),
            difference_provider=difference_provider,
            style=_PeriodChangeStyle(
                rendering.pptx.RATING_POS_CHANGE_RANGE_COLORS,
                rendering.pptx.RATING_NEG_CHANGE_RANGE_COLORS,
            ),
        )

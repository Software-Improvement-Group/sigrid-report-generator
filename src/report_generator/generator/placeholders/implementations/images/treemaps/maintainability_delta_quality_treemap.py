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
    maintainability_delta_quality_changed_code,
    maintainability_delta_quality_new_and_changed_code,
    maintainability_delta_quality_new_code,
)
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
    EndDatePortfolioTreemapPlaceholder,
)


class MaintainabilityDeltaQualityNewCodePortfolioTreemapPlaceholder(
    EndDatePortfolioTreemapPlaceholder
):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (new code) of the individual systems."""

    key = (
        "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_NEW_CODE_GROUPED_BY_{parameter}"
    )

    @classmethod
    def value(cls, parameter):
        def f(t):
            return (
                maintainability_delta_quality_new_code.data[t]["filesRatingAtEnd"]
                if maintainability_delta_quality_new_code.data[t]
                and maintainability_delta_quality_new_code.data[t]["filesRatingAtEnd"]
                else 0
            )

        return cls.create_end_date_portfolio_treemap(
            grouping=parameter.lower(),
            rating_func=f,
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )


class MaintainabilityDeltaQualityChangedCodePortfolioTreemapPlaceholder(
    EndDatePortfolioTreemapPlaceholder
):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (changed code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_CHANGED_CODE_GROUPED_BY_{parameter}"

    @classmethod
    def value(cls, parameter):
        def f(t):
            return (
                maintainability_delta_quality_changed_code.data[t]["filesRatingAtEnd"]
                if maintainability_delta_quality_changed_code.data[t]
                and maintainability_delta_quality_changed_code.data[t][
                    "filesRatingAtEnd"
                ]
                else 0
            )

        return cls.create_end_date_portfolio_treemap(
            grouping=parameter.lower(),
            rating_func=f,
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )


class MaintainabilityDeltaQualityNewAndChangedCodePortfolioTreemapPlaceholder(
    EndDatePortfolioTreemapPlaceholder
):
    """Creates a portfolio treemap where the color is determined by the delta quality of maintainability rating (new and changed code) of the individual systems."""

    key = "PORTFOLIO_PERIOD_MAINTAINABILITY_DELTA_QUALITY_NEW_AND_CHANGED_CODE_GROUPED_BY_{parameter}"

    @classmethod
    def value(cls, parameter):
        def f(t):
            return (
                maintainability_delta_quality_new_and_changed_code.data[t][
                    "filesRatingAtEnd"
                ]
                if maintainability_delta_quality_new_and_changed_code.data[t]
                and maintainability_delta_quality_new_and_changed_code.data[t][
                    "filesRatingAtEnd"
                ]
                else 0
            )

        return cls.create_end_date_portfolio_treemap(
            grouping=parameter.lower(),
            rating_func=f,
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )

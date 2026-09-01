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
    osh_portfolio_data,
)
from report_generator.generator.placeholders.formatting import formatters
from report_generator.generator.placeholders.implementations.images.treemaps.treemap_base import (
    EndDatePortfolioTreemapPlaceholder,
    MultiParameterList,
)
from report_generator.generator.utils.constants import OSHMetric


class OSHRatingsPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the open-source health rating of the individual systems.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""

    key = "PORTFOLIO_PERIOD_OSH_RATINGS"

    @classmethod
    def value(cls, parameter):
        def rating_function(system_name):
            system = osh_portfolio_data.find_system(system_name)
            props = system.get("sbom", {}).get("metadata", {}).get("properties", [])
            return next(
                (
                    float(p["value"])
                    for p in props
                    if p["name"] == "sigrid:ratings:system"
                ),
                0.0,
            )

        return cls.create_end_date_portfolio_treemap(
            grouping=parameter.lower(),
            rating_func=rating_function,
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )


class OSHMetricPortfolioTreemapPlaceholder(EndDatePortfolioTreemapPlaceholder):
    """Creates a portfolio treemap where the color is determined by the rating of a
    single open-source health metric (e.g. vulnerability) of the individual systems.
    Append `_GROUPED_BY_<DIMENSION>` to this placeholder's key to override the report's default grouping for this instance."""

    key = "PORTFOLIO_PERIOD_OSH_{parameter}"
    allowed_parameters = MultiParameterList(OSHMetric)

    @classmethod
    def value(cls, metric, grouping):
        metric_key = metric.to_json_name()

        def rating_function(system_name):
            return osh_portfolio_data.get_property_rating(system_name, metric_key)

        return cls.create_end_date_portfolio_treemap(
            grouping=grouping.lower(),
            rating_func=rating_function,
            rating_rounding_func=formatters.star_rating_round,
            determine_color_function=cls.determine_rating_color,
        )

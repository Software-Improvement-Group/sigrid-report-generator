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

from report_generator.generator.domain import architecture_portfolio_data
from report_generator.generator.formatters.formatters import star_rating_round
from .base import text_placeholder


@text_placeholder()
def portfolio_arch_above_market():
    """Percentage of systems scoring above market average (≥3.5 stars) on architecture quality."""
    distribution = architecture_portfolio_data.get_rating_distribution_percentages
    return distribution['above_market']


@text_placeholder()
def portfolio_arch_market_average():
    """Percentage of systems scoring market average (2.5-3.5 stars) on architecture quality."""
    distribution = architecture_portfolio_data.get_rating_distribution_percentages
    return distribution['market_average']


@text_placeholder()
def portfolio_arch_below_market():
    """Percentage of systems scoring below market average (<2.5 stars) on architecture quality."""
    distribution = architecture_portfolio_data.get_rating_distribution_percentages
    return distribution['below_market']


@text_placeholder()
def portfolio_arch_avg_rating():
    """Volume-weighted average architecture rating across all systems in the portfolio."""
    return star_rating_round(architecture_portfolio_data.weighted_average_rating)

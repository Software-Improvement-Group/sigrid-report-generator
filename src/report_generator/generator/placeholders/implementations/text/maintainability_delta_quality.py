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

from report_generator.generator.domain.portfolio.maintainability_delta_quality_portfolio import (
    maintainability_delta_quality_new_code,
)
from report_generator.generator.placeholders.formatting.formatters import (
    star_rating_round,
)

from .base import text_placeholder


@text_placeholder()
def portfolio_new_code_biggest_changes():
    """Descriptive summary of the biggest maintainability changes in the portfolio."""
    stats = maintainability_delta_quality_new_code.statistics
    res = []
    highest_system = stats["highest_system"]
    if highest_system:
        rating_str = star_rating_round(highest_system[1])
        res.append(
            f"The highest maintainability rating for new code was achieved by {highest_system[0]} ({rating_str} stars)."
        )
    lowest_system = stats["lowest_system"]
    if lowest_system:
        rating_str = star_rating_round(lowest_system[1])
        res.append(
            f"The lowest maintainability rating for new code was in {lowest_system[0]} ({rating_str} stars)."
        )
    if res:
        return " ".join(res)
    return ""

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

from report_generator.generator.domain.portfolio.osh_portfolio import (
    osh_portfolio_data,
)
from report_generator.generator.placeholders.implementations.text.osh_portfolio import (
    portfolio_osh_above_market_param,
    portfolio_osh_avg_rating_param,
    portfolio_osh_below_market_param,
    portfolio_osh_market_average_param,
)
from report_generator.generator.utils.constants import OSHMetric


def test_avg_rating_param_key_is_metric_specific():
    assert (
        portfolio_osh_avg_rating_param.key.format(parameter=OSHMetric.VULNERABILITY)
        == "PORTFOLIO_OSH_AVG_RATING_VULNERABILITY"
    )


def test_avg_rating_param_uses_weighted_average_for_that_metric(monkeypatch):
    monkeypatch.setattr(
        osh_portfolio_data,
        "weighted_average_rating_for_metric",
        lambda metric_key: 4.0 if metric_key == "vulnerability" else 1.0,
    )

    assert portfolio_osh_avg_rating_param.value(OSHMetric.VULNERABILITY) == "4.0"


def test_market_distribution_params_use_that_metrics_distribution(monkeypatch):
    monkeypatch.setattr(
        osh_portfolio_data,
        "rating_distribution_percentages_for_metric",
        lambda metric_key: {
            "above_market": 70,
            "market_average": 20,
            "below_market": 10,
        },
    )

    assert portfolio_osh_above_market_param.value(OSHMetric.LICENSES) == 70
    assert portfolio_osh_market_average_param.value(OSHMetric.LICENSES) == 20
    assert portfolio_osh_below_market_param.value(OSHMetric.LICENSES) == 10

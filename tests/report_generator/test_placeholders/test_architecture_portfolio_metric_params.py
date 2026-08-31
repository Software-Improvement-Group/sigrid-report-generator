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

from report_generator.generator.domain.portfolio.architecture_portfolio import (
    architecture_portfolio_data,
)
from report_generator.generator.placeholders.implementations.text.architecture_portfolio import (
    portfolio_arch_above_market_param,
    portfolio_arch_avg_rating_param,
    portfolio_arch_below_market_param,
    portfolio_arch_biggest_changes_param,
    portfolio_arch_decreased_param,
    portfolio_arch_increased_param,
    portfolio_arch_market_average_param,
    portfolio_arch_stable_param,
)
from report_generator.generator.utils.constants import ArchMetric


def test_avg_rating_param_key_is_metric_specific():
    assert (
        portfolio_arch_avg_rating_param.key.format(parameter=ArchMetric.CODE_REUSE)
        == "PORTFOLIO_ARCH_AVG_RATING_CODE_REUSE"
    )


def test_avg_rating_param_uses_weighted_average_for_that_metric(monkeypatch):
    monkeypatch.setattr(
        architecture_portfolio_data,
        "weighted_average_rating_for_metric",
        lambda metric_key: 4.0 if metric_key == "codeReuse" else 1.0,
    )

    assert portfolio_arch_avg_rating_param.value(ArchMetric.CODE_REUSE) == "4.0"


def test_market_distribution_params_use_that_metrics_distribution(monkeypatch):
    monkeypatch.setattr(
        architecture_portfolio_data,
        "rating_distribution_percentages_for_metric",
        lambda metric_key: {
            "above_market": 70,
            "market_average": 20,
            "below_market": 10,
        },
    )

    assert portfolio_arch_above_market_param.value(ArchMetric.COMPONENT_COUPLING) == 70
    assert (
        portfolio_arch_market_average_param.value(ArchMetric.COMPONENT_COUPLING) == 20
    )
    assert portfolio_arch_below_market_param.value(ArchMetric.COMPONENT_COUPLING) == 10


def test_change_percentage_params_are_computed_per_metric(monkeypatch):
    monkeypatch.setattr(
        architecture_portfolio_data,
        "change_distribution_percentages_for_metric",
        lambda metric_key: {"increased": 30, "stable": 10, "decreased": 60},
    )

    assert portfolio_arch_increased_param.value(ArchMetric.CODE_BREAKDOWN) == 30
    assert portfolio_arch_stable_param.value(ArchMetric.CODE_BREAKDOWN) == 10
    assert portfolio_arch_decreased_param.value(ArchMetric.CODE_BREAKDOWN) == 60


def test_biggest_changes_param_describes_both_directions(monkeypatch):
    monkeypatch.setattr(
        architecture_portfolio_data,
        "biggest_increase_for_metric",
        lambda metric_key: ("Display sys-a", 1.2),
    )
    monkeypatch.setattr(
        architecture_portfolio_data,
        "biggest_decrease_for_metric",
        lambda metric_key: ("Display sys-b", -0.7),
    )

    result = portfolio_arch_biggest_changes_param.value(ArchMetric.CODE_REUSE)

    assert (
        "The largest increase in Code Reuse rating was experienced by Display sys-a (1.2 stars)."
        in result
    )
    assert (
        "The largest decrease in Code Reuse rating was experienced by Display sys-b (-0.7 stars)."
        in result
    )


def test_biggest_changes_param_returns_empty_string_when_no_changes(monkeypatch):
    monkeypatch.setattr(
        architecture_portfolio_data,
        "biggest_increase_for_metric",
        lambda metric_key: None,
    )
    monkeypatch.setattr(
        architecture_portfolio_data,
        "biggest_decrease_for_metric",
        lambda metric_key: None,
    )

    assert portfolio_arch_biggest_changes_param.value(ArchMetric.CODE_REUSE) == ""

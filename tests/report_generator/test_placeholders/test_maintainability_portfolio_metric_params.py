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

import pytest

from report_generator.generator.domain.portfolio.maintainability_portfolio import (
    maintainability_portfolio_data,
)
from report_generator.generator.domain.portfolio.maintainability_portfolio.statistics import (
    maintainability_portfolio_stats,
)
from report_generator.generator.placeholders.implementations.text.maintainability_portfolio import (
    portfolio_maint_above_market_param,
    portfolio_maint_avg_rating_param,
    portfolio_maint_below_market_param,
    portfolio_maint_biggest_changes_param,
    portfolio_maint_decreased_param,
    portfolio_maint_increased_param,
    portfolio_maint_market_average_param,
    portfolio_maint_stable_param,
)
from report_generator.generator.utils.constants import MaintMetric


@pytest.fixture
def prime_metric_change_bucket():
    """Prime the portfolio stats singleton's cache with a fixed metric-change bucket."""

    def _prime(metric: MaintMetric, bucket: dict):
        maintainability_portfolio_stats.__dict__["statistics"] = {
            "metric-changes": {metric.to_json_name(): bucket}
        }

    yield _prime

    maintainability_portfolio_stats.__dict__.pop("statistics", None)


def test_avg_rating_param_key_is_metric_specific():
    assert (
        portfolio_maint_avg_rating_param.key.format(parameter=MaintMetric.VOLUME)
        == "PORTFOLIO_MAINT_AVG_RATING_VOLUME"
    )


def test_avg_rating_param_uses_weighted_average_for_that_metric(monkeypatch):
    monkeypatch.setattr(
        maintainability_portfolio_data,
        "weighted_average_rating_for_metric",
        lambda metric_key: 4.0 if metric_key == "unitComplexity" else 1.0,
    )

    assert portfolio_maint_avg_rating_param.value(MaintMetric.UNIT_COMPLEXITY) == "4.0"


def test_market_distribution_params_use_that_metrics_distribution(monkeypatch):
    monkeypatch.setattr(
        maintainability_portfolio_data,
        "rating_distribution_percentages_for_metric",
        lambda metric_key: {
            "above_market": 70,
            "market_average": 20,
            "below_market": 10,
        },
    )

    assert portfolio_maint_above_market_param.value(MaintMetric.DUPLICATION) == 70
    assert portfolio_maint_market_average_param.value(MaintMetric.DUPLICATION) == 20
    assert portfolio_maint_below_market_param.value(MaintMetric.DUPLICATION) == 10


def test_change_percentage_params_are_computed_per_metric(prime_metric_change_bucket):
    prime_metric_change_bucket(
        MaintMetric.VOLUME,
        {
            "systems-increased": 3,
            "systems-stable": 1,
            "systems-decreased": 6,
            "biggest-increase": {},
            "biggest-decrease": {},
        },
    )

    assert portfolio_maint_increased_param.value(MaintMetric.VOLUME) == 30
    assert portfolio_maint_stable_param.value(MaintMetric.VOLUME) == 10
    assert portfolio_maint_decreased_param.value(MaintMetric.VOLUME) == 60


def test_change_percentage_params_return_zero_when_no_systems(
    prime_metric_change_bucket,
):
    prime_metric_change_bucket(
        MaintMetric.VOLUME,
        {
            "systems-increased": 0,
            "systems-stable": 0,
            "systems-decreased": 0,
            "biggest-increase": {},
            "biggest-decrease": {},
        },
    )

    assert portfolio_maint_increased_param.value(MaintMetric.VOLUME) == 0
    assert portfolio_maint_stable_param.value(MaintMetric.VOLUME) == 0
    assert portfolio_maint_decreased_param.value(MaintMetric.VOLUME) == 0


def test_biggest_changes_param_describes_both_directions(
    prime_metric_change_bucket, monkeypatch
):
    monkeypatch.setattr(
        maintainability_portfolio_data,
        "get_system_display_name",
        lambda system_name: f"Display {system_name}",
    )
    prime_metric_change_bucket(
        MaintMetric.UNIT_SIZE,
        {
            "systems-increased": 0,
            "systems-stable": 0,
            "systems-decreased": 0,
            "biggest-increase": {"sys-a": 1.2},
            "biggest-decrease": {"sys-b": -0.7},
        },
    )

    result = portfolio_maint_biggest_changes_param.value(MaintMetric.UNIT_SIZE)

    assert (
        "The largest increase in Unit Size rating was experienced by Display sys-a (1.2 stars)."
        in result
    )
    assert (
        "The largest decrease in Unit Size rating was experienced by Display sys-b (-0.7 stars)."
        in result
    )


def test_biggest_changes_param_returns_empty_string_when_no_changes(
    prime_metric_change_bucket,
):
    prime_metric_change_bucket(
        MaintMetric.UNIT_SIZE,
        {
            "systems-increased": 0,
            "systems-stable": 0,
            "systems-decreased": 0,
            "biggest-increase": {},
            "biggest-decrease": {},
        },
    )

    assert portfolio_maint_biggest_changes_param.value(MaintMetric.UNIT_SIZE) == ""

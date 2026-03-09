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

from datetime import datetime
from functools import cached_property
from typing import Optional

from report_generator.generator.context import sigrid_api
from report_generator.generator.context.portfolio_filters import (
    filter_data_on_portfolio_arguments,
)
from report_generator.generator.domain.portfolio.shared.rated_mixin import RatedPortfolioMixin
from report_generator.generator.domain.portfolio.shared import utils
from report_generator.generator.utils.star_rating import calculate_star_rating_integer


def _categorize_test_code_ratio(ratio):
    """Categorize test code ratio into low/medium/high."""
    if ratio < 0.5:
        return "low"
    elif ratio < 1.0:
        return "medium"
    else:  # >= 1.0
        return "high"


def _initialize_statistics():
    return {
        "maintainability": {
            "1-star": 0,
            "2-star": 0,
            "3-star": 0,
            "4-star": 0,
            "5-star": 0,
            "number-of-systems": 0,
        },
        "maintainability-change": {
            "systems-increased": 0,
            "systems-stable": 0,
            "systems-decreased": 0,
            "biggest-increase": {},
            "biggest-decrease": {},
        },
        "volume-change": {
            "total-start": 0,
            "total-end": 0,
            "biggest-change-system": None,
            "biggest-change-amount": 0,
        },
        "test-code-ratio-change": {
            "total-start": 0,
            "total-end": 0,
            "systems-increased": 0,
            "systems-stable": 0,
            "systems-decreased": 0,
            "biggest-increase": {},
            "biggest-decrease": {},
        },
    }


def _is_system_active(metadata):
    return metadata["active"] and not metadata["isDevelopmentOnly"]


def _update_star_statistics(statistics, end_snapshot):
    star_rating_integer = calculate_star_rating_integer(end_snapshot["maintainability"])
    statistics["maintainability"][f"{star_rating_integer}-star"] += 1
    statistics["maintainability"]["number-of-systems"] += 1


def _update_best_changes(
    system_name,
    start_snapshot,
    end_snapshot,
    start_date,
    end_date,
    period_start,
    best_inc,
    best_dec,
):
    diff = 0
    if start_date != end_date and start_date >= period_start:
        diff = end_snapshot["maintainability"] - start_snapshot["maintainability"]
        if diff > best_inc[1]:
            best_inc = (system_name, diff)
        if diff < best_dec[1]:
            best_dec = (system_name, diff)
    return best_inc, best_dec, diff


def _collect_averages_data(
    start_snapshot,
    end_snapshot,
    start_date,
    period_start,
    start_maintainability_ratings,
    end_maintainability_ratings,
    start_volumes,
    end_volumes,
):
    if start_date < period_start:
        start_maintainability_ratings.append(start_snapshot["maintainability"])
        start_volumes.append(start_snapshot["volumeInPersonMonths"])
    end_maintainability_ratings.append(end_snapshot["maintainability"])
    end_volumes.append(end_snapshot["volumeInPersonMonths"])


def _update_volume_change(statistics, system_name, start_snapshot, end_snapshot):
    """Track volume changes across the portfolio."""
    start_volume = start_snapshot.get("volumeInPersonMonths", 0)
    end_volume = end_snapshot.get("volumeInPersonMonths", 0)

    statistics["volume-change"]["total-start"] += start_volume
    statistics["volume-change"]["total-end"] += end_volume

    volume_change = end_volume - start_volume
    if abs(volume_change) > abs(statistics["volume-change"]["biggest-change-amount"]):
        statistics["volume-change"]["biggest-change-system"] = system_name
        statistics["volume-change"]["biggest-change-amount"] = volume_change


def _get_test_code_ratios(start_snapshot, end_snapshot):
    """Extract test code ratios from snapshots."""
    return start_snapshot.get("testCodeRatio"), end_snapshot.get("testCodeRatio")


def _accumulate_test_code_totals(statistics, start_ratio, end_ratio):
    """Add ratios to running totals."""
    statistics["test-code-ratio-change"]["total-start"] += start_ratio
    statistics["test-code-ratio-change"]["total-end"] += end_ratio


def _track_test_code_change_direction(statistics, diff):
    """Count systems by change direction."""
    if diff > 0.01:
        statistics["test-code-ratio-change"]["systems-increased"] += 1
    elif diff < -0.01:
        statistics["test-code-ratio-change"]["systems-decreased"] += 1
    else:
        statistics["test-code-ratio-change"]["systems-stable"] += 1


def _update_biggest_changes(statistics, system_name, diff):
    """Track systems with largest increases and decreases."""
    if diff > 0.01:
        biggest = statistics["test-code-ratio-change"]["biggest-increase"]
        if not biggest or diff > next(iter(biggest.values())):
            statistics["test-code-ratio-change"]["biggest-increase"] = {
                system_name: diff
            }
    elif diff < -0.01:
        biggest = statistics["test-code-ratio-change"]["biggest-decrease"]
        if not biggest or diff < next(iter(biggest.values())):
            statistics["test-code-ratio-change"]["biggest-decrease"] = {
                system_name: diff
            }


def _update_test_code_ratio_change(
    statistics, system_name, start_snapshot, end_snapshot, start_date, end_date
):
    """Track test code ratio changes across the portfolio."""
    start_ratio, end_ratio = _get_test_code_ratios(start_snapshot, end_snapshot)

    if start_ratio is None or end_ratio is None:
        return

    _accumulate_test_code_totals(statistics, start_ratio, end_ratio)

    if start_date != end_date:
        diff = end_ratio - start_ratio
        _track_test_code_change_direction(statistics, diff)
        _update_biggest_changes(statistics, system_name, diff)


def _finalize_change_statistics(statistics, best_inc, best_dec):
    if best_dec[0] is not None and best_dec[1] < 0:
        statistics["maintainability-change"]["biggest-decrease"] = {
            best_dec[0]: int(best_dec[1] * 10) / 10
        }
    if best_inc[0] is not None and best_inc[1] > 0:
        statistics["maintainability-change"]["biggest-increase"] = {
            best_inc[0]: int(best_inc[1] * 10) / 10
        }


def _update_change_count(statistics, diff):
    if diff > 0:
        statistics["maintainability-change"]["systems-increased"] += 1
    elif diff < 0:
        statistics["maintainability-change"]["systems-decreased"] += 1
    else:
        statistics["maintainability-change"]["systems-stable"] += 1


def _calculate_averages(
    statistics,
    start_maintainability_ratings,
    end_maintainability_ratings,
    start_volumes,
    end_volumes,
):
    statistics["maintainability"]["start-average"] = _weighted_avg(
        start_maintainability_ratings, start_volumes
    )
    statistics["maintainability"]["end-average"] = _weighted_avg(
        end_maintainability_ratings, end_volumes
    )


def _weighted_avg(values, weights):
    tw = sum(weights)
    return (sum(v * w for v, w in zip(values, weights)) / tw) if tw else 0.000001


def _parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


class MaintainabilityPortfolioData(RatedPortfolioMixin):
    @cached_property
    def metadata(self):
        return sigrid_api.get_portfolio_metadata()

    @property
    def period(self):
        return sigrid_api.get_period()

    @cached_property
    @filter_data_on_portfolio_arguments(data_tag="systems", system_tag="system")
    def data(self):
        data = sigrid_api.get_portfolio_maintainability()
        filtered_data = data
        filtered_data["systems"] = [
            system for system in data["systems"] if "maintainability" in system
        ]
        return filtered_data

    @cached_property
    def system_names(self):
        return utils.system_names_helper(self.data["systems"], "system")

    def get_system(self, system):
        return utils.get_system_helper(system, self.data["systems"], "system")

    def get_system_metadata(self, system_name):
        return utils.get_system_metadata(self.metadata, system_name)

    @staticmethod
    def _get_head_entry(system):
        return {
            "maintainability": system["maintainability"],
            "componentBalance": system["componentBalance"],
            "componentIndependence": system["componentIndependence"],
            "componentEntanglement": system["componentEntanglement"],
            "duplication": system["duplication"],
            "moduleCoupling": system["moduleCoupling"],
            "testCodeRatio": system["testCodeRatio"],
            "unitComplexity": system["unitComplexity"],
            "unitInterfacing": system["unitInterfacing"],
            "unitSize": system["unitSize"],
            "volume": system["volume"],
            "volumeInPersonMonths": system["volumeInPersonMonths"],
            "volumeInLoc": system["volumeInLoc"],
            "maintainabilityDate": system["maintainabilityDate"],
        }

    @staticmethod
    def _get_snapshot_closest_to_date(date, snapshots):
        input_dt = datetime.strptime(date, "%Y-%m-%d")
        return min(
            snapshots,
            key=lambda x: abs(
                datetime.strptime(x["maintainabilityDate"], "%Y-%m-%d") - input_dt
            ),
        )

    @staticmethod
    def _return_closest_date(prime_date, date1, date2):
        input_dt = datetime.strptime(prime_date, "%Y-%m-%d")
        abs_date_1 = abs(
            datetime.strptime(date1["maintainabilityDate"], "%Y-%m-%d") - input_dt
        )
        abs_date_2 = abs(
            datetime.strptime(date2["maintainabilityDate"], "%Y-%m-%d") - input_dt
        )
        if abs_date_1 < abs_date_2:
            return date1
        else:
            return date2

    def get_closest_snapshot(self, system, snapshot_date, ignore_head_entry=False):
        s = self.get_system(system)
        head_entry = MaintainabilityPortfolioData._get_head_entry(s)
        if not s["allRatings"]:
            return head_entry
        snapshot = MaintainabilityPortfolioData._get_snapshot_closest_to_date(
            snapshot_date, s["allRatings"]
        )
        if ignore_head_entry:
            return snapshot
        snapshot = MaintainabilityPortfolioData._return_closest_date(
            snapshot_date, snapshot, head_entry
        )
        return snapshot

    def start_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[0], ignore_head_entry=True)

    def end_snapshot(self, system):
        return self.get_closest_snapshot(system, self.period[1])

    @cached_property
    def statistics(self):
        """
        Calculate comprehensive maintainability statistics for the portfolio.

        Returns:
            dict: A dictionary containing:
                - 'maintainability': Star rating distribution and averages
                    - '1-star' through '5-star': Count of systems in each rating category
                    - 'number-of-systems': Total number of active systems
                    - 'start-average': Volume-weighted average rating at period start
                    - 'end-average': Volume-weighted average rating at period end
                - 'maintainability-change': Best performing systems
                    - 'systems-increased': Count of systems with increased ratings
                    - 'systems-stable': Count of systems with stable ratings
                    - 'systems-decreased': Count of systems with decreased ratings
                    - 'biggest-increase': Dict with system name and largest positive change
                    - 'biggest-decrease': Dict with system name and largest negative change
        """
        statistics = _initialize_statistics()
        period_start = _parse_date(self.period[0])

        best_inc: tuple[Optional[str], float] = (None, float("-inf"))
        best_dec: tuple[Optional[str], float] = (None, float("inf"))
        start_maintainability_ratings, end_maintainability_ratings = [], []
        start_volumes, end_volumes = [], []

        for system_name in self.system_names:
            md = utils.get_system_metadata(self.metadata, system_name)
            if not _is_system_active(md):
                continue

            start_snapshot = self.start_snapshot(system_name)
            end_snapshot = self.end_snapshot(system_name)
            start_date = _parse_date(start_snapshot["maintainabilityDate"])
            end_date = _parse_date(end_snapshot["maintainabilityDate"])

            _update_star_statistics(statistics, end_snapshot)
            best_inc, best_dec, diff = _update_best_changes(
                system_name,
                start_snapshot,
                end_snapshot,
                start_date,
                end_date,
                period_start,
                best_inc,
                best_dec,
            )
            _update_change_count(statistics, diff)
            _update_volume_change(statistics, system_name, start_snapshot, end_snapshot)
            _update_test_code_ratio_change(
                statistics,
                system_name,
                start_snapshot,
                end_snapshot,
                start_date,
                end_date,
            )
            _collect_averages_data(
                start_snapshot,
                end_snapshot,
                start_date,
                period_start,
                start_maintainability_ratings,
                end_maintainability_ratings,
                start_volumes,
                end_volumes,
            )

        _finalize_change_statistics(statistics, best_inc, best_dec)
        _calculate_averages(
            statistics,
            start_maintainability_ratings,
            end_maintainability_ratings,
            start_volumes,
            end_volumes,
        )

        return statistics

    def _rated_systems(self):
        return self.system_names

    def _extract_rating(self, system_name):
        md = utils.get_system_metadata(self.metadata, system_name)
        if not _is_system_active(md):
            return None
        end_snapshot = self.end_snapshot(system_name)
        return end_snapshot["maintainability"]

    def _get_rating_and_volume(self, system_name):
        md = utils.get_system_metadata(self.metadata, system_name)
        if not _is_system_active(md):
            return None, 0

        end_snapshot = self.end_snapshot(system_name)
        rating = end_snapshot["maintainability"]
        volume = end_snapshot.get("volumeInPersonMonths", 0)
        return rating, volume

    @cached_property
    def test_code_ratio_distribution_percentages(self):
        """Calculate percentage of systems in each test code ratio category."""
        counts = {"low": 0, "medium": 0, "high": 0}
        total = 0

        for system_name in self.system_names:
            md = utils.get_system_metadata(self.metadata, system_name)
            if not _is_system_active(md):
                continue

            end_snapshot = self.end_snapshot(system_name)
            test_code_ratio = end_snapshot.get("testCodeRatio")

            if test_code_ratio is None:
                continue

            category = _categorize_test_code_ratio(test_code_ratio)
            counts[category] += 1
            total += 1

        # Calculate percentages
        if total == 0:
            return {"low": 0, "medium": 0, "high": 0}

        return {
            "low": round(100 * counts["low"] / total),
            "medium": round(100 * counts["medium"] / total),
            "high": round(100 * counts["high"] / total),
        }


maintainability_portfolio_data = MaintainabilityPortfolioData()

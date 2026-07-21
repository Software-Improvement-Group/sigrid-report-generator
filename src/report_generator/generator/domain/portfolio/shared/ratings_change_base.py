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

from functools import cached_property

from report_generator.generator.domain.portfolio.shared import utils


class RatingsChangePortfolioBase:
    """Per-system change in a portfolio rating between the start and end of the reporting period.

    The model-ratings endpoints are point-in-time, so the delta is obtained by requesting the
    ratings at both period boundaries (via the ``endDate`` parameter) and subtracting.

    Subclasses provide the boundary snapshots (``_start_ratings`` / ``_end_ratings``, each fetched
    with the appropriate ``@filter_data_on_portfolio_arguments`` decorator), the per-system
    identifier key (``_system_tag``), how to read a rating out of a system (``_extract_rating``)
    and the portfolio ``metadata`` used to resolve display names.
    """

    _system_tag: str

    def _extract_rating(self, system) -> float | None:
        raise NotImplementedError

    @property
    def _start_ratings(self):
        raise NotImplementedError

    @property
    def _end_ratings(self):
        raise NotImplementedError

    @property
    def metadata(self):
        raise NotImplementedError

    @staticmethod
    def _delta(start_rating, end_rating) -> float | None:
        if start_rating is None or end_rating is None:
            return None
        return end_rating - start_rating

    @cached_property
    def differences(self) -> dict[str, float | None]:
        start = {
            s[self._system_tag]: self._extract_rating(s) for s in self._start_ratings
        }
        end = {s[self._system_tag]: self._extract_rating(s) for s in self._end_ratings}
        return {
            name: self._delta(start.get(name), end_rating)
            for name, end_rating in end.items()
        }

    def get_difference(self, system_name: str) -> float | None:
        return self.differences.get(system_name)

    @cached_property
    def average_delta(self) -> float:
        """Portfolio-wide change in the volume-weighted average rating over the period.

        Computed as the end-of-period volume-weighted average minus the start-of-period average
        (a delta of averages, not an average of per-system deltas). Returns 0.0 when no system
        contributes at either boundary.
        """
        return self.end_weighted_average - self.start_weighted_average

    def get_display_name(self, system_name: str) -> str:
        md = utils.get_system_metadata(self.metadata, system_name)
        if md is None:
            return system_name
        return md.get("displayName") or system_name

    @cached_property
    def _valid_differences(self) -> dict[str, float]:
        return {
            name: delta for name, delta in self.differences.items() if delta is not None
        }

    @cached_property
    def _change_counts(self) -> dict[str, int]:
        counts = {"increased": 0, "stable": 0, "decreased": 0}
        for delta in self._valid_differences.values():
            if delta > 0:
                counts["increased"] += 1
            elif delta < 0:
                counts["decreased"] += 1
            else:
                counts["stable"] += 1
        return counts

    @cached_property
    def change_distribution_percentages(self) -> dict[str, int]:
        """Percentage of systems whose rating increased, stayed stable, or decreased."""
        counts = self._change_counts
        total = sum(counts.values())
        if total == 0:
            return counts
        return {key: round(100 * value / total) for key, value in counts.items()}

    def _biggest_mover(self, selector, keep) -> tuple[str, float] | None:
        candidates = {
            name: delta
            for name, delta in self._valid_differences.items()
            if keep(delta)
        }
        if not candidates:
            return None
        system = selector(candidates, key=candidates.get)
        return self.get_display_name(system), round(candidates[system], 1)

    @cached_property
    def biggest_increase(self) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest rating increase."""
        return self._biggest_mover(max, lambda delta: delta > 0)

    @cached_property
    def biggest_decrease(self) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest rating decrease."""
        return self._biggest_mover(min, lambda delta: delta < 0)

    def _rating_and_volume(self, system) -> tuple[float | None, float]:
        return utils.get_rating_and_volume_from_system(
            system, self._extract_rating, self._system_tag
        )

    @cached_property
    def start_weighted_average(self) -> float:
        """Volume-weighted average rating at the start of the reporting period."""
        return utils.calculate_weighted_average_rating(
            self._start_ratings, self._rating_and_volume
        )

    @cached_property
    def end_weighted_average(self) -> float:
        """Volume-weighted average rating at the end of the reporting period."""
        return utils.calculate_weighted_average_rating(
            self._end_ratings, self._rating_and_volume
        )

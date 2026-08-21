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

from abc import ABC, abstractmethod
from functools import cached_property

from report_generator.generator.domain.portfolio.shared import utils


class RatingsChangePortfolioBase(ABC):
    """Per-system change in a portfolio rating between the start and end of the reporting period.

    The model-ratings endpoints are point-in-time, so the delta is obtained by requesting the
    ratings at both period boundaries (via the ``endDate`` parameter) and subtracting.

    Subclasses provide the boundary snapshots (``_start_ratings`` / ``_end_ratings``, each fetched
    with the appropriate ``@filter_data_on_portfolio_arguments`` decorator), the per-system
    identifier key (``_system_tag``), how to read a rating out of a system (``_extract_rating``)
    and the portfolio ``metadata`` used to resolve display names.
    """

    _system_tag: str

    @abstractmethod
    def _extract_rating(self, system) -> float | None: ...

    @property
    @abstractmethod
    def _start_ratings(self): ...

    @property
    @abstractmethod
    def _end_ratings(self): ...

    @property
    @abstractmethod
    def metadata(self): ...

    @staticmethod
    def _delta(start_rating, end_rating) -> float | None:
        if start_rating is None or end_rating is None:
            return None
        return end_rating - start_rating

    def differences_using(self, extractor) -> dict[str, float | None]:
        """Per-system rating delta over the period, using an arbitrary rating extractor."""
        start = {s[self._system_tag]: extractor(s) for s in self._start_ratings}
        end = {s[self._system_tag]: extractor(s) for s in self._end_ratings}
        return {
            name: self._delta(start.get(name), end_rating)
            for name, end_rating in end.items()
        }

    @cached_property
    def differences(self) -> dict[str, float | None]:
        return self.differences_using(self._extract_rating)

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

    @staticmethod
    def _valid_differences(differences: dict[str, float | None]) -> dict[str, float]:
        return {name: delta for name, delta in differences.items() if delta is not None}

    @staticmethod
    def _change_counts(valid_differences: dict[str, float]) -> dict[str, int]:
        counts = {"increased": 0, "stable": 0, "decreased": 0}
        for delta in valid_differences.values():
            if delta > 0:
                counts["increased"] += 1
            elif delta < 0:
                counts["decreased"] += 1
            else:
                counts["stable"] += 1
        return counts

    def change_distribution_percentages_using(self, extractor) -> dict[str, int]:
        """Percentage of systems whose rating increased, stayed stable, or decreased,
        using an arbitrary rating extractor."""
        counts = self._change_counts(
            self._valid_differences(self.differences_using(extractor))
        )
        total = sum(counts.values())
        if total == 0:
            return counts
        return {key: round(100 * value / total) for key, value in counts.items()}

    @cached_property
    def change_distribution_percentages(self) -> dict[str, int]:
        """Percentage of systems whose rating increased, stayed stable, or decreased."""
        return self.change_distribution_percentages_using(self._extract_rating)

    def _biggest_mover(
        self, valid_differences: dict[str, float], selector, keep
    ) -> tuple[str, float] | None:
        candidates = {
            name: delta for name, delta in valid_differences.items() if keep(delta)
        }
        if not candidates:
            return None
        system = selector(candidates, key=candidates.get)
        return self.get_display_name(system), round(candidates[system], 1)

    def biggest_increase_using(self, extractor) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest rating increase,
        using an arbitrary rating extractor."""
        return self._biggest_mover(
            self._valid_differences(self.differences_using(extractor)),
            max,
            lambda delta: delta > 0,
        )

    def biggest_decrease_using(self, extractor) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest rating decrease,
        using an arbitrary rating extractor."""
        return self._biggest_mover(
            self._valid_differences(self.differences_using(extractor)),
            min,
            lambda delta: delta < 0,
        )

    @cached_property
    def biggest_increase(self) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest rating increase."""
        return self.biggest_increase_using(self._extract_rating)

    @cached_property
    def biggest_decrease(self) -> tuple[str, float] | None:
        """Display name and rounded delta of the system with the largest rating decrease."""
        return self.biggest_decrease_using(self._extract_rating)

    def weighted_average_using(self, ratings, extractor) -> float:
        """Volume-weighted average rating for a set of system snapshots, using an arbitrary
        rating extractor."""
        return utils.calculate_weighted_average_rating(
            ratings,
            lambda system: utils.get_rating_and_volume_from_system(
                system, extractor, self._system_tag
            ),
        )

    @cached_property
    def start_weighted_average(self) -> float:
        """Volume-weighted average rating at the start of the reporting period."""
        return self.weighted_average_using(self._start_ratings, self._extract_rating)

    @cached_property
    def end_weighted_average(self) -> float:
        """Volume-weighted average rating at the end of the reporting period."""
        return self.weighted_average_using(self._end_ratings, self._extract_rating)

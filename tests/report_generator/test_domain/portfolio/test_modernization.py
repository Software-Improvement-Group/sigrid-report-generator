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


from report_generator.generator.domain.portfolio.modernization import (
    Scenario,
    get_activity,
    get_change_speed,
    get_renovation_effort,
)


class TestModernizationHelpers:
    """Test cases for helper functions in modernization module."""

    def test_get_renovation_effort_for_keep_as_is(self):
        """Test that get_renovation_effort returns 0 for KEEP_AS_IS."""
        effort = get_renovation_effort(Scenario.KEEP_AS_IS, {}, 100.0)

        assert abs(effort - 0.0) < 0.01

    def test_get_renovation_effort_for_replace(self):
        """Test that get_renovation_effort returns 0 for REPLACE."""
        effort = get_renovation_effort(Scenario.REPLACE, {}, 100.0)

        assert abs(effort - 0.0) < 0.01

    def test_get_renovation_effort_for_rebuild(self):
        """Test that get_renovation_effort returns volume for REBUILD."""
        effort = get_renovation_effort(Scenario.REBUILD, {}, 100.0)

        assert abs(effort - 100.0) < 0.01

    def test_get_renovation_effort_for_renovate(self):
        """Test that get_renovation_effort returns renovation effort for RENOVATE."""
        architecture_metrics = {"RENOVATION_EFFORT": 50.0}
        effort = get_renovation_effort(Scenario.RENOVATE, architecture_metrics, 100.0)

        assert abs(effort - 50.0) < 0.01

    def test_get_activity_calculates_from_churn(self):
        """Test that get_activity calculates activity from churn percentage."""
        architecture_graph = {
            "systemElements": [
                {
                    "measurementTimeSeries": {
                        "YEARLY_CHURN_PERCENTAGE": {"averageValue": 10.0}
                    }
                }
            ]
        }

        activity = get_activity(100.0, architecture_graph)

        # note: (10.0 / 100.0 * 52) * 100.0 = 520.0
        assert abs(activity - 520.0) < 0.01

    def test_get_activity_returns_none_when_no_churn(self):
        """Test that get_activity returns None when churn data is missing."""
        architecture_graph = {"systemElements": [{"measurementTimeSeries": {}}]}

        activity = get_activity(100.0, architecture_graph)

        assert activity is None

    def test_get_change_speed_returns_zero_for_keep_as_is(self):
        """Test that get_change_speed returns 0 for KEEP_AS_IS."""
        speed = get_change_speed(Scenario.KEEP_AS_IS, {})

        assert abs(speed - 0.0) < 0.01

    def test_get_change_speed_returns_potential_for_renovate(self):
        """Test that get_change_speed returns potential change speed for RENOVATE."""
        architecture_metrics = {"POTENTIAL_CHANGE_SPEED": 1.5}
        speed = get_change_speed(Scenario.RENOVATE, architecture_metrics)

        assert abs(speed - 1.5) < 0.01

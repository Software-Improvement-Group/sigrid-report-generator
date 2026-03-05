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



class TestAbstractPortfolioModel:
    """Test cases for AbstractPortfolioModel base class."""

    def test_system_names_helper_extracts_names(self):
        """Test _system_names_helper extracts system names from data."""
        from report_generator.generator.domain.portfolio.shared import utils
        data = [
            {'systemName': 'system1', 'value': 100},
            {'systemName': 'system2', 'value': 200},
            {'systemName': 'system3', 'value': 150}
        ]

        names = utils.system_names_helper(data, 'systemName')

        assert len(names) == 3
        assert names == ['system1', 'system2', 'system3']

    def test_get_system_helper_finds_correct_system(self):
        """Test _get_system_helper finds the correct system."""
        from report_generator.generator.domain.portfolio.shared import utils
        data = [
            {'system': 'sys1', 'maintainability': 4.0},
            {'system': 'sys2', 'maintainability': 3.5},
            {'system': 'sys3', 'maintainability': 4.2}
        ]

        result = utils.get_system_helper('sys2', data, 'system')

        assert result is not None
        assert result['system'] == 'sys2'
        assert abs(result['maintainability'] - 3.5) < 0.01

    def test_get_system_helper_returns_none_for_missing(self):
        """Test _get_system_helper returns None for non-existent system."""
        from report_generator.generator.domain.portfolio.shared import utils
        data = [
            {'system': 'sys1', 'maintainability': 4.0}
        ]

        result = utils.get_system_helper('unknown', data, 'system')

        assert result is None



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

from unittest.mock import Mock, patch

import pytest
import yaml
from requests.exceptions import RequestException, Timeout

from report_generator.generator.formatters.technologies import (
    _fetch_technologies_yaml, _get_technology_cache, _load_technologies,
    clear_technology_cache, get_cache_info, get_fallback_technology_name,
    get_technology_category, get_technology_name
)

MOCK_YAML_DATA = [
    {'context': 'abap', 'display_name': 'ABAP', 'category': 'customization'},
    {'context': 'abapcds', 'display_name': 'ABAP Core Data Services', 'category': 'customization'},
    {'context': 'python', 'display_name': 'Python', 'category': 'modern'},
    {'context': 'js', 'display_name': 'JavaScript', 'category': 'web'}
]


@pytest.fixture(autouse=True)
def reset_cache():
    clear_technology_cache()
    import report_generator.generator.formatters.technologies
    report_generator.generator.formatters.technologies._has_attempted_load = False


def create_mock_response(text_content):
    mock_response = Mock()
    mock_response.text = text_content
    mock_response.raise_for_status.return_value = None
    return mock_response


class TestFallbackTechnologyName:
    @pytest.mark.parametrize("input_tech,expected", [
        ("js", "JS"),
        ("python", "Python"),
        ("cpp", "Cpp")
    ])
    def test_fallback_names(self, input_tech, expected):
        assert get_fallback_technology_name(input_tech) == expected


class TestTechnologyYamlFetch:
    @patch('requests.get')
    def test_successful_fetch(self, mock_get):
        mock_get.return_value = create_mock_response(yaml.dump(MOCK_YAML_DATA))

        result = _fetch_technologies_yaml()

        assert result == MOCK_YAML_DATA
        mock_get.assert_called_once_with(
            "https://raw.githubusercontent.com/Software-Improvement-Group/sigridci/main/resources/technologies.yaml",
            timeout=10
        )

    @patch('requests.get')
    @pytest.mark.parametrize("exception", [
        RequestException("Network error"),
        Timeout("Request timeout")
    ])
    def test_network_errors_return_empty_list(self, mock_get, exception):
        mock_get.side_effect = exception
        assert _fetch_technologies_yaml() == []

    @patch('requests.get')
    @pytest.mark.parametrize("invalid_content", [
        "invalid: yaml: content: [",
        yaml.dump({"not": "a list"})
    ])
    def test_invalid_yaml_returns_empty_list(self, mock_get, invalid_content):
        mock_get.return_value = create_mock_response(invalid_content)
        assert _fetch_technologies_yaml() == []


class TestTechnologyLoader:
    @patch('report_generator.generator.formatters.technologies._fetch_technologies_yaml')
    def test_load_success(self, mock_fetch):
        mock_fetch.return_value = MOCK_YAML_DATA

        result = _load_technologies()

        expected = {
            'abap'   : {'display_name': 'ABAP', 'category': 'customization'},
            'abapcds': {'display_name': 'ABAP Core Data Services', 'category': 'customization'},
            'python' : {'display_name': 'Python', 'category': 'modern'},
            'js'     : {'display_name': 'JavaScript', 'category': 'web'}
        }
        assert result == expected

    @patch('report_generator.generator.formatters.technologies._fetch_technologies_yaml')
    def test_load_filters_malformed_entries(self, mock_fetch):
        malformed_data = [
            {'context': 'good', 'display_name': 'Good', 'category': 'test'},
            {'no_context': 'bad'},
            "not a dict",
            {'context': 'also_good', 'display_name': 'Also Good'}
        ]
        mock_fetch.return_value = malformed_data

        result = _load_technologies()

        expected = {
            'good'     : {'display_name': 'Good', 'category': 'test'},
            'also_good': {'display_name': 'Also Good', 'category': None}
        }
        assert result == expected


class TestTechnologyCache:
    @patch('report_generator.generator.formatters.technologies._fetch_technologies_yaml')
    def test_cache_clear_resets_state(self, mock_fetch):
        mock_fetch.return_value = MOCK_YAML_DATA

        _get_technology_cache()
        clear_technology_cache()

        info = get_cache_info()
        assert not info["is_loaded"]
        assert info["cache_size"] == 0


class TestTechnologyLookup:
    @patch('report_generator.generator.formatters.technologies._fetch_technologies_yaml')
    def test_technology_name_lookup(self, mock_fetch):
        mock_fetch.return_value = [{'context': 'python', 'display_name': 'Python', 'category': 'modern'}]

        assert get_technology_name('python') == 'Python'
        assert get_technology_name('PYTHON') == 'Python'
        assert get_technology_name('unknown') == 'Unknown'

    @patch('report_generator.generator.formatters.technologies._fetch_technologies_yaml')
    def test_technology_category_lookup(self, mock_fetch):
        mock_fetch.return_value = [{'context': 'python', 'display_name': 'Python', 'category': 'modern'}]

        assert get_technology_category('python') == 'modern'
        assert get_technology_category('unknown') == 'unknown'

    @patch('report_generator.generator.formatters.technologies._fetch_technologies_yaml')
    @pytest.mark.parametrize("tech_data,lookup_key,expected_name,expected_category", [
        ({'display_name': None, 'category': 'test'}, 'test', 'Test', 'test'),
        ({'display_name': 'Test', 'category': None}, 'test', 'Test', 'unknown')
    ])
    def test_handles_missing_data_gracefully(self, mock_fetch, tech_data, lookup_key, expected_name, expected_category):
        mock_fetch.return_value = [{'context': lookup_key, **tech_data}]

        assert get_technology_name(lookup_key) == expected_name
        assert get_technology_category(lookup_key) == expected_category


class TestIntegration:
    @patch('requests.get')
    def test_full_workflow(self, mock_get):
        mock_get.return_value = create_mock_response(yaml.dump(MOCK_YAML_DATA))

        assert get_technology_name('abap') == 'ABAP'
        assert get_technology_name('PYTHON') == 'Python'
        assert get_technology_name('nonexistent') == 'Nonexistent'

        assert get_technology_category('abap') == 'customization'
        assert get_technology_category('js') == 'web'
        assert get_technology_category('nonexistent') == 'unknown'

        mock_get.assert_called_once()

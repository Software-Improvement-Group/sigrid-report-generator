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

import report_generator.generator.sigrid_api as sigrid_api


class TestSigridAPI:

    def test_short_sigrid_token_is_invalid(self):
        with pytest.raises(Exception) as excinfo:
            sigrid_api._test_sigrid_token("eyo")
        assert str(excinfo.value).startswith("Invalid Sigrid token")

    def test_random_string_is_invalid_sigrid_token(self):
        with pytest.raises(Exception) as excinfo:
            sigrid_api._test_sigrid_token("sfkskfiurkfshiuwhfibvcgi43hf2o3h893hg34")
        assert str(excinfo.value).startswith("Invalid Sigrid token")

    def test_valid_sigrid_token_is_valid(self):
        try:
            sigrid_api._test_sigrid_token("eyKskfiurkfshiuwhfibvcgi43hf2o3h893hg34")
        except ValueError:
            pytest.fail(f"This token was expected to be valid")

    def test_set_context_multiple_times_preserves_previous_values(self):
        sigrid_api.reset_context()

        custom_base_url = "http://localhost:8080"
        sigrid_api.set_context(base_url=custom_base_url)
        assert custom_base_url in sigrid_api._rest_url

        sigrid_api.set_context(customer="test-customer")
        assert sigrid_api._customer == "test-customer"
        assert custom_base_url in sigrid_api._rest_url, "existing context (base_url) should be preserved"

        sigrid_api.reset_context()

    def test_reset_context_not_specified_resets_all_values(self):
        sigrid_api.reset_context()

        sigrid_api.set_context(customer="test-customer", system="test-system")
        assert sigrid_api._customer == "test-customer"
        assert sigrid_api._system == "test-system"

        sigrid_api.reset_context()
        assert sigrid_api._customer is None
        assert sigrid_api._system is None

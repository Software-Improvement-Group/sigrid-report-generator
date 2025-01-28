import pytest
from src.report_generator.generic_utils import GenericUtils

class TestGenericUtils():

    def test_to_json_name(self):
        assert GenericUtils.to_json_name("UNIT_SIZE") == "unitSize"
        assert GenericUtils.to_json_name("DUPLICATION") == "duplication"

        assert GenericUtils.to_json_name("duplication") == "duplication"
        assert GenericUtils.to_json_name("UnIt_sIze") == "unitSize"
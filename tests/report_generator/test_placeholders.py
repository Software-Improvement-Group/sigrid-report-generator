from report_generator.placeholders.text.implementations import _to_json_name

class TestPlaceholders:

    def test_to_json_name(self):
        assert _to_json_name("UNIT_SIZE") == "unitSize"
        assert _to_json_name("DUPLICATION") == "duplication"

        assert _to_json_name("duplication") == "duplication"
        assert _to_json_name("UnIt_sIze") == "unitSize"
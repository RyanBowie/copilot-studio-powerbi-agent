import unittest

import yaml

from studio_yaml import dumps


class StudioYamlTests(unittest.TestCase):
    def test_sequence_items_are_indented_inside_their_property(self):
        source = {"inputs": [{"kind": "AutomaticTaskInput", "propertyName": "question"}],
                  "beginDialog": {"kind": "OnRecognizedIntent", "actions": [{"kind": "EndDialog"}]}}
        text = dumps(source)
        self.assertIn("inputs:\n  - kind:", text)
        self.assertIn("  actions:\n    - kind:", text)
        self.assertEqual(yaml.safe_load(text), source)

    def test_multiline_instructions_and_powerfx_use_literal_blocks(self):
        source = {"instructions": "First line\nSecond line",
                  "value": '=If(true,\n"quoted",\n"other")'}
        text = dumps(source)
        self.assertIn("instructions: |-", text)
        self.assertIn("value: |-", text)
        self.assertEqual(yaml.safe_load(text), source)

    def test_long_single_line_expression_is_not_soft_wrapped(self):
        expression = '="a very long Power Fx literal "' * 100
        text = dumps({"value": expression})
        self.assertEqual(len(text.splitlines()), 1)
        self.assertEqual(yaml.safe_load(text)["value"], expression)


if __name__ == "__main__":
    unittest.main()

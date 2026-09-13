import json
import re
import unittest

import yaml

from example_topics import placeholder_config, render_examples, synthetic_metadata
from general_runtime import build_error_topic, build_metadata_topic, build_query_topic


class ExampleTopicTests(unittest.TestCase):
    def test_all_four_complete_topics_are_deterministic_and_match_current_builders(self):
        files = render_examples()
        self.assertEqual(files, render_examples())
        config, metadata = placeholder_config(), synthetic_metadata()
        expected = {
            "ModelMetadata": build_metadata_topic(config, metadata),
            "GeneratedDaxQuery": build_query_topic(config, metadata),
            "GeneratedDaxAdvice": build_query_topic(config, metadata, advice=True),
            "GeneratedQueryError": build_error_topic(),
        }
        for name, topic in expected.items():
            with self.subTest(topic=name):
                self.assertEqual(yaml.safe_load(files[name + ".mcs.yml"]), topic)
                self.assertTrue(files[name + ".mcs.yml"].startswith("# SYNTHETIC REFERENCE"))

    def test_only_synthetic_metadata_and_placeholder_targets_are_used(self):
        files = render_examples()
        content = "\n".join(files.values())
        self.assertIsNone(re.search(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", content, re.I))
        self.assertEqual({t["name"] for t in synthetic_metadata()["tables"]}, {"Entity", "Event"})
        for value in placeholder_config().values():
            self.assertRegex(value, r"^__[A-Z_]+__$")
            self.assertIn(value, content)

    def test_index_exposes_contracts_and_distinguishes_error_handler_from_tools(self):
        index = json.loads(render_examples()["index.json"])
        self.assertTrue(index["syntheticReferenceOnly"])
        self.assertFalse(index["deployedSnapshot"])
        self.assertEqual(index["agentInstructions"], "..\\agent.mcs.yml")
        self.assertEqual(index["metadata"], "..\\metadata.example.json")
        self.assertEqual(len(index["topics"]), 4)
        self.assertEqual(sum(t["generativeSelection"] for t in index["topics"]), 3)
        self.assertEqual(index["topics"][-1]["trigger"], "OnError")
        for topic in index["topics"]:
            for connector in topic["connectors"]:
                self.assertEqual(connector["mode"], "Invoker")
                self.assertEqual(connector["connectionReference"], "__CONNECTION_REFERENCE__")

    def test_reference_documentation_does_not_suggest_deploying_examples(self):
        text = render_examples()["README.md"]
        self.assertIn("Do not import or publish", text)
        self.assertIn("does not", text)
        self.assertIn("read `resources.json`", text)


if __name__ == "__main__":
    unittest.main()

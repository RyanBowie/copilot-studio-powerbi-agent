"""Offline invariants for the fail-closed publication package."""
import json
from pathlib import Path
import unittest

import build_solution
import validate_publication


class SolutionPackageTests(unittest.TestCase):
    def test_all_query_paths_stop_before_execution(self):
        topics, _ = build_solution.definitions()
        for name in ("GeneratedDaxQuery", "GeneratedDaxAdvice"):
            actions = topics[name]["beginDialog"]["actions"]
            self.assertEqual(["SendActivity", "CancelAllDialogs"], [a["kind"] for a in actions[:2]])
            self.assertTrue(actions[1]["activityProcessed"])

    def test_metadata_never_probes_an_example_model(self):
        topics, _ = build_solution.definitions()
        actions = topics["ModelMetadata"]["beginDialog"]["actions"]
        self.assertNotIn("InvokeConnectorAction", [a["kind"] for a in actions])
        self.assertEqual("CancelAllDialogs", actions[-1]["kind"])
        self.assertEqual(
            {"Global.SchemaSnapshot", "Global.SchemaTurn", "Global.SchemaUser"},
            {a["variable"] for a in actions[:3]})
        for field, schema in topics["ModelMetadata"]["outputType"]["properties"].items():
            if schema["type"] == "Boolean":
                assignment = next(a for a in actions if a.get("variable") == "Topic." + field)
                self.assertIs(assignment["value"], False)

    def test_configuration_is_unpublished_and_tenant_neutral(self):
        files = build_solution.source_files()
        config = json.loads(files[Path("bots") / build_solution.NAME / "configuration.json"])
        self.assertFalse(config["publishOnImport"])
        self.assertEqual([], config["channels"])
        _, gpt = build_solution.definitions()
        self.assertNotIn("model", gpt["aISettings"])
        self.assertIn("UNCONFIGURED STARTER", gpt["instructions"])
        self.assertEqual(5, len([p for p in files if p.name == "botcomponent.xml"]))
        self.assertNotIn("<connectionid>", files[Path("Other") / "Customizations.xml"])

    def test_tracked_source_matches_generator(self):
        for relative, expected in build_solution.source_files().items():
            actual = (build_solution.ROOT / "solution" / "src" / relative).read_text(encoding="utf-8")
            self.assertEqual(expected, actual, str(relative))

    def test_every_zip_entry_is_inspected(self):
        texts = validate_publication.solution_texts(build_solution.ARCHIVE)
        self.assertEqual(15, len(texts))


if __name__ == "__main__":
    unittest.main()

import copy
import unittest

from studio_authoring import verify_components


class NativeAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.gpt = {
            "instructions": "Verified instruction\nSecond line",
            "conversationStarters": [{"title": "Explore", "text": "Show schema"}],
            "aISettings": {"model": {"kind": "PreviewModels", "modelNameHint": "IntendedModel"}},
        }
        self.topics = {"Metadata": {
            "inputs": [{}], "beginDialog": {"kind": "OnRecognizedIntent", "actions": [{}]},
        }}
        self.parsed = {"botComponentChanges": [
            {"component": {"schemaName": "example.gpt.default", "metadata": {
                "instructions": {"segments": [{"$kind": "TextSegment", "value": self.gpt["instructions"]}]},
                "conversationStarters": [{}],
                "aISettings": {"model": {"$kind": "PreviewModels", "modelNameHint": "IntendedModel"}},
            }}},
            {"component": {"schemaName": "example.topic.Metadata", "dialog": {
                "inputs": [{}], "beginDialog": {"$kind": "OnRecognizedIntent", "actions": [{}],
                                               "intent": {"includeInOnSelectIntent": True}},
            }}},
        ]}

    def test_parsed_native_contract_passes(self):
        result = verify_components(self.parsed, "example", self.gpt, self.topics)
        self.assertTrue(result["nativeInstructionTextVerified"])

    def test_stored_model_without_native_model_fails(self):
        del self.parsed["botComponentChanges"][0]["component"]["metadata"]["aISettings"]
        with self.assertRaisesRegex(RuntimeError, "model-selector"):
            verify_components(self.parsed, "example", self.gpt, self.topics)

    def test_missing_native_trigger_fails_even_if_component_exists(self):
        self.parsed["botComponentChanges"][1]["component"]["dialog"].pop("beginDialog")
        with self.assertRaisesRegex(RuntimeError, "dropped topic"):
            verify_components(self.parsed, "example", self.gpt, self.topics)

    def test_changed_native_text_and_disabled_selection_fail(self):
        for defect in ("text", "selection"):
            parsed = copy.deepcopy(self.parsed)
            if defect == "text":
                parsed["botComponentChanges"][0]["component"]["metadata"]["instructions"]["segments"][0]["value"] = "wrong"
            else:
                parsed["botComponentChanges"][1]["component"]["dialog"]["beginDialog"]["intent"]["includeInOnSelectIntent"] = False
            with self.subTest(defect=defect), self.assertRaises(RuntimeError):
                verify_components(parsed, "example", self.gpt, self.topics)


if __name__ == "__main__":
    unittest.main()

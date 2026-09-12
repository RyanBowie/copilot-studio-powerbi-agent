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

    def test_native_alias_default_resolver_and_provenance_are_verified(self):
        self.topics["Metadata"]["inputs"] = [
            {"kind": "AutomaticTaskInput", "propertyName": "modelAlias", "defaultValue": "primary"}
        ]
        dialog = self.parsed["botComponentChanges"][1]["component"]["dialog"]
        dialog["inputs"] = [{"$kind": "AutomaticTaskInput", "propertyName": "modelAlias",
                             "defaultValue": {"$kind": "ValueExpression", "literalValue": "primary"}}]
        dialog["beginDialog"]["actions"] = [
            {"id": "ResolveFixedModelAlias", "value": {"expressionText": 'Coalesce(Topic.modelAlias, "primary")'}}
        ]
        dialog["outputType"] = {"properties": {
            name: {} for name in ("stage", "connectorAttempted", "connectorReturned", "probeResultStatus",
                                 "visibilityVerified", "resolvedModelAlias")
        }}
        verify_components(self.parsed, "example", self.gpt, self.topics)
        for defect in ("default", "resolver", "provenance"):
            parsed = copy.deepcopy(self.parsed)
            value = parsed["botComponentChanges"][1]["component"]["dialog"]
            if defect == "default":
                value["inputs"][0].pop("defaultValue")
            elif defect == "resolver":
                value["beginDialog"]["actions"][0]["value"]["expressionText"] = "Topic.modelAlias"
            else:
                value["outputType"]["properties"].pop("connectorAttempted")
            with self.subTest(defect=defect), self.assertRaises(RuntimeError):
                verify_components(parsed, "example", self.gpt, self.topics)

    def test_native_connector_row_normalization_is_verified(self):
        expected = '=JSON(Topic.ProbeRows, JSONFormat.FlattenValueTables)'
        self.topics["Metadata"]["beginDialog"]["actions"] = [{"id": "setProbeJson", "value": expected}]
        dialog = self.parsed["botComponentChanges"][1]["component"]["dialog"]
        dialog["beginDialog"]["actions"] = [{"id": "setProbeJson", "value": {"expressionText": expected[1:]}}]
        verify_components(self.parsed, "example", self.gpt, self.topics)
        dialog["beginDialog"]["actions"][0]["value"]["expressionText"] = "JSON(Topic.ProbeRows)"
        with self.assertRaisesRegex(RuntimeError, "normalization"):
            verify_components(self.parsed, "example", self.gpt, self.topics)

    def test_native_safe_diagnostic_expression_and_message_reference_are_verified(self):
        condition = 'Topic.probeResultStatus <> "validated"'
        self.topics["Metadata"]["beginDialog"]["actions"] = [{
            "id": "RequireVerifiedVisibility", "conditions": [{
                "condition": "=" + condition,
                "actions": [{"id": "BuildSafeProbeDiagnostics", "value": '=JSON({version:"D1"})'}],
            }],
        }]
        guard = {"id": "RequireVerifiedVisibility", "conditions": [{
            "condition": {"expressionText": condition}, "actions": [
                {"id": "BuildSafeProbeDiagnostics", "value": {"expressionText": 'JSON({version:"D1"})'}},
                {"$kind": "SendActivity", "activity": {"text": [{"segments": [{
                    "$kind": "ExpressionSegment", "expression": {"variableReference": "Topic.ProbeDiagnostics"},
                }, {
                    "$kind": "ExpressionSegment", "expression": {"variableReference": "Topic.ProbeTypedMarkerIsOne"},
                }]}]}},
            ],
        }]}
        self.parsed["botComponentChanges"][1]["component"]["dialog"]["beginDialog"]["actions"] = [guard]
        verify_components(self.parsed, "example", self.gpt, self.topics)
        for defect in ("expression", "reference", "guard"):
            parsed = copy.deepcopy(self.parsed)
            branch = parsed["botComponentChanges"][1]["component"]["dialog"]["beginDialog"]["actions"][0]["conditions"][0]
            if defect == "expression":
                branch["actions"][0]["value"]["expressionText"] = "wrong"
            elif defect == "reference":
                branch["actions"][1]["activity"]["text"][0]["segments"][0]["expression"]["variableReference"] = "Topic.ProbeJson"
            else:
                branch["condition"]["expressionText"] = "false"
            with self.subTest(defect=defect), self.assertRaisesRegex(RuntimeError, "safe probe diagnostic"):
                verify_components(parsed, "example", self.gpt, self.topics)

    def test_native_fixed_probe_output_schema_must_match_the_actual_marker(self):
        from general_runtime import PROBE_OUTPUT_SCHEMA
        self.topics["Metadata"]["beginDialog"]["actions"] = [{
            "id": "VerifyCallerSchemaVisibility", "dynamicOutputSchema": PROBE_OUTPUT_SCHEMA,
        }]
        schema = {"$kind": "Record", "properties": {"firstTableRows": {
            "type": {"$kind": "Table", "properties": {"[AccessProbe]": {"type": {"$kind": "Number"}}}},
        }}}
        dialog = self.parsed["botComponentChanges"][1]["component"]["dialog"]
        dialog["beginDialog"]["actions"] = [{
            "id": "VerifyCallerSchemaVisibility", "dynamicOutputSchema": schema,
        }]
        verify_components(self.parsed, "example", self.gpt, self.topics)
        schema["properties"]["firstTableRows"]["type"]["properties"] = {"Value": {"type": {"$kind": "Any"}}}
        with self.assertRaisesRegex(RuntimeError, "fixed-probe output schema"):
            verify_components(self.parsed, "example", self.gpt, self.topics)


if __name__ == "__main__":
    unittest.main()

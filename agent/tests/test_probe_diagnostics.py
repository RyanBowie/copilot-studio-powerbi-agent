"""Safe diagnostic fixtures describe synthetic bindings; they are not caller-response evidence."""
import json
import unittest

from general_runtime import (
    PROBE_OUTPUT_SCHEMA, PROBE_STATUS_EXPRESSION, PROBE_TYPED_MARKER_CHECK,
    build_metadata_topic, connector_rows_json, fx_text, probe_diagnostics_expression, schema_probe,
)
from test_generated_dax import CONFIG, SCHEMA


def native_diagnostic_cases():
    base = {
        "version": "D1", "status": "missing_marker", "rawRows": 1, "rawState": "present",
        "normalizedRows": 1, "rootKind": "array", "firstKind": "object",
        "markerPresent": False, "markerType": "absent", "markerIsOne": False,
        "valueWrapper": False, "valueMarkerDepth": 0,
        "plainMarkerPresent": False, "plainMarkerIsOne": False,
        "responseContainer": False, "errorMemberPresent": False,
    }
    rows_cases = [
        ("valid-number", [{"[AccessProbe]": 1}],
         {"status": "validated", "markerPresent": True, "markerType": "number", "markerIsOne": True}),
        ("one-value-wrapper", [{"Value": {"[AccessProbe]": 1}}],
         {"valueWrapper": True, "valueMarkerDepth": 1}),
        ("two-value-wrappers", [{"Value": {"Value": {"[AccessProbe]": 1}}}],
         {"valueWrapper": True, "valueMarkerDepth": 2}),
        ("plain-marker", [{"AccessProbe": 1}], {"plainMarkerPresent": True, "plainMarkerIsOne": True}),
        ("string-row", ['{"[AccessProbe]":1}'], {"firstKind": "string"}),
        ("scalar-row", [1], {"firstKind": "number"}),
        ("empty-table", [], {"status": "missing_output", "rawRows": 0, "rawState": "empty",
                             "normalizedRows": 0, "firstKind": "blank"}),
        ("null-marker", [{"[AccessProbe]": None}], {"markerPresent": True, "markerType": "blank"}),
        ("wrong-number", [{"[AccessProbe]": 2}],
         {"status": "unexpected_marker", "markerPresent": True, "markerType": "number"}),
        ("empty-string-marker", [{"[AccessProbe]": ""}],
         {"status": "missing_marker", "markerPresent": True, "markerType": "blank"}),
        ("boolean-marker", [{"[AccessProbe]": True}],
         {"status": "validated", "markerPresent": True, "markerType": "boolean", "markerIsOne": True}),
        ("string-marker-no-sensitive-values", [{"[AccessProbe]": "DO_NOT_DISCLOSE_SENTINEL",
                                                "PrivateSyntheticColumn": "DO_NOT_DISCLOSE_SENTINEL"}],
         {"status": "unexpected_marker", "markerPresent": True, "markerType": "string"}),
        ("object-marker", [{"[AccessProbe]": {"private": None}}],
         {"status": "unexpected_marker", "markerPresent": True, "markerType": "object"}),
        ("array-marker", [{"[AccessProbe]": [1]}],
         {"status": "unexpected_marker", "markerPresent": True, "markerType": "array"}),
        ("response-container", [{"firstTableRows": [{"[AccessProbe]": 1}]}], {"responseContainer": True}),
        ("error-member-not-denial", [{"error": {"code": "SyntheticError"}}], {"errorMemberPresent": True}),
    ]
    cases = []
    status = PROBE_STATUS_EXPRESSION[1:].replace("Topic.ProbeRows", "R").replace("Topic.ProbeJson", "J")
    for name, rows, changes in rows_cases:
        j = fx_text(json.dumps(rows))
        expression = (f"With({{R:Table(ParseJSON({j})),J:{j}}}, "
                      f"With({{Topic:{{ProbeRows:R,ProbeJson:J,probeResultStatus:{status}}}}}, "
                      f"{probe_diagnostics_expression()[1:]}))")
        cases.append({"name": "diagnostic-" + name, "expression": expression,
                      "parseResultJson": True, "expected": {**base, **changes}})
    blank_expression = (
        'With({R:If(false,Table(ParseJSON("[]"))),J:"null"}, '
        f"With({{Topic:{{ProbeRows:R,ProbeJson:J,probeResultStatus:{status}}}}}, "
        f"{probe_diagnostics_expression()[1:]}))")
    cases.append({"name": "diagnostic-blank-or-unbound-not-distinguishable", "expression": blank_expression,
                  "parseResultJson": True, "expected": {
                      **base, "status": "missing_output", "rawRows": 0, "rawState": "blank_or_unbound",
                      "normalizedRows": -1, "rootKind": "null", "firstKind": "blank"}})
    typed = "Table({'[AccessProbe]':1})"
    cases += [
        {"name": "typed-probe-json-preserves-real-caller-marker",
         "expression": connector_rows_json(typed)[1:], "expected": '[{"[AccessProbe]":1}]'},
        {"name": "typed-probe-direct-field-and-original-gate-pass",
         "expression": (f"With({{R:{typed}}},With({{J:{connector_rows_json('R')[1:]},Topic:{{ProbeRows:R}}}},"
                        f"({PROBE_TYPED_MARKER_CHECK[1:]}) && ({status}) = \"validated\"))"),
         "expected": True},
        {"name": "typed-probe-missing-marker-still-rejected",
         "expression": ("With({R:Table({'[AccessProbe]':If(false,1)})},"
                        f"With({{J:{connector_rows_json('R')[1:]}}},{status}))"),
         "expected": "missing_marker"},
    ]
    return cases


class ProbeDiagnosticTests(unittest.TestCase):
    def test_diagnostics_run_only_in_failure_branch_before_terminal_message(self):
        body = build_metadata_topic(CONFIG, SCHEMA)
        top = body["beginDialog"]["actions"]
        self.assertFalse(any(a.get("id") == "BuildSafeProbeDiagnostics" for a in top))
        failure = next(a for a in top if a["id"] == "RequireVerifiedVisibility")["conditions"][0]
        self.assertEqual(failure["condition"], '=Topic.probeResultStatus <> "validated"')
        actions = failure["actions"]
        diagnostic = next(a for a in actions if a["id"] == "BuildSafeProbeDiagnostics")
        self.assertEqual(diagnostic["value"], probe_diagnostics_expression())
        message = next(a for a in actions if a["kind"] == "SendActivity")
        self.assertLess(actions.index(diagnostic), actions.index(message))
        self.assertIn("{Topic.ProbeDiagnostics}", message["activity"])
        self.assertIn("cannot distinguish", message["activity"])
        self.assertEqual(actions[-1]["kind"], "CancelAllDialogs")

    def test_message_never_interpolates_rows_or_marker_values(self):
        body = build_metadata_topic(CONFIG, SCHEMA)
        failure = next(a for a in body["beginDialog"]["actions"] if a["id"] == "RequireVerifiedVisibility")
        message = next(a["activity"] for a in failure["conditions"][0]["actions"] if a["kind"] == "SendActivity")
        for value in ("{Topic.ProbeRows}", "{Topic.ProbeJson}", "{Topic.modelAlias}"):
            self.assertNotIn(value, message)
        expression = probe_diagnostics_expression()
        self.assertNotIn("Concat(ColumnNames", expression)
        self.assertNotIn("error.code", expression)
        self.assertNotIn("error.message", expression)

    def test_full_probe_and_invoker_binding_are_unchanged(self):
        body = build_metadata_topic(CONFIG, SCHEMA)
        action = next(a for a in body["beginDialog"]["actions"] if a["id"] == "VerifyCallerSchemaVisibility")
        self.assertEqual(action["input"]["binding"]["query"], schema_probe(SCHEMA))
        self.assertEqual(action["output"]["binding"], {"firstTableRows": "Topic.ProbeRows"})
        self.assertEqual(action["connectionProperties"], {"mode": "Invoker"})
        self.assertEqual(action["dynamicOutputSchema"], PROBE_OUTPUT_SCHEMA)
        check = next(a for a in body["beginDialog"]["actions"] if a["id"] == "CheckTypedProbeMarker")
        self.assertEqual(check["value"], PROBE_TYPED_MARKER_CHECK)

    def test_native_cases_cover_shapes_without_emitting_synthetic_private_content(self):
        cases = native_diagnostic_cases()
        self.assertEqual(len(cases), 20)
        self.assertEqual(len({case["name"] for case in cases}), len(cases))
        for case in cases:
            expected = json.dumps(case["expected"])
            self.assertNotIn("DO_NOT_DISCLOSE_SENTINEL", expected)
            self.assertNotIn("PrivateSyntheticColumn", expected)


if __name__ == "__main__":
    unittest.main()

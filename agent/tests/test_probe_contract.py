"""Synthetic response fixtures; native_cases evaluates actual generated Power Fx, not Python emulation."""
import json
import unittest

from general_runtime import PROBE_STATUS_EXPRESSION, build_metadata_topic, build_query_topic, connector_rows_json, fx_text
from test_generated_dax import CONFIG, SCHEMA


PROBE_CASES = [
    ("valid-native-row", [{"[AccessProbe]": 1}], "validated"),
    ("empty-table", [], "missing_output"),
    ("multiple-markers", [{"[AccessProbe]": 1}, {"[AccessProbe]": 1}], "unexpected_row_count"),
    ("missing-marker", [{}], "missing_marker"),
    ("null-marker", [{"[AccessProbe]": None}], "missing_marker"),
    ("wrong-marker", [{"[AccessProbe]": 0}], "unexpected_marker"),
    ("nonnumeric-marker", [{"[AccessProbe]": "invalid"}], "unexpected_marker"),
    ("scalar-row", ["not a record"], "missing_marker"),
    ("provider-error-shaped-row", [{"error": {"code": "SyntheticError"}}], "missing_marker"),
    ("extra-unexpected-wrapper", [{"Value": {"[AccessProbe]": 1}}], "missing_marker"),
    ("numeric-string-retains-original-behavior", [{"[AccessProbe]": "1"}], "validated"),
]


def native_cases():
    cases = []
    normalizer = connector_rows_json("R").removeprefix("=")
    status = PROBE_STATUS_EXPRESSION[1:].replace("Topic.ProbeRows", "R").replace("Topic.ProbeJson", "J")
    for name, rows, expected in PROBE_CASES:
        expression = f"With({{R:Table(ParseJSON({fx_text(json.dumps(rows))}))}}, With({{J:{normalizer}}}, {status}))"
        case = {"name": name, "expression": expression, "expected": expected}
        if name == "null-marker":
            # The installed Json assembly throws on its own ParseJSON null representation.
            case["allowedClosedException"] = "System.NotSupportedException"
            cases.append({"name": "null-marker-decoder-after-serialization",
                          "expression": f"With({{R:Table(ParseJSON({fx_text(json.dumps(rows))})),J:{fx_text(json.dumps(rows))}}}, {status})",
                          "expected": expected})
        cases.append(case)
    row = 'Table(ParseJSON("[{""[AccessProbe]"":1}]"))'
    cases += [
        {"name": "reproduce-default-native-value-wrapper", "expression": f"JSON({row})",
         "expected": '[{"Value":{"[AccessProbe]":1}}]'},
        {"name": "flatten-only-native-value-table", "expression": f"JSON({row}, JSONFormat.FlattenValueTables)",
         "expected": '[{"[AccessProbe]":1}]'},
        {"name": "old-normalizer-rejects-valid-probe",
         "expression": f"With({{R:{row}}}, With({{J:JSON(R)}}, {status}))", "expected": "missing_marker"},
    ]
    actions = {a["id"]: a for a in build_query_topic(CONFIG, SCHEMA)["beginDialog"]["actions"]}
    require = actions["RequireEnvelope"]["conditions"][0]["condition"][1:].replace("Topic.Envelope", "E")
    validate = actions["ValidateEnvelope"]["conditions"][0]["condition"][1:].replace("Topic.Envelope", "E").replace("Topic.Summary", "S")
    summary = actions["setSummary"]["value"][1:].replace("Topic.Envelope", "E")
    good = [{"[__kind]": "Summary", "[__status]": "ok", "[__returned]": 1},
            {"[__kind]": "Data", "[SyntheticValue]": 7}]
    for name, rows, encoding, expected in [
        ("old-normalizer-rejects-valid-query-envelope", good, "JSON(R)", True),
        ("normalized-query-envelope-passes", good, normalizer, False),
        ("missing-summary-rejected", good[1:], normalizer, True),
        ("duplicate-summary-rejected", [good[0], *good], normalizer, True),
        ("wrong-returned-count-rejected", [good[0]], normalizer, True),
    ]:
        expression = (f"With({{R:Table(ParseJSON({fx_text(json.dumps(rows))}))}}, "
                      f"With({{E:Table(ParseJSON({encoding}))}}, "
                      f"If({require}, true, With({{S:{summary}}}, {validate}))))")
        cases.append({"name": name, "expression": expression, "expected": expected})
    return cases


class ProbeContractTests(unittest.TestCase):
    def test_both_connector_results_normalize_value_tables(self):
        for body, identifier, variable in [
            (build_metadata_topic(CONFIG, SCHEMA), "setProbeJson", "Topic.ProbeRows"),
            (build_query_topic(CONFIG, SCHEMA), "setResultJson", "Topic.RawRows"),
        ]:
            action = next(a for a in body["beginDialog"]["actions"] if a["id"] == identifier)
            self.assertEqual(action["value"], connector_rows_json(variable))
            self.assertIn("JSONFormat.FlattenValueTables", action["value"])

    def test_returned_and_validation_stage_follow_connector_before_disclosure(self):
        actions = build_metadata_topic(CONFIG, SCHEMA)["beginDialog"]["actions"]
        connector_index = next(i for i, a in enumerate(actions) if a["id"] == "VerifyCallerSchemaVisibility")
        disclosure = next(i for i, a in enumerate(actions) if a.get("variable") == "Global.SchemaSnapshot")
        between = actions[connector_index + 1:disclosure]
        self.assertTrue(any(a.get("variable") == "Topic.connectorReturned" and a["value"] is True for a in between))
        self.assertTrue(any(a.get("variable") == "Topic.stage" and a["value"] == "schema_probe_output_validation" for a in between))
        status_index = next(i for i, a in enumerate(between) if a.get("value") == PROBE_STATUS_EXPRESSION)
        guard_index = next(i for i, a in enumerate(between) if a["id"] == "RequireVerifiedVisibility")
        verified_index = next(i for i, a in enumerate(between) if a.get("variable") == "Topic.visibilityVerified")
        self.assertLess(status_index, guard_index)
        self.assertLess(guard_index, verified_index)

    def test_bad_probe_stops_deterministically_without_permission_diagnosis(self):
        body = build_metadata_topic(CONFIG, SCHEMA)
        guard = next(a for a in body["beginDialog"]["actions"] if a["id"] == "RequireVerifiedVisibility")["conditions"][0]
        self.assertEqual(guard["condition"], '=Topic.probeResultStatus <> "validated"')
        self.assertTrue(any(a["kind"] == "CancelAllDialogs" and a["activityProcessed"] for a in guard["actions"]))
        message = next(a["activity"] for a in guard["actions"] if a["kind"] == "SendActivity")
        self.assertIn("not an established Power BI permission denial", message)
        self.assertIn("do not change permissions or datasets", message)
        self.assertNotIn("Topic.ProbeJson", message)

    def test_fixture_cases_cover_real_contract_and_fail_closed_shapes(self):
        cases = native_cases()
        self.assertEqual(len(cases), 20)
        self.assertEqual(len({c["name"] for c in cases}), len(cases))
        self.assertTrue(all("PowerBI" not in c["expression"] for c in cases))
        self.assertEqual(dict((name, result) for name, _, result in PROBE_CASES)["provider-error-shaped-row"], "missing_marker")


if __name__ == "__main__":
    unittest.main()

import copy
import json
import unittest

from generated_dax import build_query, validate_result
from general_runtime import build_query_topic, fx_text
from query_transport import OUTPUT_SCHEMA, decode_rows
from test_generated_dax import CONFIG, SCHEMA


def sample_rows(count=1):
    summary = {"[__kind]": "Summary", "[__status]": "ok", "[__returned]": count,
               "[__hasMore]": False, "[__textTruncated]": False,
               "[__anchorUtc]": "2026-09-12", "[__requestedStart]": "", "[__requestedEnd]": ""}
    data = {"[__kind]": "Data", "[__status]": "ok", "[__hasMore]": False, "[__textTruncated]": False,
            "[Scope]": "Synthetic", "[Rank]": 1, "[Creator]": 'quote " \u03a9\nuntrusted text',
            "[Fraction]": 0.14285714285714285, "[Tiny]": 1.23456789e-7,
            "[Large]": 123456789.1234567, "[Integer64]": 9007199254740993,
            "[Enabled]": True, "[Date]": "2024-02-03T00:00:00", "[Empty]": ""}
    return [summary] + [copy.deepcopy(data) for _ in range(count)]


def native_pipeline(raw, limit=20):
    actions = {a["id"]: a for a in build_query_topic(CONFIG, SCHEMA)["beginDialog"]["actions"]}
    def expression(name):
        a = actions[name]
        value = (a["value"] if "value" in a else a["conditions"][0]["condition"])[1:]
        for source, target in [
            ("Topic.RawRowCount", "N"), ("Topic.RawRows", "R"), ("Topic.ResultJson", "J"),
            ("Topic.Envelope", "E"), ("Topic.Summary", "S"), ("Topic.limit", str(limit)),
        ]:
            value = value.replace(source, target)
        return value
    return (
        f"With({{R:{raw}}},With({{N:{expression('setRawRowCount')}}},"
        f"If({expression('RequireTransportRows')},\"transport\","
        f"With({{J:{expression('setResultJson')}}},If({expression('ResponseBudget')},\"size\","
        f"With({{E:{expression('setEnvelope')}}},If({expression('RequireEnvelope')},\"markers\","
        f"With({{S:{expression('setSummary')}}},If({expression('ValidateEnvelope')},\"bounds\",\"success\"))"
        ")))))))"
    )


def native_transport_cases():
    variants = [
        ("varied-types", sample_rows(), "success"),
        ("empty-success", sample_rows(0), "success"),
        ("missing-summary", sample_rows()[1:], "markers"),
        ("duplicate-summary", [sample_rows()[0], *sample_rows()], "markers"),
        ("wrong-count", sample_rows(2)[:2], "bounds"),
        ("error-object", {"error": "Synthetic"}, "transport"),
        ("empty-array", [], "transport"),
        ("blank-root", None, "transport"),
        ("scalar-root", 1, "transport"),
        ("wrong-data-kind", [{**sample_rows()[0], "[__kind]": "Unknown"}], "markers"),
        ("bounds-status", [{**sample_rows(0)[0], "[__status]": "bounds_error"}], "bounds"),
        ("missing-return-count", [{k: v for k, v in sample_rows(0)[0].items() if k != "[__returned]"}], "bounds"),
        ("string-return-count", [{**sample_rows(0)[0], "[__returned]": "0"}], "bounds"),
        ("string-flag", [{**sample_rows(0)[0], "[__hasMore]": "false"}], "bounds"),
        ("missing-flag", [{k: v for k, v in sample_rows(0)[0].items() if k != "[__hasMore]"}], "bounds"),
        ("bad-data-status", [sample_rows()[0], {**sample_rows()[1], "[__status]": "error"}], "bounds"),
    ]
    cases = []
    for name, rows, expected in variants:
        raw = "ParseJSON(" + fx_text(json.dumps(rows, ensure_ascii=False)) + ")"
        cases.append({"name": "dynamic-query-" + name, "expression": native_pipeline(raw), "expected": expected})
    rows = sample_rows()
    raw = "ParseJSON(" + fx_text(json.dumps(rows, ensure_ascii=False)) + ")"
    cases.append({"name": "dynamic-query-exact-full-precision-and-types", "expression": "JSON(" + raw + ")",
                  "parseResultJson": True, "expected": rows})
    rows = sample_rows(100)
    raw = "ParseJSON(" + fx_text(json.dumps(rows, ensure_ascii=False)) + ")"
    cases += [
        {"name": "dynamic-query-top100", "expression": native_pipeline(raw, limit=100), "expected": "success"},
        {"name": "dynamic-query-over-limit", "expression": native_pipeline(raw, limit=99), "expected": "transport"},
    ]
    rows = sample_rows()
    rows[1]["[Creator]"] = "x" * 64001
    raw = "ParseJSON(" + fx_text(json.dumps(rows)) + ")"
    cases.append({"name": "dynamic-query-response-budget", "expression": native_pipeline(raw), "expected": "size"})
    return cases


class QueryTransportTests(unittest.TestCase):
    def test_full_precision_and_scalar_values_are_not_reencoded_by_dax(self):
        rows = sample_rows()
        self.assertIs(decode_rows(rows), rows)
        summary, data = validate_result(rows)
        self.assertEqual(data[0]["[Fraction]"], 0.14285714285714285)
        self.assertEqual(data[0]["[Integer64]"], 9007199254740993)
        self.assertIs(data[0]["[Enabled]"], True)
        self.assertEqual(data[0]["[Empty]"], "")
        self.assertNotIn("[Nullable]", data[0])

    def test_invalid_rows_flags_counts_and_size_fail_closed(self):
        variants = [[], [{"error": "synthetic"}], sample_rows(2)[:2]]
        value = sample_rows()
        value[0]["[__hasMore]"] = "false"
        variants.append(value)
        value = sample_rows()
        value[1]["[Creator]"] = "x" * 64001
        variants.append(value)
        for rows in variants:
            with self.subTest(count=len(rows)), self.assertRaises(ValueError):
                validate_result(rows)

    def test_original_dax_distinct_order_bounds_and_precision_are_unchanged(self):
        q = build_query({"tableExpression": 'ROW("Free Alias",DIVIDE(1,7))', "columns": "Free Alias", "limit": 100})
        self.assertNotIn("TOJSON", q)
        self.assertNotIn("__pocPayload", q)
        self.assertIn("TOPN(101,", q)
        self.assertIn("DISTINCT(SELECTCOLUMNS", q)
        self.assertTrue(q.endswith("ORDER BY [__kind] DESC, [Free Alias] ASC"))

    def test_dynamic_schema_and_explicit_null_policy_avoid_value_projection(self):
        body = build_query_topic(CONFIG, SCHEMA)
        actions = {a["id"]: a for a in body["beginDialog"]["actions"]}
        call = actions["ExecuteGeneratedQuery"]
        self.assertEqual(call["dynamicOutputSchema"], OUTPUT_SCHEMA)
        self.assertEqual(call["input"]["binding"]["serializerSettings"], "={includeNulls:false}")
        self.assertEqual(call["connectionProperties"], {"mode": "Invoker"})
        self.assertEqual(actions["setResultJson"]["value"], "=JSON(Topic.RawRows)")
        for name in ("RequireTransportRows", "RequireEnvelope", "ValidateEnvelope"):
            self.assertTrue(any(a["kind"] == "CancelAllDialogs" for a in actions[name]["conditions"][0]["actions"]))
        self.assertIn("Global.QueryAttempts >= 2", actions["AttemptBudget"]["conditions"][0]["condition"])
        self.assertNotIn("possibly a provider error", json.dumps(body))

    def test_native_cases_cover_current_dynamic_path(self):
        cases = native_transport_cases()
        self.assertEqual(len(cases), 20)
        self.assertEqual(len(cases), len({c["name"] for c in cases}))


if __name__ == "__main__":
    unittest.main()

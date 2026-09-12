import json
from pathlib import Path
import unittest

import generated_dax as dax
from general_runtime import build_error_topic, build_metadata_topic, build_query_topic, schema_probe

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {"workspaceId": "workspace-placeholder", "datasetId": "model-placeholder", "connectionReference": "reference-placeholder"}
SCHEMA = {
    "retrievedAtUtc": "2026-09-12T00:00:00+00:00",
    "tables": [
        {"name": "Entity", "description": "", "hidden": False,
         "columns": [{"name": "Key", "type": "string"}, {"name": "Owner", "type": "string"}, {"name": "Score", "type": "double"}],
         "measures": []},
        {"name": "Event", "description": "", "hidden": False,
         "columns": [{"name": "EntityKey", "type": "string"}, {"name": "Date", "type": "dateTime"}],
         "measures": [{"name": "Event Count", "description": "", "expressionAvailable": False}]},
    ],
    "relationships": [{"fromTable": "Event", "fromColumn": "EntityKey", "toTable": "Entity", "toColumn": "Key", "isActive": True}],
}


def flatten(actions):
    for a in actions:
        yield a
        for branch in a.get("conditions", []):
            yield from flatten(branch.get("actions", []))


class GeneratedDaxTests(unittest.TestCase):
    def test_free_expressions_not_business_enums(self):
        expressions = [
            ('SUMMARIZECOLUMNS(\'Entity\'[Owner], "Events", [Event Count])', "Owner,Events"),
            ('ROW("Owners", DISTINCTCOUNT(\'Entity\'[Owner]), "Mean", AVERAGE(\'Entity\'[Score]))', "Owners,Mean"),
            ('SELECTCOLUMNS(FILTER(\'Entity\', \'Entity\'[Score] > 2 && NOT ISBLANK(\'Entity\'[Owner])), "Who", \'Entity\'[Owner], "Squared", \'Entity\'[Score]^2)', "Who,Squared"),
            ('VAR X = FILTER(\'Entity\', \'Entity\'[Score] > 3) RETURN ROW("Eligible", COUNTROWS(X))', "Eligible"),
        ]
        for expr, columns in expressions:
            query = dax.build_query({"tableExpression": expr, "columns": columns})
            self.assertIn(expr, query)
            self.assertIn("DISTINCT(SELECTCOLUMNS", query)
        self.assertFalse(hasattr(dax, "METRICS"))
        self.assertFalse(hasattr(dax, "GROUPS"))

    def test_expression_boundary_cannot_escape_envelope(self):
        for expr in ('ROW("x",1))', 'ROW("x",1) EVALUATE \'Entity\'',
                     'VAR UTC_TODAY = DATE(1999,1,1) RETURN ROW("x",1)',
                     'ROW("x", __pocCount)', 'INFO.VIEW.TABLES()', 'EXTERNALMEASURE("x","server")',
                     'ROW("x",1);', 'ROW("x","unclosed)', 'ROW("x",1) /* unclosed'):
            with self.subTest(expr=expr), self.assertRaises(ValueError):
                dax.validate_expression(expr)

    def test_quotes_brackets_and_comments_are_lexed_not_executed(self):
        for expr in ('ROW("x", ") EVALUATE INFO")',
                     'SELECTCOLUMNS(\'Odd\'\'Table\', "x", \'Odd\'\'Table\'[a]]b])',
                     'ROW("x",1) // EVALUATE something',
                     'ROW("x",1) /* ) EVALUATE */'):
            dax.validate_expression(expr)
        self.assertNotIn("EVALUATE", dax.code_only('ROW("x", "EVALUATE")'))

    def test_projection_ordering_and_limits(self):
        query = dax.build_query({"tableExpression": 'ROW("N",1,"Label","a")', "columns": "N,Label", "sortBy": "n desc", "limit": 100})
        self.assertIn("TOPN(101,", query)
        self.assertIn("[N], DESC, [Label], ASC", query)
        for update in ({"columns": "__kind"}, {"columns": "N,n"}, {"columns": "bad]"},
                       {"sortBy": "NotDeclared desc"}, {"sortBy": "N desc,N asc"},
                       {"limit": 101}, {"limit": True}, {"limit": 1.5}, {"datasetid": "other"},
                       {"modelAlias": "secondary"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                dax.build_query({"tableExpression": 'ROW("N",1)', "columns": "N", **update})

    def test_general_date_expressions_and_trusted_clock(self):
        for start, end in (("UTC_TODAY-89", "UTC_TODAY"),
                           ("EOMONTH(UTC_TODAY,-2)+1", "EOMONTH(UTC_TODAY,-1)"),
                           ("DATE(YEAR(UTC_TODAY),1,1)", "UTC_TODAY")):
            query = dax.build_query({"tableExpression": 'ROW("Start",QUERY_START,"End",QUERY_END)', "columns": "Start,End",
                                     "startDateExpression": start, "endDateExpression": end})
            self.assertIn("VAR __pocNow = UTCNOW()", query)
            self.assertIn(start, query)
            self.assertIn(end, query)
            self.assertIn('"__requestedStart"', query)
        with self.assertRaisesRegex(ValueError, "Both date"):
            dax.build_query({"tableExpression": 'ROW("x",1)', "columns": "x", "startDateExpression": "UTC_TODAY"})
        with self.assertRaisesRegex(ValueError, "both QUERY_START"):
            dax.build_query({"tableExpression": 'ROW("x",1)', "columns": "x", "startDateExpression": "UTC_TODAY-2", "endDateExpression": "UTC_TODAY"})

    def test_resource_budget_and_cell_truncation_are_explicit(self):
        query = dax.build_query({"tableExpression": 'ROW("x","abc")', "columns": "x"})
        for text in ("LEFT([x], 256)", '"__textTruncated"', '"__hasMore"', '"bounds_error"', 'FILTER(__pocPage, __pocOk)'):
            self.assertIn(text, query)
        with self.assertRaises(ValueError):
            dax.build_query({"tableExpression": 'ROW("x",1)' + " " * 12000, "columns": "x"})
        with self.assertRaises(ValueError):
            dax.validate_expression("(" * 33 + 'ROW("x",1)' + ")" * 33)

    def test_success_requires_owned_envelope_not_http_or_rows_alone(self):
        summary = {"[__kind]": "Summary", "[__status]": "ok", "[__returned]": 1}
        data = {"[__kind]": "Data", "[x]": 1}
        self.assertEqual(dax.validate_result([summary, data])[1], [data])
        for rows in ([], [data], [summary], [summary, summary], [{**summary, "[__status]": "bounds_error"}, data]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                dax.validate_result(rows)
        self.assertEqual(dax.validate_result([{**summary, "[__returned]": 0}])[1], [])

    def test_native_query_is_invoker_scoped_and_uses_same_template(self):
        query = build_query_topic(CONFIG, SCHEMA)
        actions = query["beginDialog"]["actions"]
        call = next(a for a in actions if a["kind"] == "InvokeConnectorAction")
        self.assertEqual(call["connectionProperties"]["mode"], "Invoker")
        self.assertEqual(call["input"]["binding"]["datasetid"], CONFIG["datasetId"])
        self.assertEqual(call["input"]["binding"]["impersonatedUserName"], "=Blank()")
        self.assertNotIn("datasetid", query["inputType"]["properties"])
        self.assertTrue(all(not i["shouldPromptUser"] for i in query["inputs"] if i["propertyName"] != "modelAlias"))
        self.assertFalse(query["inputType"]["properties"]["tableExpression"]["isRequired"])
        ids = [a["id"] for a in actions]
        self.assertEqual(len(ids), len(set(ids)))
        serialized = json.dumps(query)
        self.assertNotIn("System.Activity.Id", serialized)
        self.assertIn("System.LastMessage.Id", serialized)
        self.assertNotIn("\\'", dax.FX_TOKEN_PATTERN)
        self.assertLess(ids.index("BalanceTable"), ids.index("ExecuteGeneratedQuery"))
        self.assertLess(ids.index("AttemptBudget"), ids.index("ExecuteGeneratedQuery"))
        self.assertIn("RequestedDatesRequired", ids)
        self.assertIn("LengthTable", ids)
        self.assertIn("ColumnNames", ids)
        compiled = next(a["value"] for a in actions if a.get("variable") == "Topic.generatedDax" and isinstance(a["value"], str) and a["value"].startswith("="))
        self.assertIn("UTCNOW()", compiled)
        self.assertIn("Topic.tableExpression", compiled)
        self.assertIn("Topic.StartExpr", compiled)

    def test_advice_does_not_execute_proposed_query(self):
        advice = build_query_topic(CONFIG, SCHEMA, advice=True)
        self.assertFalse(any(a["kind"] == "InvokeConnectorAction" for a in flatten(advice["beginDialog"]["actions"])))
        self.assertIn("UNEXECUTED", advice["beginDialog"]["actions"][-1]["value"])

    def test_metadata_is_gated_by_actual_caller_column_probe(self):
        metadata = build_metadata_topic(CONFIG, SCHEMA)
        actions = metadata["beginDialog"]["actions"]
        ids = [a["id"] for a in actions]
        self.assertLess(ids.index("VerifyCallerSchemaVisibility"), ids.index("RequireVerifiedVisibility"))
        self.assertLess(ids.index("RequireVerifiedVisibility"), ids.index("setSchemaRows"))
        probe = schema_probe(SCHEMA)
        self.assertIn("TOPN(0,", probe)
        self.assertIn("'Entity'[Owner]", probe)
        self.assertNotIn("getDefinition", probe)

    def test_runtime_no_longer_enforces_legacy_identity_or_metric_exclusions(self):
        import yaml
        agent = yaml.safe_load((ROOT / "agent.mcs.yml").read_text(encoding="utf-8"))
        text = agent["instructions"]
        self.assertLess(len(text), 8000)
        self.assertNotIn("Microsoft Agent 365", text)
        self.assertIn("owner/creator fields", text)
        self.assertIn("actual Power BI permissions", text)
        self.assertIn("AUTHOR NEW DAX", text)
        self.assertEqual(agent["aISettings"]["model"]["modelNameHint"], "GPT5Reasoning")
        self.assertFalse((ROOT / "analytics.py").exists())

    def test_errors_and_ambiguity_are_not_fabricated_results(self):
        error = build_error_topic()
        self.assertEqual(error["beginDialog"]["kind"], "OnError")
        self.assertIn("System.Error.Message", error["beginDialog"]["actions"][0]["value"])
        message = error["beginDialog"]["actions"][2]["activity"]
        self.assertIn("Access errors do not prove model fields are absent", message)
        self.assertIn("at most once", message)
        import yaml
        instructions = yaml.safe_load((ROOT / "agent.mcs.yml").read_text(encoding="utf-8"))["instructions"]
        self.assertIn("business meaning is ambiguous", instructions)
        self.assertIn("never pretend a retry ran", instructions)


if __name__ == "__main__":
    unittest.main()

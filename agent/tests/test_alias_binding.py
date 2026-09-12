"""Offline execution of the small generated scalar input gates, not a native chat test."""
import ast
import re
import unittest

from general_runtime import build_metadata_topic, build_query_topic
from test_generated_dax import CONFIG, SCHEMA, flatten


def scalar_gate(expression, topic, global_state=None):
    expression = expression.removeprefix("=").replace("<>", "!=").replace("||", " or ").replace("&&", " and ")
    expression = re.sub(r"!(?!=)", " not ", expression)
    expression = re.sub(r"(?<![<>!=])=(?!=)", "==", expression)

    def evaluate(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [evaluate(item) for item in node.elts]
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return {"Topic": topic, "Global": global_state or {}}[node.value.id].get(node.attr)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            args = [evaluate(arg) for arg in node.args]
            if node.func.id == "Coalesce":
                return next((value for value in args if value is not None and value != ""), None)
            if node.func.id == "Len":
                return len(args[0] or "")
        if isinstance(node, ast.BoolOp):
            values = [evaluate(value) for value in node.values]
            return any(values) if isinstance(node.op, ast.Or) else all(values)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not evaluate(node.operand)
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = evaluate(node.left), evaluate(node.comparators[0])
            op = node.ops[0]
            if isinstance(op, ast.NotEq):
                return left != right
            if isinstance(op, ast.Eq):
                return left == right
            if isinstance(op, ast.In):
                return left in right
            if isinstance(op, ast.Gt):
                return left > right
            if isinstance(op, ast.GtE):
                return left >= right
        raise AssertionError("Unsupported offline gate expression: " + ast.dump(node))

    return evaluate(ast.parse(expression.strip(), mode="eval").body)


class AliasBindingTests(unittest.TestCase):
    def setUp(self):
        self.metadata = build_metadata_topic(CONFIG, SCHEMA)
        self.actions = {a["id"]: a for a in self.metadata["beginDialog"]["actions"]}

    def request(self, alias, view="catalog", tables=""):
        state = {"modelAlias": alias, "view": view, "tableNames": tables}
        for identifier in ("ResolveFixedModelAlias", "DefaultMetadataView", "DefaultMetadataTables"):
            action = self.actions[identifier]
            state[action["variable"].split(".")[-1]] = scalar_gate(action["value"], state)
        invalid = scalar_gate(self.actions["ValidateMetadataInput"]["conditions"][0]["condition"], state)
        return state, invalid

    def test_missing_and_empty_alias_catalog_reproduce_and_fix_regression(self):
        for alias in (None, "", "primary"):
            with self.subTest(alias=alias):
                state, invalid = self.request(alias)
                self.assertEqual(state["resolvedModelAlias"], "primary")
                self.assertFalse(invalid)
        state, invalid = self.request("", "", "")
        self.assertEqual(state["view"], "catalog")
        self.assertFalse(invalid)

    def test_nonempty_invalid_alias_ids_view_and_length_are_rejected(self):
        for alias in ("other", "dataset-id", "workspace-id", " ", "primary/other"):
            with self.subTest(alias=alias):
                state, invalid = self.request(alias)
                self.assertEqual(state["resolvedModelAlias"], alias)
                self.assertTrue(invalid)
        self.assertTrue(self.request("", "invalid")[1])
        self.assertTrue(self.request("", tables="x" * 501)[1])

    def test_all_three_capabilities_use_supported_default_and_runtime_resolution(self):
        for topic in (self.metadata, build_query_topic(CONFIG, SCHEMA),
                      build_query_topic(CONFIG, SCHEMA, advice=True)):
            alias = next(i for i in topic["inputs"] if i["propertyName"] == "modelAlias")
            self.assertEqual(alias["kind"], "AutomaticTaskInput")
            self.assertEqual(alias["defaultValue"], "primary")
            self.assertFalse(alias["shouldPromptUser"])
            actions = {a["id"]: a for a in topic["beginDialog"]["actions"]}
            for value in (None, "", "primary", "other"):
                resolved = scalar_gate(actions["ResolveFixedModelAlias"]["value"], {"modelAlias": value})
                self.assertEqual(resolved, "primary" if value in (None, "") else value)
            if "ValidateQueryModel" in actions:
                gate = actions["ValidateQueryModel"]["conditions"][0]["condition"]
                self.assertFalse(scalar_gate(gate, {"resolvedModelAlias": "primary"}))
                self.assertTrue(scalar_gate(gate, {"resolvedModelAlias": "other"}))

    def test_input_rejection_has_pre_connector_provenance_and_records_failure(self):
        actions = self.metadata["beginDialog"]["actions"]
        ids = [a["id"] for a in actions]
        self.assertLess(ids.index("ResolveFixedModelAlias"), ids.index("ValidateMetadataInput"))
        self.assertLess(ids.index("ValidateMetadataInput"), ids.index("VerifyCallerSchemaVisibility"))
        branch = self.actions["ValidateMetadataInput"]["conditions"][0]["actions"]
        self.assertTrue(any(a.get("variable") == "Global.MetadataFailureKey" for a in branch))
        error = next(a["value"] for a in branch if a.get("variable") == "Topic.error")
        self.assertIn("BEFORE any Power BI connector attempt", error)
        for field in ("stage", "connectorAttempted", "visibilityVerified", "resolvedModelAlias"):
            self.assertIn(field, self.metadata["outputType"]["properties"])

    def test_identical_failed_request_cancels_and_budget_is_bounded(self):
        repeat = self.actions["StopRepeatedMetadataFailure"]["conditions"][0]
        state = {"MetadataRequestKey": "message:catalog"}
        self.assertTrue(scalar_gate(repeat["condition"], state, {"MetadataFailureKey": "message:catalog"}))
        self.assertFalse(scalar_gate(repeat["condition"], state, {"MetadataFailureKey": "other-message:catalog"}))
        cancel = next(a for a in repeat["actions"] if a["kind"] == "CancelAllDialogs")
        self.assertTrue(cancel["activityProcessed"])
        limit = self.actions["MetadataAttemptBudget"]["conditions"][0]
        self.assertFalse(scalar_gate(limit["condition"], {}, {"MetadataAttempts": 7}))
        self.assertTrue(scalar_gate(limit["condition"], {}, {"MetadataAttempts": 8}))
        self.assertTrue(any(a["kind"] == "CancelAllDialogs" for a in limit["actions"]))

    def test_success_path_keeps_catalog_table_retrieval_and_invoker_targets(self):
        self.assertFalse(self.request("", "tables", "Entity")[1])
        self.assertIn("ValidateTableSelection", self.actions)
        for topic in (self.metadata, build_query_topic(CONFIG, SCHEMA)):
            for action in flatten(topic["beginDialog"]["actions"]):
                if action["kind"] == "InvokeConnectorAction":
                    self.assertEqual(action["connectionProperties"]["mode"], "Invoker")
                    self.assertEqual(action["input"]["binding"]["datasetid"], CONFIG["datasetId"])
                    self.assertEqual(action["input"]["binding"]["groupid"], CONFIG["workspaceId"])


if __name__ == "__main__":
    unittest.main()

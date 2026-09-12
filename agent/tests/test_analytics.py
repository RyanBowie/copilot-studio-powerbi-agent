import json
from config import load_config
from pathlib import Path
import unittest

import yaml

from analytics import DEFAULTS, GROUPS, METRICS, build_advice_topic, build_clarification_topic, build_query, build_topic, validate_request

ROOT = Path(__file__).resolve().parents[1]


def flatten(actions):
    for action in actions:
        yield action
        for condition in action.get("conditions", []):
            yield from flatten(condition.get("actions", []))
        yield from flatten(action.get("elseActions", []))


class AnalyticsTests(unittest.TestCase):
    def test_materially_different_questions_share_compiler(self):
        queries = [
            build_query({"metric": "interactions", "groupBy": "platform", "startDate": "2026-08-01", "endDate": "2026-08-31"}),
            build_query({"metric": "agents", "groupBy": "risk"}),
            build_query({"metric": "sessions", "groupBy": "month", "sortBy": "group"}),
            build_query({"metric": "users", "groupBy": "host", "topN": 3}),
            build_query({"metric": "environments", "groupBy": "region"}),
        ]
        self.assertEqual(len(set(queries)), 5)
        for query in queries:
            self.assertIn('ROW("RowType", "Summary"', query)
            self.assertIn('"TotalGroups", __Count', query)
            self.assertIn('"HasMore", __Count >', query)
            self.assertNotIn("[Value], DESC", query.split("ORDER BY")[1])
        self.assertIn("DATESBETWEEN('Date'[Date], DATE(2026,8,1), DATE(2026,8,31))", queries[0])
        self.assertIn("VAR __Start = BLANK()", queries[1])

    def test_unknown_fields_and_incompatible_context_rejected(self):
        bad = [
            {"query": "EVALUATE 'User'"},
            {"datasetid": "another"},
            {"metric": "cost"},
            {"groupBy": "OwnerUpn"},
            {"filterBy": "ThreadId", "filterValue": "abc"},
            {"metric": "agents", "groupBy": "day"},
            {"metric": "environments", "filterBy": "host", "filterValue": "Teams"},
            {"metric": "agents", "startDate": "2026-08-01", "endDate": "2026-08-31"},
            {"filterBy": "region"},
            {"filterValue": "unrequested"},
            {"filterBy": "platform", "filterValue": "a" * 129},
        ]
        for request in bad:
            with self.subTest(request=request), self.assertRaises(ValueError):
                build_query(request)

    def test_bounds_and_dates(self):
        for top_n in (0, -1, 101, 1.5, True, "100"):
            with self.subTest(topN=top_n), self.assertRaises(ValueError):
                validate_request({"topN": top_n})
        for dates in [
            {"startDate": "2026-08-01"},
            {"startDate": "2026-02-30", "endDate": "2026-03-01"},
            {"startDate": "2026-08-31", "endDate": "2026-08-01"},
            {"startDate": "2024-01-01", "endDate": "2026-01-01"},
            {"startDate": "20260801", "endDate": "2026-08-31"},
            {"startDate": "0001-08-01", "endDate": "0001-08-31"},
        ]:
            with self.subTest(dates=dates), self.assertRaises(ValueError):
                build_query(dates)
        self.assertIn("TOPN(100,", build_query({"topN": 100}))

    def test_filter_injection_is_a_quoted_value_not_code(self):
        attack = 'x"}), EVALUATE \'User\' //'
        query = build_query({"filterBy": "platform", "filterValue": attack})
        self.assertIn('TREATAS({"x""}), EVALUATE \'User\' //"}, \'Agent\'[Platform])', query)
        topic = build_topic()
        filter_action = next(a for a in topic["beginDialog"]["actions"] if a["id"] == "setFilterDax")
        self.assertIn("Substitute(Topic.filterValue, Char(34), Char(34) & Char(34))", filter_action["value"])

    def test_generated_topic_is_current_and_enforces_scope_before_execution(self):
        generated = yaml.safe_load((ROOT / "topics" / "ModelAnalytics.mcs.yml").read_text(encoding="utf-8"))
        self.assertEqual(generated, build_topic())
        self.assertEqual(set(generated["inputType"]["properties"]), set(DEFAULTS) - {"mode"})
        actions = generated["beginDialog"]["actions"]
        ids = [a["id"] for a in actions]
        query_index = ids.index("ExecuteStructuredQuery")
        for guard in ("ValidateParameters", "ValidateInventoryContext", "ValidateDates", "AdviceOnly"):
            self.assertLess(ids.index(guard), query_index)
        self.assertEqual(actions[0]["value"], "execute")
        for guard in actions[1:4]:
            kinds = [a["kind"] for a in guard["conditions"][0]["actions"]]
            self.assertEqual(kinds[-1], "EndDialog")
        call = actions[query_index]
        config = load_config()
        self.assertEqual(call["input"]["binding"], {
            "groupid": config["workspaceId"], "datasetid": config["datasetId"],
            "query": "=Topic.Dax", "impersonatedUserName": "=Blank()",
        })
        self.assertEqual(call["connectionProperties"]["mode"], "Invoker")
        self.assertEqual(len([a for a in flatten(actions) if a["kind"] == "InvokeConnectorAction"]), 1)
        advice = actions[ids.index("AdviceOnly")]["conditions"][0]["actions"]
        self.assertFalse(any(a["kind"] == "InvokeConnectorAction" for a in flatten(advice)))
        self.assertIn("NOT EXECUTED", advice[0]["activity"])
        self.assertEqual(advice[-1]["kind"], "EndDialog")

    def test_all_allowed_contexts_build_without_external_names(self):
        for metric in METRICS:
            for group in GROUPS:
                if metric in ("agents", "environments") and group in ("month", "day", "host"):
                    continue
                query = build_query({"metric": metric, "groupBy": group})
                for forbidden in ("OwnerUpn", "OwnerName", "UserPrincipalName", "ThreadId", "[Resources]", "[Agent Interactions]"):
                    self.assertNotIn(forbidden, query)
                self.assertIn("TOPN(20,", query)

    def test_advice_has_no_connector_dependency(self):
        topic = build_advice_topic()
        generated = yaml.safe_load((ROOT / "topics" / "ModelDaxAdvice.mcs.yml").read_text(encoding="utf-8"))
        self.assertEqual(generated, topic)
        self.assertNotIn("mode", topic["inputType"]["properties"])
        actions = topic["beginDialog"]["actions"]
        self.assertEqual(actions[0]["variable"], "Topic.mode")
        self.assertEqual(actions[0]["value"], "dax")
        self.assertFalse(any("connectionReference" in a or a["kind"] == "InvokeConnectorAction" for a in flatten(actions)))

    def test_unknown_schema_has_useful_clarification(self):
        topic = build_clarification_topic()
        self.assertEqual(topic["beginDialog"]["kind"], "OnUnknownIntent")
        message = topic["beginDialog"]["actions"][0]["activity"]
        self.assertIn("Revenue", message)
        self.assertIn("Which supported metric and grouping", message)
        self.assertFalse(any("connectionReference" in a for a in flatten(topic["beginDialog"]["actions"])))


if __name__ == "__main__":
    unittest.main()

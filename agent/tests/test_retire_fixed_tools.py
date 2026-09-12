import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "retire_fixed_tools", Path(__file__).resolve().parents[1] / "retire-fixed-tools.py"
)
retire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retire)


class FakeApi:
    def __init__(self, blocked=None):
        self.blocked = blocked

    def request(self, path):
        if path.startswith("solutioncomponents?"):
            return {"value": [{"componenttype": 10228}]}
        if self.blocked and self.blocked in path:
            return {"value": [{"botid": "other-agent"}]}
        return {"value": []}


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "bot": {"configuration": "unchanged", "authenticationmode": 2,
                    "authenticationtrigger": 1, "accesscontrolpolicy": 2},
            "reference": {"connectionid": "preserved"},
            "components": [
                {"botcomponentid": str(i), "schemaname": retire.CONFIG["schemaName"] + "." + suffix,
                 "data": "fixed-fixture-" + str(i), "statecode": 1, "statuscode": 2}
                for i, suffix in enumerate(sorted(retire.SUFFIXES))
            ],
        }

    def test_only_three_inactive_unreferenced_tools_pass(self):
        self.assertEqual(len(retire.preflight(FakeApi(), self.snapshot, self.snapshot)), 3)

    def test_user_edits_stop_cleanup(self):
        reviewed = copy.deepcopy(self.snapshot)
        self.snapshot["components"][0]["data"] = "user-edit"
        with self.assertRaisesRegex(RuntimeError, "Concurrent portal"):
            retire.preflight(FakeApi(), self.snapshot, reviewed)

    def test_active_tool_cannot_be_deleted(self):
        self.snapshot["components"][0]["statecode"] = 0
        with self.assertRaisesRegex(RuntimeError, "no longer inactive"):
            retire.preflight(FakeApi(), self.snapshot, self.snapshot)

    def test_references_stop_cleanup(self):
        self.snapshot["components"][1]["data"] = self.snapshot["components"][0]["schemaname"]
        with self.assertRaisesRegex(RuntimeError, "references"):
            retire.preflight(FakeApi(), self.snapshot, self.snapshot)

    def test_platform_dependency_child_and_other_agent_guards(self):
        for blocked in ("RetrieveDependencies", "botcomponents?", "/bot_botcomponent?"):
            with self.subTest(blocked=blocked), self.assertRaises(RuntimeError):
                retire.preflight(FakeApi(blocked), self.snapshot, self.snapshot)

    def test_remaining_configuration_and_binding_must_match(self):
        after = copy.deepcopy(self.snapshot)
        after["components"].pop(0)
        retire.verify_remaining(self.snapshot, after, {"0"})
        after["reference"]["connectionid"] = "different"
        with self.assertRaisesRegex(RuntimeError, "connection-binding"):
            retire.verify_remaining(self.snapshot, after, {"0"})


if __name__ == "__main__":
    unittest.main()

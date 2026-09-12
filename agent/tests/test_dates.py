import datetime as dt
from pathlib import Path
import unittest

import yaml

from analytics import DEFAULTS, DATE_CONVENTION, LAST_30_PATTERN, build_advice_topic, build_query, build_topic, validate_request

ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
FIXTURE = dt.datetime(2026, 9, 12, 13, 32, tzinfo=UTC)


class DateTests(unittest.TestCase):
    def test_last_30_calendar_dates_include_today(self):
        p = validate_request({"relativePeriod": "last30Days"}, now=FIXTURE)
        self.assertEqual((p["startDate"], p["endDate"]), ("2026-08-14", "2026-09-12"))
        self.assertEqual((dt.date.fromisoformat(p["endDate"]) - dt.date.fromisoformat(p["startDate"])).days + 1, 30)
        query = build_query({"metric": "interactions", "groupBy": "agent", "relativePeriod": "last30Days", "topN": 100}, now=FIXTURE)
        self.assertIn("DATESBETWEEN('Date'[Date], DATE(2026,8,14), DATE(2026,9,12))", query)
        self.assertIn("TOPN(100,", query)
        self.assertIn('"RequestedStartDate", "2026-08-14"', query)
        self.assertIn('"RequestedEndDate", "2026-09-12"', query)

    def test_month_year_and_leap_transitions(self):
        for end, start in (("2026-03-01", "2026-01-31"), ("2024-03-01", "2024-02-01"), ("2026-01-01", "2025-12-03")):
            with self.subTest(end=end):
                clock = dt.datetime.fromisoformat(end).replace(tzinfo=UTC)
                p = validate_request({"relativePeriod": "last30Days"}, now=clock)
                self.assertEqual((p["startDate"], p["endDate"]), (start, end))

    def test_timezone_midnight_uses_utc_not_local_calendar(self):
        for clock, start, end in (
            (dt.datetime(2026, 9, 12, 0, 30, tzinfo=dt.timezone(dt.timedelta(hours=1))), "2026-08-13", "2026-09-11"),
            (dt.datetime(2026, 9, 11, 23, 30, tzinfo=dt.timezone(dt.timedelta(hours=-7))), "2026-08-14", "2026-09-12"),
        ):
            with self.subTest(clock=clock):
                p = validate_request({"relativePeriod": "last30Days"}, now=clock)
                self.assertEqual((p["startDate"], p["endDate"]), (start, end))
        with self.assertRaisesRegex(ValueError, "aware runtime clock"):
            validate_request({"relativePeriod": "last30Days"}, now=dt.datetime(2026, 9, 12))

    def test_conflicts_unknown_relative_and_unresolved_dates_fail_closed(self):
        for request in (
            {"relativePeriod": "last30Days", "startDate": "2026-08-14", "endDate": "2026-09-12"},
            {"relativePeriod": "last30Days", "endDate": "2026-09-12"},
            {"relativePeriod": "last7Days"},
            {"relativePeriod": "clarify"},
            {"relativePeriod": ""},
            {"ClockUtc": "2030-01-01"},
            {"metric": "agents", "relativePeriod": "last30Days"},
        ):
            with self.subTest(request=request), self.assertRaises(ValueError):
                build_query(request, now=FIXTURE)
        for prompt in ("Top agents last month", "Top agents between 2026-08-14 and 2026-09-12", "Usage for August 2026"):
            with self.subTest(prompt=prompt), self.assertRaisesRegex(ValueError, "no resolved dates"):
                build_query({}, now=FIXTURE, utterance=prompt)
        for prompt in ("last 30 days in BST", "last 30 days of latest available data", "last 30 days in local time"):
            with self.subTest(prompt=prompt), self.assertRaisesRegex(ValueError, "UTC calendar"):
                build_query({}, now=FIXTURE, utterance=prompt)

    def test_literal_relative_request_is_resolved_even_if_input_defaults_none(self):
        p = validate_request({}, now=FIXTURE, utterance="Give me the top agents and their usage over the last 30 days")
        self.assertEqual(p["relativePeriod"], "last30Days")
        self.assertEqual(p["startDate"], "2026-08-14")
        explicit = {"startDate": "2026-08-01", "endDate": "2026-08-31"}
        self.assertEqual(validate_request(explicit)["startDate"], explicit["startDate"])
        self.assertIn("DATE(2026,8,1), DATE(2026,8,31)", build_query(explicit))
        self.assertEqual(validate_request({})["startDate"], "")

    def test_power_fx_resolves_before_validation_and_query_in_both_modes(self):
        for topic in (build_topic(), build_advice_topic()):
            with self.subTest(topic=topic["modelDisplayName"]):
                actions = topic["beginDialog"]["actions"]
                by_id = {a["id"]: a for a in actions}
                ids = list(by_id)
                self.assertEqual(by_id["setClockUtc"]["value"], "=Now()")
                self.assertIn("Year(Topic.ClockUtc)", by_id["setAnchorUtcDate"]["value"])
                self.assertIn("DateAdd(Topic.AnchorUtcDate, -29, TimeUnit.Days)", by_id["setstartDate"]["value"])
                self.assertIn("Text(Topic.AnchorUtcDate", by_id["setendDate"]["value"])
                self.assertIn(LAST_30_PATTERN, by_id["setrelativePeriod"]["value"])
                self.assertLess(ids.index("ValidateRelativePeriod"), ids.index("setstartDate"))
                self.assertLess(ids.index("setendDate"), ids.index("ValidateDates"))
                self.assertLess(ids.index("ValidateDates"), ids.index("setDax"))
                self.assertIn("Year(DateValue(Topic.startDate", by_id["setFilterDax"]["value"])
                self.assertIn("Year(DateValue(Topic.endDate", by_id["setFilterDax"]["value"])
                self.assertIn('"RequestedStartDate"', by_id["setMetadataDax"]["value"])
                self.assertIn('"RequestedEndDate"', by_id["setMetadataDax"]["value"])
                self.assertNotIn("ClockUtc", topic["inputType"]["properties"])
                self.assertEqual(set(topic["inputType"]["properties"]), set(DEFAULTS) - {"mode"})

    def test_empty_and_partial_window_explanations_do_not_claim_coverage_or_widening(self):
        query = build_query({"relativePeriod": "last30Days"}, now=FIXTURE)
        self.assertIn('"WindowStart", __Start, "WindowEnd", __End', query)
        self.assertIn(DATE_CONVENTION, query)
        self.assertIn("COALESCE(COUNTROWS(__Summary), 0)", query)
        topic = build_topic()
        context = next(a for a in topic["beginDialog"]["actions"] if a["id"] == "setqueryContext")["value"]
        self.assertIn("not refresh timestamps or continuous coverage", context)
        self.assertIn("no matching recorded events", context)
        self.assertIn("never widen the interval", context)

    def test_routing_contract_prefers_reusable_for_dates_filters_and_other_limits(self):
        agent = yaml.safe_load((ROOT / "agent.mcs.yml").read_text(encoding="utf-8"))
        self.assertLessEqual(len(agent["instructions"]), 8000)
        for phrase in ("Date-scoped rankings are available NOW", "Dated top100 uses topN=100", "relativePeriod=last30Days", "BOTH dates blank", "ONLY for unfiltered, undated/all-history top100"):
            self.assertIn(phrase, agent["instructions"])
        fixed = yaml.safe_load((ROOT / "actions" / "PowerBITopAgentsByUsage.mcs.yml").read_text(encoding="utf-8"))
        self.assertIn("ONLY for the exact unfiltered, undated top 100", fixed["modelDescription"])
        self.assertIn("NOT for last 30 days", fixed["modelDescription"])
        generic = build_topic()
        self.assertTrue(generic["beginDialog"]["intent"]["includeInOnSelectIntent"])
        self.assertIn("Give me the top agents and their usage over the last 30 days", generic["beginDialog"]["intent"]["triggerQueries"])
        self.assertIn("UTC runtime resolver", build_advice_topic()["modelDescription"])


if __name__ == "__main__":
    unittest.main()

"""Authorized direct Power BI date tests; no business rows or values are printed. Not chat E2E."""
import datetime as dt
import importlib.util
import json
from pathlib import Path

from analytics import build_query, validate_request

spec = importlib.util.spec_from_file_location("verify_model", Path(__file__).with_name("verify-model.py"))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run(parameters, clock):
    rows = model.query_rows(build_query(parameters, now=clock))
    summaries = [r for r in rows if r["[RowType]"] == "Summary"]
    data = [r for r in rows if r["[RowType]"] == "Data"]
    assert len(summaries) == 1
    summary = summaries[0]
    expected = validate_request(parameters, now=clock)
    assert summary["[RequestedStartDate]"] == expected["startDate"]
    assert summary["[RequestedEndDate]"] == expected["endDate"]
    assert summary["[ReturnedGroups]"] == len(data) <= expected["topN"]
    assert summary["[HasMore]"] == (summary["[TotalGroups]"] > len(data))
    if expected["startDate"] and summary.get("[WindowStart]"):
        assert expected["startDate"] <= summary["[WindowStart]"][:10]
        assert summary["[WindowEnd]"][:10] <= expected["endDate"]
    return summary, data


def main():
    clock = dt.datetime.now(dt.timezone.utc)
    resolved = validate_request({"relativePeriod": "last30Days"}, now=clock)
    all_summary, all_data = run({"metric": "interactions"}, clock)
    period_summary, period_data = run({"metric": "interactions", "relativePeriod": "last30Days"}, clock)
    assert sum(r["[Value]"] for r in period_data) <= sum(r["[Value]"] for r in all_data)
    print(json.dumps({"case": "all_history_vs_runtime_30_days", "directQuery": "PASS", "valuesPublished": False}))
    relative = {"metric": "interactions", "groupBy": "agent", "sortBy": "value", "topN": 100, "relativePeriod": "last30Days"}
    relative_summary, relative_rows = run(relative, clock)
    explicit = {k: v for k, v in relative.items() if k != "relativePeriod"}
    explicit.update(startDate=resolved["startDate"], endDate=resolved["endDate"])
    explicit_summary, explicit_rows = run(explicit, clock)
    project = lambda rows: [(r["[GroupKey]"], r["[Value]"]) for r in rows]
    assert project(relative_rows) == project(explicit_rows)
    assert [r["[Value]"] for r in relative_rows] == sorted([r["[Value]"] for r in relative_rows], reverse=True)
    print(json.dumps({
        "case": "explicit_vs_runtime_relative_agent_ranking", "directQuery": "PASS",
        "requestedStartDate": resolved["startDate"], "requestedEndDate": resolved["endDate"],
        "rowCount": len(relative_rows), "businessRowsPublished": False,
        "observedEndPrecedesRequestedEnd": bool(relative_summary.get("[WindowEnd]") and relative_summary["[WindowEnd]"][:10] < resolved["endDate"]),
        "continuousCoverageOrRefreshTimeEstablished": False,
    }))
    if all_summary.get("[WindowEnd]"):
        # This constructs an explicit empty-test interval, not the production relative-date anchor.
        start = dt.date.fromisoformat(all_summary["[WindowEnd]"][:10]) + dt.timedelta(days=1)
        empty_parameters = {"metric": "interactions", "groupBy": "agent", "startDate": start.isoformat(), "endDate": (start + dt.timedelta(days=29)).isoformat()}
        summary, rows = run(empty_parameters, clock)
        assert rows == [] and summary["[TotalGroups]"] == 0
        assert not summary.get("[WindowStart]") and not summary.get("[WindowEnd]")
        print(json.dumps({"case": "empty_explicit_window", "directQuery": "PASS", "requestedIntervalPreserved": True, "allHistorySubstitution": False}))
    print("Direct date checks passed; actual chat tool selection/arguments/results remain a separate test.")


if __name__ == "__main__":
    main()

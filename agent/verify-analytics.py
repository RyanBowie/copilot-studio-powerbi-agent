"""Direct query validation for the reusable compiler; this is not a chat E2E test."""
import importlib.util
import json
from pathlib import Path

from analytics import build_query

spec = importlib.util.spec_from_file_location("verify_model", Path(__file__).with_name("verify-model.py"))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

SCENARIOS = [
    {"metric": "interactions", "groupBy": "platform", "startDate": "2026-08-01", "endDate": "2026-08-31"},
    {"metric": "agents", "groupBy": "risk"},
    {"metric": "sessions", "groupBy": "month", "sortBy": "group"},
    {"metric": "users", "groupBy": "host", "topN": 3},
    {"metric": "environments", "groupBy": "environmentType"},
    {"metric": "interactions", "groupBy": "total", "filterBy": "platform", "filterValue": "Copilot Studio"},
    {"metric": "interactions", "filterBy": "platform", "filterValue": 'nonexistent"}), EVALUATE \'User\' //'},
]


def main():
    for parameters in SCENARIOS:
        rows = model.query_rows(build_query(parameters))
        summaries = [row for row in rows if row["[RowType]"] == "Summary"]
        data = [row for row in rows if row["[RowType]"] == "Data"]
        assert len(summaries) == 1 and len(rows) <= 101
        summary = summaries[0]
        assert len(data) == summary["[ReturnedGroups]"]
        assert summary["[HasMore]"] == (summary["[TotalGroups]"] > summary["[ReturnedGroups]"])
        assert len({row["[GroupKey]"] for row in data}) == len(data)
        assert all(row["[Value]"] > 0 for row in data)
        assert all(set(row) <= {
            "[RowType]", "[Group]", "[GroupKey]", "[Value]", "[Metric]", "[GroupBy]",
            "[TotalGroups]", "[ReturnedGroups]", "[HasMore]", "[WindowStart]", "[WindowEnd]",
        } for row in rows)
        if "nonexistent" in parameters.get("filterValue", ""):
            assert not data, "Escaped injection-like value must not become executable DAX."
        print(json.dumps({
            "parameters": parameters, "summary": summary, "dataRows": len(data),
            "directQuery": "PASS", "chatEndToEnd": "NOT_TESTED_BY_THIS_SCRIPT",
        }))


if __name__ == "__main__":
    main()

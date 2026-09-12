"""LLM-authored varied DAX fixtures, applied to the generic contract. Direct tests, NOT cloud chat proof."""
import json
import math
from pathlib import Path

import yaml

from generated_dax import build_query, validate_result
from general_runtime import schema_probe
from powerbi_client import QueryError, query_rows

ROOT = Path(__file__).resolve().parent


def check(label, request):
    summary, data = validate_result(query_rows(build_query(request)))
    print(json.dumps({"case": label, "directApi": "PASS", "businessRowsPublished": False,
                      "rows": len(data), "hasMore": summary["[__hasMore]"], "chatEndToEnd": False}))
    return summary, data


def main():
    schema = json.loads((ROOT / "model-schema.private.json").read_text(encoding="utf-8"))
    assert query_rows(schema_probe(schema)) == [{"[AccessProbe]": 1}]
    print("Current-caller full prepared-column probe: PASS (no business rows).")
    multi = {
        "tableExpression": """SUMMARIZECOLUMNS('Agent'[Platform], 'Agent'[AuthoringSurface],
            FILTER('Agent', 'Agent'[ToolCount] > 0 && 'Agent'[KnowledgeCount] > 0),
            "Agents", COUNTROWS('Agent'), "AverageRisk", AVERAGE('Agent'[RiskScore]))""",
        "columns": "Platform,AuthoringSurface,Agents,AverageRisk", "sortBy": "Agents desc", "limit": 100,
    }
    summary, rows = check("multiple_groupings_and_multiple_filters", multi)
    total = query_rows("""EVALUATE ROW("Expected", COUNTROWS(FILTER('Agent', 'Agent'[ToolCount] > 0 && 'Agent'[KnowledgeCount] > 0)))""")[0]["[Expected]"]
    if not summary["[__hasMore]"]:
        assert sum(r["[Agents]"] for r in rows) == total
    _, rows = check("derived_tool_intensity", {
        "tableExpression": """ROW("Tools", SUM('Agent'[ToolCount]), "Agents", COUNTROWS('Agent'),
            "ToolsPerAgent", DIVIDE(SUM('Agent'[ToolCount]), COUNTROWS('Agent')))""",
        "columns": "Tools,Agents,ToolsPerAgent",
    })
    assert math.isclose(rows[0]["[ToolsPerAgent]"], rows[0]["[Tools]"] / rows[0]["[Agents]"])
    check("authorized_owner_and_creator_fields_as_aggregates", {
        "tableExpression": """ROW("DistinctOwners", DISTINCTCOUNT('Agent'[OwnerUpn]),
            "DistinctCreators", DISTINCTCOUNT('Agent'[CreatedBy]),
            "NamedCreators", COUNTROWS(FILTER('Agent', NOT ISBLANK('Agent'[CreatedByName]))))""",
        "columns": "DistinctOwners,DistinctCreators,NamedCreators",
    })
    ranking_expression = """FILTER(SUMMARIZECOLUMNS('Agent'[AgentKey], 'Agent'[AgentName],
        "Interactions", [Interactions]), NOT ISBLANK('Agent'[AgentKey]) && [Interactions] > 0)"""
    _, ranking = check("familiar_top100_without_fixed_runtime_dependency", {
        "tableExpression": ranking_expression, "columns": "AgentKey,AgentName,Interactions",
        "sortBy": "Interactions desc,AgentKey asc", "limit": 100,
    })
    legacy = ROOT / "legacy" / "actions" / "PowerBITopAgentsByUsage.mcs.yml"
    if legacy.exists():
        old = yaml.safe_load(legacy.read_text(encoding="utf-8"))
        baseline = query_rows(next(i["value"] for i in old["inputs"] if i["propertyName"] == "query"))
        assert [(r["[AgentKey]"], r["[Interactions]"]) for r in ranking] == [(r["[AgentKey]"], r["[Interactions]"]) for r in baseline]
        print("Original top100 membership and ordering regression: PASS; no names/values printed.")
    check("explicit_date_ranking", {
        "tableExpression": """FILTER(SUMMARIZECOLUMNS('Agent'[AgentKey], 'Agent'[AgentName],
            DATESBETWEEN('Date'[Date], QUERY_START, QUERY_END), "Interactions", [Interactions]),
            NOT ISBLANK('Agent'[AgentKey]) && [Interactions] > 0)""",
        "columns": "AgentKey,AgentName,Interactions", "sortBy": "Interactions desc,AgentKey asc", "limit": 100,
        "startDateExpression": "DATE(2026,8,14)", "endDateExpression": "DATE(2026,9,12)",
    })
    summary, _ = check("relative_complete_month_comparison", {
        "tableExpression": """UNION(
            ROW("Period", "Previous complete month", "Interactions",
                CALCULATE([Interactions], DATESBETWEEN('Date'[Date], QUERY_START, EOMONTH(QUERY_END,-1)))),
            ROW("Period", "Current month to date", "Interactions",
                CALCULATE([Interactions], DATESBETWEEN('Date'[Date], EOMONTH(QUERY_END,-1)+1, QUERY_END))))""",
        "columns": "Period,Interactions",
        "startDateExpression": "EOMONTH(UTC_TODAY,-2)+1", "endDateExpression": "UTC_TODAY",
    })
    assert summary["[__requestedEnd]"] == summary["[__anchorUtc]"]
    check("different_model_table_not_in_old_contract", {
        "tableExpression": """SUMMARIZECOLUMNS('ShadowAiSignal'[Layer], 'ShadowAiSignal'[Category],
            "Devices", SUM('ShadowAiSignal'[DeviceCount]), "Users", SUM('ShadowAiSignal'[UserCount]))""",
        "columns": "Layer,Category,Devices,Users", "sortBy": "Devices desc", "limit": 100,
    })
    _, empty = check("empty_results_have_successful_zero_row_envelope", {
        "tableExpression": """SELECTCOLUMNS(FILTER('Agent', FALSE()), "Key", 'Agent'[AgentKey])""", "columns": "Key"})
    assert empty == []
    try:
        query_rows(build_query({"tableExpression": """ROW("Invalid", SUM('Agent'[DefinitelyMissing_Probe]))""", "columns": "Invalid"}))
    except QueryError:
        print("Unsupported-column provider error: observed and rejected, not fabricated success or a permissions claim.")
    else:
        raise AssertionError("Expected a real unsupported-field error.")
    print("All direct generated-expression checks passed. Cloud LLM generation/tool arguments/answers require separate chat evidence.")


if __name__ == "__main__":
    main()

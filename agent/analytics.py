"""Allowlisted aggregate query compiler and its equivalent executable Power Fx topic."""
import datetime as dt
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
from config import load_config
CONFIG = load_config()
METRICS = {
    "interactions": "[Interactions]",
    "sessions": "[Interaction Sessions]",
    "users": "[Interaction Users]",
    "agents": "COUNTROWS('Agent')",
    "environments": "DISTINCTCOUNT('Agent'[EnvironmentId])",
}
GROUPS = {
    "total": ("", '"Total"', '"Total"'),
    "platform": ("'Agent'[Platform]", "'Agent'[Platform]", "'Agent'[Platform]"),
    "environment": (
        "'Agent'[EnvironmentId], 'Agent'[EnvironmentName]",
        "'Agent'[EnvironmentName]", "'Agent'[EnvironmentId]",
    ),
    "region": ("'Agent'[Region]", "'Agent'[Region]", "'Agent'[Region]"),
    "environmentType": ("'Agent'[EnvironmentType]", "'Agent'[EnvironmentType]", "'Agent'[EnvironmentType]"),
    "risk": ("'Agent'[RiskBand]", "'Agent'[RiskBand]", "'Agent'[RiskBand]"),
    "activity": ("'Agent'[ActivityStatus]", "'Agent'[ActivityStatus]", "'Agent'[ActivityStatus]"),
    "agent": ("'Agent'[AgentKey], 'Agent'[AgentName]", "'Agent'[AgentName]", "'Agent'[AgentKey]"),
    "month": ("'Date'[YearMonth]", "'Date'[YearMonth]", "'Date'[YearMonth]"),
    "day": ("'Date'[Date]", 'FORMAT(\'Date\'[Date], "yyyy-MM-dd")', 'FORMAT(\'Date\'[Date], "yyyy-MM-dd")'),
    "host": ("'Interaction'[AppHost]", "'Interaction'[AppHost]", "'Interaction'[AppHost]"),
}
FILTERS = {
    "none": "",
    "platform": "'Agent'[Platform]",
    "environment": "'Agent'[EnvironmentName]",
    "environmentType": "'Agent'[EnvironmentType]",
    "region": "'Agent'[Region]",
    "risk": "'Agent'[RiskBand]",
    "activity": "'Agent'[ActivityStatus]",
    "agent": "'Agent'[AgentKey]",
    "agentName": "'Agent'[AgentName]",
    "host": "'Interaction'[AppHost]",
}
DEFAULTS = {
    "metric": "interactions", "groupBy": "total", "filterBy": "none", "filterValue": "",
    "startDate": "", "endDate": "", "topN": 20, "sortBy": "value", "mode": "execute",
}
SCOPE_LIMIT = "Unavailable through this PoC's approved tools does not establish whether a field exists in the underlying custom semantic model."
IDENTITY_SCOPE = (
    "Owner and creator identities are outside this PoC's approved analytics scope, so the current tools cannot return that table. "
    "That does not establish whether those fields exist in the underlying custom semantic model. "
    "I can provide approved agent-level aggregates. No identity query is run or recommended."
)


def literal(value):
    return '"' + value.replace('"', '""') + '"'


def validate_request(request):
    if set(request) - set(DEFAULTS):
        raise ValueError("Unknown approved-tool parameter; raw DAX and model identifiers are not accepted. " + SCOPE_LIMIT)
    p = {**DEFAULTS, **request}
    if p["metric"] not in METRICS or p["groupBy"] not in GROUPS or p["filterBy"] not in FILTERS:
        raise ValueError("Metric, grouping, or filter is outside the approved analytics contract. " + SCOPE_LIMIT)
    if p["mode"] not in ("execute", "dax") or p["sortBy"] not in ("value", "group"):
        raise ValueError("Unsupported mode or sorting.")
    if isinstance(p["topN"], bool) or not isinstance(p["topN"], (int, float)) or int(p["topN"]) != p["topN"] or not 1 <= p["topN"] <= 100:
        raise ValueError("topN must be an integer from 1 to 100.")
    p["topN"] = int(p["topN"])
    if not isinstance(p["filterValue"], str) or len(p["filterValue"]) > 128:
        raise ValueError("Filter values must be text of at most 128 characters.")
    if (p["filterBy"] == "none") != (p["filterValue"] == ""):
        raise ValueError("Supply both an approved filter and an exact value, or neither.")
    if bool(p["startDate"]) != bool(p["endDate"]):
        raise ValueError("Provide both dates or neither.")
    if p["startDate"]:
        start, end = (dt.date.fromisoformat(p[key]) for key in ("startDate", "endDate"))
        if start.year < 1900 or start.isoformat() != p["startDate"] or end.isoformat() != p["endDate"] or not 0 <= (end - start).days <= 365:
            raise ValueError("Use ISO dates and an inclusive range of at most 366 days.")
    if p["metric"] in ("agents", "environments") and (p["groupBy"] in ("month", "day", "host") or p["filterBy"] == "host" or p["startDate"]):
        raise ValueError("Inventory metrics describe the current snapshot; audit dates and host dimensions do not apply.")
    return p


def date_literal(value):
    date = dt.date.fromisoformat(value)
    return f"DATE({date.year},{date.month},{date.day})"


def build_query(request):
    p = validate_request(request)
    columns, label, key = GROUPS[p["groupBy"]]
    metric = METRICS[p["metric"]]
    source = (f'SUMMARIZECOLUMNS({columns}, "Value", {metric})'
              if columns else f'ROW("Value", {metric})')
    base = f'SELECTCOLUMNS({source}, "Group", COALESCE({label}, "(blank)"), "GroupKey", COALESCE({key}, "(blank)"), "Value", [Value])'
    filters = ""
    if p["filterBy"] != "none":
        filters += f', TREATAS({{{literal(p["filterValue"])}}}, {FILTERS[p["filterBy"]]})'
    if p["startDate"]:
        filters += f", DATESBETWEEN('Date'[Date], {date_literal(p['startDate'])}, {date_literal(p['endDate'])})"
    start = "BLANK()" if p["metric"] in ("agents", "environments") else f"CALCULATE([First Interaction]{filters})"
    end = "BLANK()" if p["metric"] in ("agents", "environments") else f"CALCULATE([Last Interaction]{filters})"
    excluded = ' && [GroupKey] <> "(blank)"' if p["groupBy"] == "agent" else ""
    sort = "[Value], DESC, [GroupKey], ASC" if p["sortBy"] == "value" else "[GroupKey], ASC"
    order = sort.replace(", DESC", " DESC").replace(", ASC", " ASC")
    metadata = (
        f'"Metric", "{p["metric"]}", "GroupBy", "{p["groupBy"]}", '
        f'"TotalGroups", __Count, "ReturnedGroups", MIN(__Count, {p["topN"]}), '
        f'"HasMore", __Count > {p["topN"]}, "WindowStart", __Start, "WindowEnd", __End'
    )
    return (
        f"DEFINE VAR __Summary = FILTER(CALCULATETABLE({base}{filters}), NOT ISBLANK([Value]) && [Value] > 0{excluded}) "
        f"VAR __Count = COALESCE(COUNTROWS(__Summary), 0) VAR __Start = {start} VAR __End = {end} "
        f"VAR __Rows = TOPN({p['topN']}, __Summary, {sort}) "
        f'EVALUATE UNION(ROW("RowType", "Summary", "Group", "", "GroupKey", "", "Value", BLANK(), {metadata}), '
        f'SELECTCOLUMNS(__Rows, "RowType", "Data", "Group", [Group], "GroupKey", [GroupKey], "Value", [Value], {metadata})) '
        f"ORDER BY [RowType] DESC, {order}"
    )


def fx_switch(variable, mapping):
    parts = [f"Topic.{variable}"]
    for key, value in mapping.items():
        parts.extend([literal(key), literal(value)])
    parts.append('""')
    return "=Switch(" + ", ".join(parts) + ")"


def set_variable(name, expression):
    return {"kind": "SetVariable", "id": "set" + name, "variable": "Topic." + name, "value": expression}


def rejection(identifier, condition, message):
    return {
        "kind": "ConditionGroup", "id": identifier,
        "conditions": [{
            "id": identifier + "Invalid", "condition": condition,
            "actions": [
                {"kind": "SendActivity", "id": identifier + "Message", "activity": message},
                {"kind": "EndDialog", "id": identifier + "Stop"},
            ],
        }],
    }


def _build_base_topic():
    descriptions = {
        "metric": "Metric: interactions (audited turns), sessions (distinct threads), users (distinct user count, never identities), agents (inventory row count), environments (distinct environments represented in inventory).",
        "groupBy": "One grouping: total, platform, environment, environmentType, region, risk, activity, agent, month, day, or host. Inventory metrics cannot use month/day/host.",
        "filterBy": "Optional single exact-equality filter: none, platform, environment (display name), environmentType, region, risk, activity, agent (AgentKey), agentName (exact name, combines duplicate names), host. Use none if not requested.",
        "filterValue": "Exact text value of the requested filter, at most 128 characters. Leave blank with filterBy=none. Never use DAX here.",
        "startDate": "Inclusive audit start date YYYY-MM-DD, or blank for all available audit data. Both dates required together. Not supported for inventory metrics.",
        "endDate": "Inclusive audit end date YYYY-MM-DD, or blank. Range must be no more than 366 inclusive days. Do not invent requested dates.",
        "topN": "Maximum aggregate groups, integer 1 through 100. Default 20. Result explicitly reports TotalGroups and HasMore.",
        "sortBy": "value for highest metric first; group for ascending category/date order (use for time trends).",
        "mode": "execute for a data question, dax for advice-only DAX writing/explanation. dax returns compiled model-specific DAX without executing it.",
    }
    inputs = [
        {"kind": "AutomaticTaskInput", "propertyName": name, "description": descriptions[name],
         "entity": "NumberPrebuiltEntity" if name == "topN" else "StringPrebuiltEntity",
         "shouldPromptUser": False, "defaultValue": default}
        for name, default in DEFAULTS.items()
    ]
    properties = {name: {"type": "Number" if name == "topN" else "String", "description": descriptions[name]} for name in DEFAULTS}
    for name, values in {"metric": list(METRICS), "groupBy": list(GROUPS), "filterBy": list(FILTERS), "sortBy": ["value", "group"]}.items():
        properties[name]["enumValues"] = values
    properties["metric"]["isRequired"] = True
    metric_input = next(item for item in inputs if item["propertyName"] == "metric")
    metric_input["shouldPromptUser"] = True
    del metric_input["defaultValue"]
    conditions = [
        f'!(Topic.metric in {json.dumps(list(METRICS))})',
        f'!(Topic.groupBy in {json.dumps(list(GROUPS))})',
        f'!(Topic.filterBy in {json.dumps(list(FILTERS))})',
        '!(Topic.mode in ["execute", "dax"])',
        '!(Topic.sortBy in ["value", "group"])',
        "Topic.topN < 1", "Topic.topN > 100", "Topic.topN <> RoundDown(Topic.topN, 0)",
        "Len(Topic.filterValue) > 128",
        '(Topic.filterBy = "none" && !IsBlank(Topic.filterValue))',
        '(Topic.filterBy <> "none" && IsBlank(Topic.filterValue))',
        "IsBlank(Topic.startDate) <> IsBlank(Topic.endDate)",
    ]
    actions = [
        rejection("ValidateParameters", "=" + " || ".join(conditions),
                  "These inputs are outside the approved tool contract or its limits; no query is run or recommended. " + SCOPE_LIMIT + " Owner/creator identities and transcripts are excluded from this PoC, including DAX advice. Approved alternatives are interaction/session/distinct-user counts or current agent/inventory-environment counts, one approved grouping/filter, limit 1–100 and paired ISO audit dates."),
        rejection("ValidateInventoryContext",
                  '=Topic.metric in ["agents", "environments"] && (Topic.groupBy in ["month", "day", "host"] || Topic.filterBy = "host" || !IsBlank(Topic.startDate))',
                  "Inventory counts are a current snapshot. Audit dates and client hosts apply only to interaction/session/user metrics. The Agent creation-date relationship is inactive, so I will not mislabel inventory counts as historical usage. Choose an audit metric or remove those dimensions/dates."),
        rejection("ValidateDates",
                  '=!IsBlank(Topic.startDate) && (!IsMatch(Topic.startDate, "\\d{4}-\\d{2}-\\d{2}") || !IsMatch(Topic.endDate, "\\d{4}-\\d{2}-\\d{2}") || IfError(IsBlank(DateValue(Topic.startDate, "en-US")) || IsBlank(DateValue(Topic.endDate, "en-US")) || Year(DateValue(Topic.startDate, "en-US")) < 1900 || Text(DateValue(Topic.startDate, "en-US"), "yyyy-mm-dd", "en-US") <> Topic.startDate || Text(DateValue(Topic.endDate, "en-US"), "yyyy-mm-dd", "en-US") <> Topic.endDate || DateValue(Topic.startDate, "en-US") > DateValue(Topic.endDate, "en-US") || DateDiff(DateValue(Topic.startDate, "en-US"), DateValue(Topic.endDate, "en-US")) > 365, true))',
                  "Please supply valid start and end dates as YYYY-MM-DD, in order, spanning at most 366 inclusive days. No query has been run."),
        set_variable("MetricDax", fx_switch("metric", METRICS)),
        set_variable("GroupColumns", fx_switch("groupBy", {k: v[0] for k, v in GROUPS.items()})),
        set_variable("GroupLabel", fx_switch("groupBy", {k: v[1] for k, v in GROUPS.items()})),
        set_variable("GroupKey", fx_switch("groupBy", {k: v[2] for k, v in GROUPS.items()})),
        set_variable("FilterColumn", fx_switch("filterBy", FILTERS)),
        set_variable("FilterDax",
                     '=If(Topic.filterBy = "none", "", ", TREATAS({" & Char(34) & Substitute(Topic.filterValue, Char(34), Char(34) & Char(34)) & Char(34) & "}, " & Topic.FilterColumn & ")") & If(IsBlank(Topic.startDate), "", ", DATESBETWEEN(\'Date\'[Date], DATE(" & Text(Year(DateValue(Topic.startDate, "en-US")), "0", "en-US") & "," & Text(Month(DateValue(Topic.startDate, "en-US")), "0", "en-US") & "," & Text(Day(DateValue(Topic.startDate, "en-US")), "0", "en-US") & "), DATE(" & Text(Year(DateValue(Topic.endDate, "en-US")), "0", "en-US") & "," & Text(Month(DateValue(Topic.endDate, "en-US")), "0", "en-US") & "," & Text(Day(DateValue(Topic.endDate, "en-US")), "0", "en-US") & "))")'),
        set_variable("BaseDax",
                     '= "SELECTCOLUMNS(" & If(Topic.groupBy = "total", "ROW(""Value"", " & Topic.MetricDax & ")", "SUMMARIZECOLUMNS(" & Topic.GroupColumns & ", ""Value"", " & Topic.MetricDax & ")") & ", ""Group"", COALESCE(" & Topic.GroupLabel & ", ""(blank)""), ""GroupKey"", COALESCE(" & Topic.GroupKey & ", ""(blank)""), ""Value"", [Value])"'),
        set_variable("StartDax", '=If(Topic.metric in ["agents", "environments"], "BLANK()", "CALCULATE([First Interaction]" & Topic.FilterDax & ")")'),
        set_variable("EndDax", '=If(Topic.metric in ["agents", "environments"], "BLANK()", "CALCULATE([Last Interaction]" & Topic.FilterDax & ")")'),
        set_variable("SortDax", '=If(Topic.sortBy = "value", "[Value], DESC, [GroupKey], ASC", "[GroupKey], ASC")'),
        set_variable("OrderDax", '=Substitute(Substitute(Topic.SortDax, ", DESC", " DESC"), ", ASC", " ASC")'),
        set_variable("LimitText", '=Text(Topic.topN, "0", "en-US")'),
        set_variable("MetadataDax",
                     '="""Metric"", """ & Topic.metric & """, ""GroupBy"", """ & Topic.groupBy & """, ""TotalGroups"", __Count, ""ReturnedGroups"", MIN(__Count, " & Topic.LimitText & "), ""HasMore"", __Count > " & Topic.LimitText & ", ""WindowStart"", __Start, ""WindowEnd"", __End"'),
        set_variable("Dax",
                     '="DEFINE VAR __Summary = FILTER(CALCULATETABLE(" & Topic.BaseDax & Topic.FilterDax & "), NOT ISBLANK([Value]) && [Value] > 0" & If(Topic.groupBy = "agent", " && [GroupKey] <> ""(blank)""", "") & ") VAR __Count = COALESCE(COUNTROWS(__Summary), 0) VAR __Start = " & Topic.StartDax & " VAR __End = " & Topic.EndDax & " VAR __Rows = TOPN(" & Topic.LimitText & ", __Summary, " & Topic.SortDax & ") EVALUATE UNION(ROW(""RowType"", ""Summary"", ""Group"", """", ""GroupKey"", """", ""Value"", BLANK(), " & Topic.MetadataDax & "), SELECTCOLUMNS(__Rows, ""RowType"", ""Data"", ""Group"", [Group], ""GroupKey"", [GroupKey], ""Value"", [Value], " & Topic.MetadataDax & ")) ORDER BY [RowType] DESC, " & Topic.OrderDax'),
        {
            "kind": "ConditionGroup", "id": "AdviceOnly",
            "conditions": [{
                "id": "ReturnUnexecutedDax", "condition": '=Topic.mode = "dax"',
                "actions": [
                    {"kind": "SendActivity", "id": "ExplainDax", "activity": "Model-grounded DAX suggestion — NOT EXECUTED. This compiles your allowed metric/grouping/filter/date inputs. Summary rows disclose result limits and the available audit window; Data rows are aggregates. Date filters use the active Date-to-Interaction relationship, not the inactive Agent creation-date relationship.\n```dax\n{Topic.Dax}\n```"},
                    {"kind": "EndDialog", "id": "EndAdvice"},
                ],
            }],
        },
        {
            "kind": "InvokeConnectorAction", "id": "ExecuteStructuredQuery",
            "connectionReference": CONFIG["connectionReference"],
            "connectionProperties": {"mode": "Invoker"}, "operationId": "ExecuteDatasetQuery",
            "requestTimeoutInMilliseconds": 30000,
            "input": {"binding": {
                "groupid": CONFIG["workspaceId"],
                "datasetid": CONFIG["datasetId"],
                "query": "=Topic.Dax", "impersonatedUserName": "=Blank()",
            }},
            "output": {"binding": {"firstTableRows": "Topic.Rows"}},
        },
        rejection("ValidateQueryResponse", "=IsEmpty(Topic.Rows) || CountRows(Topic.Rows) > 101",
                  "The connector did not return the expected bounded response with a Summary row. This is an execution/response error, not evidence of zero usage or absent fields. Actual permission errors are access issues, not model absence. No successful analytics result is claimed."),
        set_variable("result", "=Topic.Rows"),
        set_variable("generatedDax", "=Topic.Dax"),
        set_variable("queryContext", '="Metric=" & Topic.metric & "; grouping=" & Topic.groupBy & "; exact filter=" & Topic.filterBy & ":" & Topic.filterValue & "; requested inclusive audit dates=" & Topic.startDate & ".." & Topic.endDate & ". Blank dates mean all available data; inventory has no audit window. Use Summary.TotalGroups/ReturnedGroups/HasMore and actual WindowStart/WindowEnd. No Data rows means no positive matched groups, not proof about uncaptured telemetry."'),
    ]
    return {
        "kind": "AdaptiveDialog", "modelDisplayName": "Model analytics",
        "modelDescription": "Execute reusable aggregate analytics over the approved analytical subset, not the full model schema: totals, rankings, categorical breakdowns, filtered and date-windowed interaction/session/user aggregates, current agent/environment inventory breakdowns and time trends. Use this SAME capability for materially different data questions by setting structured inputs, never raw DAX. Supports one grouping, one exact categorical filter, one inclusive audit date range, topN 1–100. This is a DATA EXECUTION capability, not a DAX-writing capability. For approved DAX advice without execution, select Model DAX advice instead. Unknown metrics/columns and unsafe inputs are rejected in executable validation. For owner/creator identities or questions about field existence, explain approved-tool scope without calling this topic or requesting grouping parameters. Tool exclusions do not establish model absence. Preserve the specialized top-100 tool for the unfiltered top-100-agent request.",
        "inputs": inputs, "inputType": {"properties": properties},
        "outputType": {"properties": {
            "result": {"type": "Any", "description": "Actual connector aggregate rows: one Summary and up to 100 Data rows. Present a readable table; disclose HasMore and audit window."},
            "generatedDax": {"type": "String", "description": "Exact validated DAX sent to the connector. Only describe as executed if actual result rows were returned."},
            "queryContext": {"type": "String", "description": "Applied structured parameters and interpretation caveats."},
        }},
        "beginDialog": {
            "kind": "OnRecognizedIntent", "id": "main",
            "intent": {"displayName": "Model analytics", "includeInOnSelectIntent": True, "triggerQueries": [
                "Analyze interactions by platform", "Show sessions by month",
                "Count agents by risk band", "Analyze usage for a date range",
                "Show distinct user counts by client host",
            ]},
            "actions": actions,
        },
    }


def build_topic():
    topic = _build_base_topic()
    topic["inputs"] = [item for item in topic["inputs"] if item["propertyName"] != "mode"]
    del topic["inputType"]["properties"]["mode"]
    topic["beginDialog"]["actions"].insert(0, set_variable("mode", "execute"))
    return topic


def build_advice_topic():
    topic = _build_base_topic()
    topic["modelDisplayName"] = "Model DAX advice"
    topic["modelDescription"] = (
        "Write, recommend or explain DAX grounded in this Power BI model. Advice only; no data access, "
        "no connector is called by this topic. The channel still uses its normal authentication. Reuses the same validated metric, grouping, "
        "exact filter, audit dates, topN and sorting compiler as model analytics. Choose metric sessions "
        "and groupBy month for sessions by month, interactions/platform for platform usage, etc. "
        "Returns clearly labelled UNEXECUTED DAX plus relationship/filter explanation. "
        "Grounding is an approved subset, not full model metadata. Owner/creator identities are outside this PoC's scope; "
        "do not call this topic or ask grouping parameters for identity or field-existence questions. "
        "Explain that tool exclusions do not establish model absence; never recommend identity DAX. "
        "Use for questions containing DAX, write a query, explain the formula, or help author model queries."
    )
    topic["inputs"] = [item for item in topic["inputs"] if item["propertyName"] != "mode"]
    del topic["inputType"]["properties"]["mode"]
    del topic["outputType"]
    actions = topic["beginDialog"]["actions"]
    end = next(i for i, action in enumerate(actions) if action["id"] == "AdviceOnly")
    topic["beginDialog"]["actions"] = [set_variable("mode", "dax")] + actions[:end + 1]
    topic["beginDialog"]["intent"]["triggerQueries"] = [
        "Help me write DAX for this model", "Write DAX for sessions by month",
        "Recommend a DAX query", "Explain DAX filters and relationships",
        "How do I write a query against this semantic model?",
    ]
    topic["beginDialog"]["intent"]["displayName"] = "Model DAX advice"
    return topic


def build_clarification_topic():
    return {
        "kind": "AdaptiveDialog",
        "beginDialog": {
            "kind": "OnUnknownIntent", "id": "main",
            "actions": [
                {
                    "kind": "ConditionGroup", "id": "ExplainIdentityScope",
                    "conditions": [{
                        "id": "IdentityScopeQuestion",
                        "condition": '=IsMatch(Lower(System.Activity.Text), "\\b(owner|owners|creator|creators|ownerupn|ownername|created by|owned by)\\b", MatchOptions.Contains)',
                        "actions": [
                            {"kind": "SendActivity", "id": "IdentityScopeMessage", "activity": IDENTITY_SCOPE},
                            {"kind": "EndDialog", "id": "EndIdentityScope"},
                        ],
                    }],
                },
                {"kind": "SendActivity", "id": "ExplainModelScope",
                 "activity": "I could not map that request to this PoC's approved tool contract. These tools support audited interaction turns, distinct session counts, distinct-user counts (not identities), current agent inventory and inventory-environment counts. You can group/filter by platform, environment, region, risk, activity or agent; audit metrics also support month/day and client host. Optional paired audit dates span up to 366 days. Revenue, financial cost and product-category metrics are outside this approved subset. " + SCOPE_LIMIT + " Only authoritative full current-version metadata with sufficient visibility can prove absence; this subset, errors and empty results cannot. Actual permission errors are access issues, not model absence. If you want an approved aggregate, specify its metric and grouping. You can also ask 'Write DAX for sessions by month' for approved, unexecuted guidance."},
            ],
        },
    }


if __name__ == "__main__":
    for name, topic in [
        ("ModelAnalytics", build_topic()), ("ModelDaxAdvice", build_advice_topic()),
        ("ModelQuestionClarification", build_clarification_topic()),
    ]:
        path = ROOT / "topics" / f"{name}.mcs.yml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(yaml.safe_dump(topic, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        print("Generated", path.name)

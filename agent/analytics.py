"""Allowlisted aggregate query compiler and its equivalent executable Power Fx topic."""
import datetime as dt
import json
import re
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
    "startDate": "", "endDate": "", "relativePeriod": "none",
    "topN": 20, "sortBy": "value", "mode": "execute",
}
LAST_30_PATTERN = r"\b(last|past|trailing)[ -]+(30|thirty)[ -]+(calendar[ -]+)?days?\b"
DATE_REQUEST_PATTERN = r"\b(last|past|trailing|previous|today|yesterday|this month|this year|latest available)\b|\b(since|between|from)\s+\d|\b\d{4}-\d{2}-\d{2}\b|\b(in|during|for)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b"
OTHER_CALENDAR_PATTERN = r"\b(local|bst|london|pacific|eastern|cet|cest|est|edt|pst|pdt)\b|\blatest\s+available\b"
DATE_CONVENTION = "UTC calendar anchor; model Date.Date as stored; source timezone unverified"
SCOPE_LIMIT = "Unavailable through this PoC's approved tools does not establish whether a field exists in the underlying custom semantic model."
IDENTITY_SCOPE = (
    "Owner and creator identities are outside this PoC's approved analytics scope, so the current tools cannot return that table. "
    "That does not establish whether those fields exist in the underlying custom semantic model. "
    "I can provide approved agent-level aggregates. No identity query is run or recommended."
)


def literal(value):
    return '"' + value.replace('"', '""') + '"'


def resolve_dates(parameters, *, now=None, utterance=""):
    p = dict(parameters)
    text = utterance.lower()
    if p["relativePeriod"] == "none" and re.search(LAST_30_PATTERN, text):
        p["relativePeriod"] = "last30Days"
    if p["relativePeriod"] not in ("none", "last30Days"):
        raise ValueError("Unrecognized or unresolved relative period; supply explicit paired dates or last30Days. No all-history fallback.")
    if p["relativePeriod"] == "last30Days":
        if p["startDate"] or p["endDate"]:
            raise ValueError("Relative and explicit dates conflict; choose one date mode.")
        if re.search(OTHER_CALENDAR_PATTERN, text):
            raise ValueError("Relative dates use today's UTC calendar, not a local timezone or latest-event anchor. Clarify with explicit dates.")
        clock = now if now is not None else dt.datetime.now(dt.timezone.utc)
        if not isinstance(clock, dt.datetime) or clock.tzinfo is None:
            raise ValueError("An aware runtime clock is required; no all-history fallback.")
        end = clock.astimezone(dt.timezone.utc).date()
        p["startDate"] = (end - dt.timedelta(days=29)).isoformat()
        p["endDate"] = end.isoformat()
    elif not p["startDate"] and not p["endDate"] and re.search(DATE_REQUEST_PATTERN, text):
        raise ValueError("A date-scoped request has no resolved dates; clarify the interval, never substitute all history.")
    return p


def validate_request(request, *, now=None, utterance=""):
    if set(request) - set(DEFAULTS):
        raise ValueError("Unknown approved-tool parameter; raw DAX and model identifiers are not accepted. " + SCOPE_LIMIT)
    p = resolve_dates({**DEFAULTS, **request}, now=now, utterance=utterance)
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


def build_query(request, *, now=None, utterance=""):
    p = validate_request(request, now=now, utterance=utterance)
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
        f'"HasMore", __Count > {p["topN"]}, "WindowStart", __Start, "WindowEnd", __End, '
        f'"RequestedStartDate", {literal(p["startDate"])}, "RequestedEndDate", {literal(p["endDate"])}, '
        f'"RelativePeriod", {literal(p["relativePeriod"])}, "DateConvention", {literal(DATE_CONVENTION)}'
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
        "startDate": "Explicit inclusive audit start date YYYY-MM-DD, paired with endDate. Leave BOTH blank for relativePeriod=last30Days; runtime resolves dates. Never invent absolute dates for a relative request.",
        "endDate": "Inclusive audit end date YYYY-MM-DD, or blank. Range must be no more than 366 inclusive days. Do not invent requested dates.",
        "relativePeriod": "none for explicit dates or a truly undated request; last30Days for last/past/trailing 30 calendar days INCLUDING today, resolved from the trusted UTC runtime clock, never the latest event. Leave startDate/endDate blank with last30Days. clarify for unsupported/ambiguous relative periods: validation stops rather than querying all history.",
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
    for name, values in {"metric": list(METRICS), "groupBy": list(GROUPS), "filterBy": list(FILTERS), "sortBy": ["value", "group"], "relativePeriod": ["none", "last30Days", "clarify"]}.items():
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
        set_variable("ClockUtc", "=Now()"),
        set_variable("RequestText", '=Lower(Coalesce(System.Activity.Text, ""))'),
        set_variable("relativePeriod", '=If(Topic.relativePeriod = "none" && IsMatch(Topic.RequestText, ' + literal(LAST_30_PATTERN) + ', MatchOptions.Contains), "last30Days", Topic.relativePeriod)'),
        rejection("ValidateRelativePeriod",
                  '=!(Topic.relativePeriod in ["none", "last30Days"]) || (Topic.relativePeriod = "last30Days" && (!IsBlank(Topic.startDate) || !IsBlank(Topic.endDate)))',
                  "Choose explicit paired dates OR last30Days, not both. Last 30 days uses 30 inclusive UTC calendar dates ending today, not the latest recorded event. Other relative periods need clarification/explicit dates. No query or all-history substitute is run."),
        rejection("ValidateRelativeCalendar",
                  '=Topic.relativePeriod = "last30Days" && IsMatch(Topic.RequestText, ' + literal(OTHER_CALENDAR_PATTERN) + ', MatchOptions.Contains)',
                  "The relative resolver uses today's UTC calendar, not local time or the latest available event. Please confirm explicit start/end dates for a different calendar or anchor. No query has run."),
        rejection("RequireRequestedDates",
                  '=Topic.relativePeriod = "none" && IsBlank(Topic.startDate) && IsBlank(Topic.endDate) && IsMatch(Topic.RequestText, ' + literal(DATE_REQUEST_PATTERN) + ', MatchOptions.Contains)',
                  "Your question requests a date window, but no supported interval was resolved. I can run dated rankings now: specify paired YYYY-MM-DD dates, or last 30 days using the UTC calendar. I will not substitute all-history results."),
        set_variable("AnchorUtcDate", "=Date(Year(Topic.ClockUtc), Month(Topic.ClockUtc), Day(Topic.ClockUtc))"),
        set_variable("startDate", '=If(Topic.relativePeriod = "last30Days", Text(DateAdd(Topic.AnchorUtcDate, -29, TimeUnit.Days), "yyyy-mm-dd", "en-US"), Topic.startDate)'),
        set_variable("endDate", '=If(Topic.relativePeriod = "last30Days", Text(Topic.AnchorUtcDate, "yyyy-mm-dd", "en-US"), Topic.endDate)'),
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
                     '="""Metric"", """ & Topic.metric & """, ""GroupBy"", """ & Topic.groupBy & """, ""TotalGroups"", __Count, ""ReturnedGroups"", MIN(__Count, " & Topic.LimitText & "), ""HasMore"", __Count > " & Topic.LimitText & ", ""WindowStart"", __Start, ""WindowEnd"", __End, ""RequestedStartDate"", """ & Topic.startDate & """, ""RequestedEndDate"", """ & Topic.endDate & """, ""RelativePeriod"", """ & Topic.relativePeriod & """, ""DateConvention"", ""' + DATE_CONVENTION + '"""'),
        set_variable("Dax",
                     '="DEFINE VAR __Summary = FILTER(CALCULATETABLE(" & Topic.BaseDax & Topic.FilterDax & "), NOT ISBLANK([Value]) && [Value] > 0" & If(Topic.groupBy = "agent", " && [GroupKey] <> ""(blank)""", "") & ") VAR __Count = COALESCE(COUNTROWS(__Summary), 0) VAR __Start = " & Topic.StartDax & " VAR __End = " & Topic.EndDax & " VAR __Rows = TOPN(" & Topic.LimitText & ", __Summary, " & Topic.SortDax & ") EVALUATE UNION(ROW(""RowType"", ""Summary"", ""Group"", """", ""GroupKey"", """", ""Value"", BLANK(), " & Topic.MetadataDax & "), SELECTCOLUMNS(__Rows, ""RowType"", ""Data"", ""Group"", [Group], ""GroupKey"", [GroupKey], ""Value"", [Value], " & Topic.MetadataDax & ")) ORDER BY [RowType] DESC, " & Topic.OrderDax'),
        {
            "kind": "ConditionGroup", "id": "AdviceOnly",
            "conditions": [{
                "id": "ReturnUnexecutedDax", "condition": '=Topic.mode = "dax"',
                "actions": [
                    {"kind": "SendActivity", "id": "ExplainDax", "activity": "Model-grounded DAX suggestion — NOT EXECUTED. Requested dates: {Topic.startDate} through {Topic.endDate}, inclusive (blank means no date restriction). Relative mode: {Topic.relativePeriod}. UTC calendar anchor; model dates are compared as stored, source timezone unverified. WindowStart/WindowEnd would be matching recorded-event bounds, not refresh timestamps or proof of continuous coverage. Date filters use the active Date-to-Interaction relationship.\n```dax\n{Topic.Dax}\n```"},
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
        set_variable("queryContext", '="Metric=" & Topic.metric & "; grouping=" & Topic.groupBy & "; exact filter=" & Topic.filterBy & ":" & Topic.filterValue & "; requested inclusive dates=" & Topic.startDate & ".." & Topic.endDate & "; relativePeriod=" & Topic.relativePeriod & ". UTC calendar anchor; source timezone unverified; model dates compared as stored. Show RequestedStartDate/RequestedEndDate separately from observed WindowStart/WindowEnd, not refresh timestamps or continuous coverage. Disclose TotalGroups/ReturnedGroups/HasMore. No Data rows means no matching recorded events for audit metrics, not no activity: never widen the interval. Inventory has no audit window."'),
    ]
    return {
        "kind": "AdaptiveDialog", "modelDisplayName": "Model analytics",
        "modelDescription": "Run approved analytics NOW, including TOP AGENTS FOR THE LAST 30 DAYS, explicit-date rankings, categorical filters, alternative metrics and limits 1–100. For usage ranking: metric=interactions, groupBy=agent, sortBy=value, topN=20 unless specified (100 for dated top100). For last 30 days set relativePeriod=last30Days, startDate/endDate blank: executable UTC-clock resolver supplies the inclusive dates. Never substitute all history or claim this capability is future work. The fixed top100 tool is ONLY for the exact undated/unfiltered all-history top100 experience. This reusable DATA EXECUTION capability compiles validated inputs over an approved subset, not full model schema. It supports one grouping, one exact categorical filter, explicit audit dates or the controlled relative period. For advice only use Model DAX advice. For owner/creator identities or field-existence questions explain scope without querying or asking grouping parameters. Tool exclusions do not establish model absence.",
        "inputs": inputs, "inputType": {"properties": properties},
        "outputType": {"properties": {
            "result": {"type": "Any", "description": "One Summary and up to 100 Data rows. Agent rankings: numbered table in returned order, all requested available rows up to topN. Disclose requested dates separately from observed-event bounds, HasMore and DateConvention. Empty audit window means no matching recorded events, never no activity or permission to widen dates."},
            "generatedDax": {"type": "String", "description": "Exact validated DAX sent to the connector. Only describe as executed if actual result rows were returned."},
            "queryContext": {"type": "String", "description": "Applied structured parameters and interpretation caveats."},
        }},
        "beginDialog": {
            "kind": "OnRecognizedIntent", "id": "main",
            "intent": {"displayName": "Model analytics", "includeInOnSelectIntent": True, "triggerQueries": [
                "Analyze interactions by platform", "Show sessions by month",
                "Count agents by risk band", "Analyze usage for a date range",
                "Show distinct user counts by client host",
                "Give me the top agents and their usage over the last 30 days",
                "Show top 100 agents between 2026-08-14 and 2026-09-12",
                "Show the top 10 agents by sessions filtered to a platform",
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
        "Supports explicit dates or relativePeriod=last30Days with blank date inputs; the same executable UTC runtime resolver "
        "supplies 30 inclusive calendar dates ending today, never the latest event. Unsupported periods/calendar anchors stop for clarification. "
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
        "Write DAX for top agents over the last 30 days without executing it",
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
                 "activity": "I could not map that request to this PoC's approved tool contract. These tools support audited interaction turns, distinct session counts, distinct-user counts (not identities), current agent inventory and inventory-environment counts. You can group/filter by platform, environment, region, risk, activity or agent; audit metrics also support month/day and client host. Dated agent rankings are available now: paired inclusive dates (maximum 366 days), or last 30 days ending today using the UTC calendar. No all-history substitute is used for an unresolved date window. Revenue, financial cost and product-category metrics are outside this approved subset. " + SCOPE_LIMIT + " Only authoritative full current-version metadata with sufficient visibility can prove absence; this subset, errors and empty results cannot. Actual permission errors are access issues, not model absence. If you want an approved aggregate, specify its metric and grouping. You can also ask 'Write DAX for sessions by month' for approved, unexecuted guidance."},
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

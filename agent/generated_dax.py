"""Generic DAX table-expression contract, not a business-metric/query-template compiler.

The lexer protects the envelope boundary; Power BI remains the DAX parser and authorizer.
"""
import re

MAX_EXPRESSION = 12000
MAX_CODE = 4000
MAX_COLUMNS = 16
MAX_ROWS = 100
CELL_CHARS = 256
MAX_RESULT_JSON = 64000
TOKEN_PATTERN = r'(?P<Literal>"(?:[^"]|"")*"|\'(?:[^\']|\'\')*\'|\[(?:[^\]]|\]\])*\]|//[^\r\n]*|--[^\r\n]*|/\*[\s\S]*?\*/)|(?P<Code>[\s\S])'
FX_TOKEN_PATTERN = TOKEN_PATTERN.replace("?P<", "?<").replace("\\'", "'")
FORBIDDEN = r"\b(EVALUATE|DEFINE|ORDER|INFO|EXTERNALMEASURE)\b|\bVAR\s+(UTC_TODAY|QUERY_START|QUERY_END)\b|\b__poc\w*"
ALIAS_PATTERN = r"[A-Za-z][A-Za-z0-9_ ]{0,59}"
QUERY_TEMPLATE = (
    'DEFINE VAR __pocNow = UTCNOW() '
    'VAR UTC_TODAY = DATE(YEAR(__pocNow), MONTH(__pocNow), DAY(__pocNow)) '
    'VAR QUERY_START = (\n{start}\n) VAR QUERY_END = (\n{end}\n) '
    'VAR __pocSource = DISTINCT(SELECTCOLUMNS((\n{expression}\n), {projection})) '
    'VAR __pocSample = TOPN({next_limit}, __pocSource, {sort}) '
    'VAR __pocCount = COALESCE(COUNTROWS(__pocSample), 0) '
    'VAR __pocPage = TOPN({limit}, __pocSample, {sort}) '
    'VAR __pocOk = __pocCount <= {next_limit} && COUNTROWS(__pocPage) <= {limit} && ({date_valid}) '
    'VAR __pocTextCut = SUMX(__pocPage, {truncated}) > 0 '
    'EVALUATE UNION(ROW("__kind", "Summary", "__status", IF(__pocOk, "ok", "bounds_error"), '
    '"__returned", IF(__pocOk, COALESCE(COUNTROWS(__pocPage), 0), 0), "__textTruncated", __pocTextCut, '
    '"__hasMore", __pocCount > {limit}, "__anchorUtc", FORMAT(UTC_TODAY, "yyyy-MM-dd"), '
    '"__requestedStart", IF(ISBLANK(QUERY_START), "", FORMAT(QUERY_START, "yyyy-MM-dd")), '
    '"__requestedEnd", IF(ISBLANK(QUERY_END), "", FORMAT(QUERY_END, "yyyy-MM-dd")), {blanks}), '
    'SELECTCOLUMNS(FILTER(__pocPage, __pocOk), "__kind", "Data", "__status", "ok", '
    '"__returned", BLANK(), "__textTruncated", ({truncated}) > 0, "__hasMore", __pocCount > {limit}, '
    '"__anchorUtc", FORMAT(UTC_TODAY, "yyyy-MM-dd"), '
    '"__requestedStart", IF(ISBLANK(QUERY_START), "", FORMAT(QUERY_START, "yyyy-MM-dd")), '
    '"__requestedEnd", IF(ISBLANK(QUERY_END), "", FORMAT(QUERY_END, "yyyy-MM-dd")), {cells})) '
    'ORDER BY [__kind] DESC, {order}'
)


def dax_string(value):
    return '"' + value.replace('"', '""') + '"'


def code_only(expression):
    return "".join(m.group("Code") or "" for m in re.finditer(TOKEN_PATTERN, expression))


def validate_expression(expression, max_length=MAX_EXPRESSION):
    if not isinstance(expression, str) or not expression.strip() or len(expression) > max_length:
        raise ValueError("DAX expression is empty or exceeds its length bound.")
    code = code_only(expression)
    if len(code) > MAX_CODE or re.search(FORBIDDEN, code, re.I):
        raise ValueError("Use one table/scalar expression, not a full query, metadata command or external-model reference.")
    if any(c in code for c in "\"'[];") or "/*" in code or "*/" in code:
        raise ValueError("Unclosed literal/identifier/comment or statement delimiter.")
    parens = braces = 0
    for char in code:
        parens += (char == "(") - (char == ")")
        braces += (char == "{") - (char == "}")
        if not 0 <= parens <= 32 or not 0 <= braces <= 16:
            raise ValueError("Unbalanced or overly nested expression.")
    if parens or braces:
        raise ValueError("Unbalanced expression.")
    return code


def validate_request(request):
    allowed = {"modelAlias", "tableExpression", "columns", "sortBy", "limit", "startDateExpression", "endDateExpression"}
    if set(request) - allowed:
        raise ValueError("Unknown parameter; model IDs, connections and arbitrary full queries are not accepted.")
    p = {"modelAlias": "primary", "sortBy": "", "limit": 20, "startDateExpression": "", "endDateExpression": "", **request}
    if p["modelAlias"] != "primary":
        raise ValueError("Model alias is not onboarded.")
    validate_expression(p.get("tableExpression", ""))
    if not isinstance(p.get("columns"), str) or len(p["columns"]) > 1000 or not isinstance(p["sortBy"], str) or len(p["sortBy"]) > 1000:
        raise ValueError("Output aliases and ordering must be bounded text.")
    columns = [v.strip() for v in p["columns"].split(",")]
    if not 1 <= len(columns) <= MAX_COLUMNS or len({c.lower() for c in columns}) != len(columns):
        raise ValueError("Supply 1–16 distinct output aliases.")
    if any(not re.fullmatch(ALIAS_PATTERN, c) for c in columns):
        raise ValueError("Use simple ASCII output aliases, up to 60 characters.")
    if isinstance(p["limit"], bool) or not isinstance(p["limit"], (int, float)) or int(p["limit"]) != p["limit"] or not 1 <= p["limit"] <= MAX_ROWS:
        raise ValueError("limit must be an integer from 1 to 100.")
    p["limit"] = int(p["limit"])
    if bool(p["startDateExpression"]) != bool(p["endDateExpression"]):
        raise ValueError("Both date expressions or neither are required.")
    if p["startDateExpression"]:
        validate_expression(p["startDateExpression"], 256)
        validate_expression(p["endDateExpression"], 256)
        if not all(re.search(r"\b" + key + r"\b", code_only(p["tableExpression"]), re.I) for key in ("QUERY_START", "QUERY_END")):
            raise ValueError("Dated expressions must use both QUERY_START and QUERY_END; no silent all-history substitution.")
    order = []
    for part in p["sortBy"].split(",") if p["sortBy"].strip() else []:
        match = re.fullmatch(r"\s*(.+?)\s+(asc|desc)\s*", part, re.I)
        lookup = {c.lower(): c for c in columns}
        if not match or match[1].lower() not in lookup or match[1].lower() in [c.lower() for c, _ in order]:
            raise ValueError("Sort only declared output aliases once each, followed by asc/desc.")
        order.append((lookup[match[1].lower()], match[2].upper()))
    order += [(c, "ASC") for c in columns if c not in [name for name, _ in order]]
    return p, columns, order


def build_query(request):
    p, columns, order = validate_request(request)
    projection = ", ".join(f'{dax_string(c)}, [{c}]' for c in columns)
    sorting = ", ".join(f"[{c}], {direction}" for c, direction in order)
    ordering = ", ".join(f"[{c}] {direction}" for c, direction in order)
    blanks = ", ".join(f"{dax_string(c)}, BLANK()" for c in columns)
    cells = ", ".join(f'{dax_string(c)}, IF(ISTEXT([{c}]), LEFT([{c}], {CELL_CHARS}), [{c}])' for c in columns)
    truncated = " + ".join(f"IF(ISTEXT([{c}]) && LEN([{c}]) > {CELL_CHARS}, 1, 0)" for c in columns)
    start, end = p["startDateExpression"] or "BLANK()", p["endDateExpression"] or "BLANK()"
    dated = bool(p["startDateExpression"])
    date_valid = "QUERY_START <= QUERY_END" if dated else "TRUE()"
    return QUERY_TEMPLATE.format(
        expression=p["tableExpression"], start=start, end=end, projection=projection,
        next_limit=p["limit"] + 1, limit=p["limit"], sort=sorting, order=ordering,
        date_valid=date_valid, truncated=truncated, blanks=blanks, cells=cells,
    )


def validate_result(rows):
    """Provider errors must be checked by the transport before this envelope check."""
    import json
    if len(json.dumps(rows, ensure_ascii=True)) > MAX_RESULT_JSON:
        raise ValueError("Result exceeds the preview byte/character budget; reduce rows/columns.")
    summaries = [r for r in rows if r.get("[__kind]") == "Summary"]
    data = [r for r in rows if r.get("[__kind]") == "Data"]
    if len(summaries) != 1 or len(rows) != len(data) + 1 or len(data) > MAX_ROWS:
        raise ValueError("Missing or invalid execution envelope; no successful result claimed.")
    summary = summaries[0]
    if summary.get("[__status]") != "ok" or summary.get("[__returned]") != len(data):
        raise ValueError("Bounds, dates or row-count validation failed.")
    return summary, data

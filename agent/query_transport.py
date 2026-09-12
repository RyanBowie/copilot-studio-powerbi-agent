"""Dynamic Power BI row transport; no declared Value column or lossy DAX serialization."""
import json

OWNED_COLUMNS = ("__kind", "__status", "__returned", "__textTruncated", "__hasMore",
                 "__anchorUtc", "__requestedStart", "__requestedEnd")
OUTPUT_SCHEMA = {"kind": "Record", "properties": {"firstTableRows": {"type": "Any"}}}
ROW_COUNT_EXPRESSION = "=If(IsBlank(Topic.RawRows), -1, IfError(CountRows(Table(Topic.RawRows)), -1))"
RESULT_EXPRESSION = "=JSON(Topic.RawRows)"
ENVELOPE_EXPRESSION = "=Table(Topic.RawRows)"
REQUIRE_ENVELOPE_EXPRESSION = (
    '=IfError(CountIf(Topic.Envelope, Text(Value.\'[__kind]\') = "Summary") <> 1 || '
    'CountIf(Topic.Envelope, !(Text(Value.\'[__kind]\') in ["Summary","Data"])) > 0, true)'
)
VALIDATE_ENVELOPE_EXPRESSION = (
    '=IfError(IsBlank(Topic.Summary.\'[__returned]\') || '
    '!IsNumeric(JSON(Topic.Summary.\'[__returned]\')) || '
    'Text(Topic.Summary.\'[__status]\') <> "ok" || '
    'Value(Topic.Summary.\'[__returned]\') <> CountIf(Topic.Envelope, Text(Value.\'[__kind]\') = "Data") || '
    'Value(Topic.Summary.\'[__returned]\') < 0 || Value(Topic.Summary.\'[__returned]\') > Topic.limit || '
    'CountIf(Topic.Envelope, Text(Value.\'[__status]\') <> "ok" || '
    'IsBlank(Value.\'[__hasMore]\') || IsBlank(Value.\'[__textTruncated]\') || '
    '!(JSON(Value.\'[__hasMore]\') in ["true","false"]) || '
    '!(JSON(Value.\'[__textTruncated]\') in ["true","false"])) > 0, true)'
)


def decode_rows(rows, maximum=100, expected_columns=None):
    """Validate direct REST rows without changing their names, ordering or scalar values."""
    if not isinstance(rows, list) or not 1 <= len(rows) <= maximum + 1:
        raise ValueError("Missing/oversized dynamic rowset.")
    encoded = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-16-le", errors="surrogatepass")) // 2 > 64000:
        raise ValueError("Result exceeds the preview character budget.")
    allowed = {"[" + c + "]" for c in (*OWNED_COLUMNS, *expected_columns)} if expected_columns else None
    for row in rows:
        if not isinstance(row, dict) or (allowed is not None and set(row) - allowed):
            raise ValueError("Unexpected row or column shape.")
        if any(isinstance(value, (dict, list)) for value in row.values()):
            raise ValueError("DAX scalar cells cannot be nested objects or arrays.")
        if any(type(row.get("[" + name + "]")) is not bool for name in ("__hasMore", "__textTruncated")):
            raise ValueError("Missing/invalid typed envelope flags.")
    return rows

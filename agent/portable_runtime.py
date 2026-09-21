"""Portable native topics and bounded, publication-time environment configuration.

No credentials, network, private-file discovery or writes. The GPT helper reads
only the existing public agent.mcs.yml beside this module at package-build time.
Env.<schemaName> is the native Copilot Studio environment-variable namespace.
See PORTABLE.md for authoritative sources, package integration and trust boundary.
"""
import copy
import datetime as dt
import json
import re
from uuid import UUID

from general_runtime import (
    CATALOG_POLICY, build_metadata_topic, build_query_topic, build_error_topic,
    fx_text, set_value, snapshot_hash, stop_metadata,
)

CONTRACT = "powerbi-native-config-v1"
UNCONFIGURED = "NOT_CONFIGURED"
CHUNK_COUNT = 128
CHUNK_PAYLOAD = 1900
CHUNK_HEADER = 45  # canonical revision UUID | three-digit index | three-digit count |
VALUE_LIMIT = 2000
MAX_DOCUMENT = CHUNK_COUNT * CHUNK_PAYLOAD
GUID_PATTERN = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
MANIFEST_KEYS = (
    "contract", "revision", "environmentId", "workspaceId", "datasetId",
    "snapshotHash", "chunkCount", "payloadLength",
)
DOCUMENT_KEYS = (*MANIFEST_KEYS[:6], "snapshot")
TABLE_KEYS = ("name", "description", "hidden", "columns", "measures")
COLUMN_KEYS = ("name", "type", "description", "hidden")
MEASURE_KEYS = ("name", "description", "formatString", "expressionAvailable")
RELATIONSHIP_KEYS = (
    "name", "fromTable", "fromColumn", "toTable", "toColumn",
    "fromCardinality", "toCardinality", "crossFilteringBehavior", "isActive",
)
SNAPSHOT_KEYS = (
    "modelAlias", "source", "retrievedAtUtc", "sourcePermission", "tables",
    "relationships", "guidance", "sourceBinding",
)
GUIDANCE_KEYS = (
    "authoredInstructions", "verifiedAnswers", "linguisticMetadataPresent", "measureExpressions",
)
BOTCOMPONENT_TYPES = {"topic": 9, "globalVariable": 12, "gpt": 15}


def build_portable_instructions():
    """Return complete native GptComponentMetadata from the real public agent.

    Build-time only: reads the existing adjacent agent.mcs.yml, never a template,
    private configuration, or cloud resource. Leaves that file unchanged. The
    original analyst instructions are retained verbatim after a conditional
    configuration-state preface. No model/provider selection is shipped.

    Serialize this dictionary as the native type-15 GPT component's data. It is
    deliberately separate from build_portable_bundle/source_files so their
    existing pure API, native component inventory, and fingerprints stay stable.
    """
    from pathlib import Path
    import yaml

    source = yaml.safe_load(Path(__file__).with_name("agent.mcs.yml").read_text(encoding="utf-8"))
    if (not isinstance(source, dict) or source.get("kind") != "GptComponentMetadata" or
            not isinstance(source.get("instructions"), str) or not source["instructions"].strip() or
            not isinstance(source.get("aISettings", {}), dict)):
        raise ValueError("Portable GPT requires the real existing GptComponentMetadata and analyst instructions.")
    if "unconfigured starter" in source["instructions"].lower():
        raise ValueError("Portable GPT cannot inherit the historical unconfigured starter's permanent stop instructions.")

    result = copy.deepcopy(source)
    result.get("aISettings", {}).pop("model", None)
    result["conversationStarters"] = [
        {"title": "Explore model structure",
         "text": "What tables, measures and relationships are available in the configured model?"},
        {"title": "Plan an analysis",
         "text": "Review the model and help me choose a measure and grouping for an analysis."},
        {"title": "Compare groups",
         "text": "Help me compare values across groups using fields supported by this model."},
        {"title": "Explore time periods",
         "text": "If the model supports dated analysis, help me compare a measure across two time periods."},
        {"title": "Recommend DAX",
         "text": "Recommend DAX for an analysis supported by this model without executing the business query."},
    ]
    result["instructions"] = (
        "Configuration state is determined by the native tools, not by the package's initial defaults.\n"
        "If Get model metadata or another native tool explicitly reports NOT_CONFIGURED, report that exact\n"
        "status, explain that the owner must complete configuration and publish in Copilot Studio, and stop\n"
        "that request. Do not invent schema, substitute synthetic data, or request private configuration in chat.\n"
        "Report other errors with their actual provenance; do not relabel them NOT_CONFIGURED.\n"
        "When configuration is valid and metadata visibility is verified, perform the requested analysis\n"
        "normally under the instructions below. Configuration requires no runtime topic replacement.\n\n"
        + source["instructions"]
    )
    return result


def compact(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def canonical_guid(value):
    if not isinstance(value, str) or not re.fullmatch(GUID_PATTERN, value):
        raise ValueError("Expected an explicit lowercase canonical GUID.")
    if UUID(value).int == 0:
        raise ValueError("Zero GUID is not a configured target.")
    return value


def validate_names(schema_name, environment_prefix, connection_reference):
    for value in (schema_name, environment_prefix, connection_reference):
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,90}", value):
            raise ValueError("Explicit schema/prefix/connection names must be simple platform identifiers.")


def environment_names(prefix):
    validate_names(prefix, prefix, prefix)
    return [prefix + "_Manifest"] + [prefix + f"_Chunk{i:03}" for i in range(1, CHUNK_COUNT + 1)]


def _keys(value, allowed, required):
    if not isinstance(value, dict) or set(value) - set(allowed) or not set(required) <= set(value):
        raise ValueError("Unexpected or missing configuration properties; raw definitions are not accepted.")


def _text(value, maximum=4096, required=False):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ValueError("Invalid bounded text in reviewed metadata.")


def reviewed_snapshot(snapshot):
    """Allowlist names/metadata; reject example snapshots and raw source/role expressions."""
    _keys(snapshot, SNAPSHOT_KEYS, ("retrievedAtUtc", "tables", "relationships"))
    _text(snapshot["retrievedAtUtc"], 64, True)
    timestamp = dt.datetime.fromisoformat(snapshot["retrievedAtUtc"].replace("Z", "+00:00"))
    if timestamp.utcoffset() != dt.timedelta(0):
        raise ValueError("Snapshot preparation timestamp must be UTC.")
    if snapshot.get("modelAlias", "primary") != "primary":
        raise ValueError("Only the primary model alias is supported.")
    for key in ("source", "sourcePermission"):
        if key in snapshot:
            _text(snapshot[key])
    tables = snapshot["tables"]
    if not isinstance(tables, list) or not 1 <= len(tables) <= 256:
        raise ValueError("Configuration requires 1–256 governed tables.")
    names = set()
    result = copy.deepcopy(snapshot)
    if "sourceBinding" in result:
        binding = result["sourceBinding"]
        _keys(binding, ("tenantId", "workspaceId", "datasetId"), ("tenantId", "workspaceId", "datasetId"))
        for value in binding.values():
            canonical_guid(value)
    for table in result["tables"]:
        _keys(table, TABLE_KEYS, ("name", "columns", "measures"))
        _text(table["name"], 256, True)
        if "," in table["name"] or table["name"].lower() in names:
            raise ValueError("Table names must be distinct and cannot contain the table-selector delimiter comma.")
        names.add(table["name"].lower())
        table.setdefault("description", "")
        table.setdefault("hidden", False)
        _text(table["description"])
        if type(table["hidden"]) is not bool:
            raise ValueError("hidden must be Boolean.")
        for collection, allowed, required in (
            ("columns", COLUMN_KEYS, ("name", "type")),
            ("measures", MEASURE_KEYS, ("name",)),
        ):
            rows = table[collection]
            if not isinstance(rows, list) or len(rows) > 2048:
                raise ValueError("Invalid column/measure list.")
            seen = set()
            for item in rows:
                _keys(item, allowed, required)
                _text(item["name"], 256, True)
                if item["name"].lower() in seen:
                    raise ValueError("Duplicate column/measure name.")
                seen.add(item["name"].lower())
                item.setdefault("description", "")
                _text(item["description"])
                if collection == "columns":
                    _text(item["type"], 64, True)
                    item.setdefault("hidden", False)
                    if type(item["hidden"]) is not bool:
                        raise ValueError("Column hidden must be Boolean.")
                else:
                    item.setdefault("formatString", "")
                    _text(item["formatString"])
                    if item.get("expressionAvailable", False) is not False:
                        raise ValueError("Measure expressions are not part of the name-discovery contract.")
                    item["expressionAvailable"] = False
    if not isinstance(result["relationships"], list) or len(result["relationships"]) > 2048:
        raise ValueError("Invalid relationships.")
    for rel in result["relationships"]:
        _keys(rel, RELATIONSHIP_KEYS, ("fromTable", "fromColumn", "toTable", "toColumn"))
        for key, value in rel.items():
            if key == "isActive":
                if type(value) is not bool:
                    raise ValueError("Relationship isActive must be Boolean.")
            else:
                _text(value, 256, True)
        for end in ("from", "to"):
            table = next((t for t in result["tables"] if t["name"] == rel[end + "Table"]), None)
            if not table or rel[end + "Column"] not in [c["name"] for c in table["columns"]]:
                raise ValueError("Relationship references are outside the governed snapshot.")
    result.setdefault("guidance", {})
    _keys(result["guidance"], GUIDANCE_KEYS, ())
    for key, value in result["guidance"].items():
        if key == "linguisticMetadataPresent":
            if type(value) is not bool:
                raise ValueError("linguisticMetadataPresent must be Boolean.")
        else:
            _text(value)
    return result


def make_configuration(snapshot, *, environment_id, workspace_id, dataset_id, revision, prefix):
    """Return PRIVATE text values; callers must persist outside source control."""
    snapshot = reviewed_snapshot(snapshot)
    if snapshot.get("sourceBinding", {}).get("workspaceId") != workspace_id or snapshot.get("sourceBinding", {}).get("datasetId") != dataset_id:
        raise ValueError("CONFIG_SOURCE_MISMATCH: prepare a source-bound snapshot for the explicit model target.")
    binding = dict(contract=CONTRACT, revision=canonical_guid(revision),
                   environmentId=canonical_guid(environment_id), workspaceId=canonical_guid(workspace_id),
                   datasetId=canonical_guid(dataset_id), snapshotHash=snapshot_hash(snapshot))
    document = compact({**binding, "snapshot": snapshot})
    count = (len(document) + CHUNK_PAYLOAD - 1) // CHUNK_PAYLOAD
    if count > CHUNK_COUNT:
        raise ValueError(f"CONFIG_TOO_LARGE: reviewed metadata exceeds {MAX_DOCUMENT} ASCII JSON characters.")
    manifest = {**binding, "chunkCount": count, "payloadLength": len(document)}
    names = environment_names(prefix)
    values = {names[0]: compact(manifest)}
    for index, name in enumerate(names[1:], 1):
        values[name] = (f"{revision}|{index:03}|{count:03}|" +
                        document[(index - 1) * CHUNK_PAYLOAD:index * CHUNK_PAYLOAD]) if index <= count else UNCONFIGURED
    assert all(len(value) <= VALUE_LIMIT for value in values.values())
    return values


def decode_configuration(values, prefix, environment_id):
    """Owner/helper verification, also used for offline malformed-config regressions."""
    names = environment_names(prefix)
    if set(values) != set(names) or any(not isinstance(v, str) or len(v) > VALUE_LIMIT for v in values.values()):
        raise ValueError("CONFIG_INCOMPLETE: all bounded slots are required.")
    if values[names[0]] in ("", UNCONFIGURED):
        raise ValueError("NOT_CONFIGURED")
    manifest = json.loads(values[names[0]])
    _keys(manifest, MANIFEST_KEYS, MANIFEST_KEYS)
    if manifest["contract"] != CONTRACT or manifest["environmentId"] != canonical_guid(environment_id):
        raise ValueError("CONFIG_TARGET_MISMATCH")
    for key in ("revision", "environmentId", "workspaceId", "datasetId"):
        canonical_guid(manifest[key])
    count = manifest["chunkCount"]
    if type(count) is not int or not 1 <= count <= CHUNK_COUNT:
        raise ValueError("CONFIG_CHUNK_COUNT")
    parts = []
    for index, name in enumerate(names[1:], 1):
        value = values[name]
        if index > count:
            if value != UNCONFIGURED:
                raise ValueError("CONFIG_TRAILING_CHUNK")
            continue
        header = f"{manifest['revision']}|{index:03}|{count:03}|"
        if not value.startswith(header) or not 0 < len(value) - CHUNK_HEADER <= CHUNK_PAYLOAD:
            raise ValueError("CONFIG_CHUNK_REVISION")
        if index < count and len(value) - CHUNK_HEADER != CHUNK_PAYLOAD:
            raise ValueError("CONFIG_CHUNK_LENGTH")
        parts.append(value[CHUNK_HEADER:])
    document = "".join(parts)
    if type(manifest["payloadLength"]) is not int or len(document) != manifest["payloadLength"]:
        raise ValueError("CONFIG_LENGTH")
    parsed = json.loads(document)
    _keys(parsed, DOCUMENT_KEYS, DOCUMENT_KEYS)
    if any(parsed[k] != manifest[k] for k in DOCUMENT_KEYS if k != "snapshot"):
        raise ValueError("CONFIG_BINDING")
    snapshot = reviewed_snapshot(parsed["snapshot"])
    if snapshot != parsed["snapshot"] or snapshot_hash(snapshot) != parsed["snapshotHash"]:
        raise ValueError("CONFIG_SNAPSHOT_HASH")
    if snapshot.get("sourceBinding", {}).get("workspaceId") != parsed["workspaceId"] or snapshot.get("sourceBinding", {}).get("datasetId") != parsed["datasetId"]:
        raise ValueError("CONFIG_SOURCE_MISMATCH")
    return parsed


def _closed(identifier, condition, code):
    action = stop_metadata(identifier, condition,
        code + ": the native Power BI tool is not configured with a complete reviewed configuration. "
        "No connector was attempted and no metadata was disclosed. Ask the agent owner to configure and publish; "
        "do not retry or diagnose this as a Power BI permission failure.")
    # Clear every prior schema authorization before terminating a bad configuration.
    actions = action["conditions"][0]["actions"]
    actions[0:0] = [set_value("Global." + name, "", identifier + name)
                    for name in ("SchemaSnapshot", "SchemaTurn", "SchemaUser", "SchemaConfiguration")]
    return action


def allowed_keys(expression, keys):
    return f'CountIf(ColumnNames({expression}), !(Value in [{",".join(fx_text(k) for k in keys)}])) = 0'


def string_check(expression, maximum=4096, required=False):
    return (f'And(StartsWith(JSON({expression}), Char(34)), Len(Text({expression})) <= {maximum}' +
            (f', !IsBlank(TrimEnds(Text({expression})))' if required else "") + ")")


def snapshot_valid_expression():
    """Validate dynamic JSON before constructing any DAX or disclosing any metadata."""
    col = "c.Value"
    measure = "m.Value"
    table = "t.Value"
    snapshot = "Topic.Config.snapshot"
    columns = f"Table({table}.columns)"
    measures = f"Table({table}.measures)"
    optional_rel = [
        f'If({fx_text(k)} in ColumnNames(r.Value), {string_check("r.Value." + k, 256, True)}, true)'
        for k in ("name", "fromCardinality", "toCardinality", "crossFilteringBehavior")
    ]
    optional_rel.append('If("isActive" in ColumnNames(r.Value), JSON(r.Value.isActive) in ["true","false"], true)')
    checks = [
        allowed_keys(snapshot, SNAPSHOT_KEYS),
        f'If("modelAlias" in ColumnNames({snapshot}), Text({snapshot}.modelAlias) = "primary", true)',
        string_check(snapshot + ".retrievedAtUtc", 64, True),
        f'!IsBlank(DateTimeValue(Text({snapshot}.retrievedAtUtc)))',
        f'IsMatch(Text({snapshot}.retrievedAtUtc), ".*(Z|\\+00:00)$")',
        f'Text({snapshot}.sourceBinding.workspaceId) = Text(Topic.Config.workspaceId)',
        f'Text({snapshot}.sourceBinding.datasetId) = Text(Topic.Config.datasetId)',
        allowed_keys(snapshot + ".sourceBinding", ("tenantId", "workspaceId", "datasetId")),
        f'IsMatch(Text({snapshot}.sourceBinding.tenantId), {fx_text(GUID_PATTERN)})',
        f'Text({snapshot}.sourceBinding.tenantId) = Lower(Text(System.Bot.TenantId))',
        f'StartsWith(JSON({snapshot}.tables), "[")',
        f'CountRows(Table({snapshot}.tables)) >= 1 && CountRows(Table({snapshot}.tables)) <= 256',
        f'CountRows(Distinct(ForAll(Table({snapshot}.tables), Lower(Text(Value.name))), Value)) = CountRows(Table({snapshot}.tables))',
        f'StartsWith(JSON({snapshot}.relationships), "[") && CountRows(Table({snapshot}.relationships)) <= 2048',
        f'CountIf(Table({snapshot}.relationships) As r, !And({allowed_keys("r.Value", RELATIONSHIP_KEYS)}, '
        + ", ".join(string_check("r.Value." + key, 256, True) for key in ("fromTable", "fromColumn", "toTable", "toColumn"))
        + f', CountIf(Table({snapshot}.tables) As t, Text(t.Value.name) = Text(r.Value.fromTable) && '
        'CountIf(Table(t.Value.columns), Text(Value.name) = Text(r.Value.fromColumn)) = 1) = 1'
        + f', CountIf(Table({snapshot}.tables) As t, Text(t.Value.name) = Text(r.Value.toTable) && '
        'CountIf(Table(t.Value.columns), Text(Value.name) = Text(r.Value.toColumn)) = 1) = 1)) = 0',
        f'CountIf(Table({snapshot}.relationships) As r, !And({",".join(optional_rel)})) = 0',
        allowed_keys(snapshot + ".guidance", GUIDANCE_KEYS),
        f'CountIf(ColumnNames({snapshot}.guidance), If(Value = "linguisticMetadataPresent", '
        f'!(JSON(Column({snapshot}.guidance, Value)) in ["true","false"]), '
        f'!({string_check("Column(" + snapshot + ".guidance, Value)")}))) = 0',
    ]
    table_checks = [
        allowed_keys(table, TABLE_KEYS), string_check(table + ".name", 256, True),
        f'!IsMatch(Text({table}.name), ",", MatchOptions.Contains)',
        string_check(table + ".description"), f'JSON({table}.hidden) in ["true","false"]',
        f'StartsWith(JSON({table}.columns), "[") && CountRows({columns}) <= 2048',
        f'StartsWith(JSON({table}.measures), "[") && CountRows({measures}) <= 2048',
        f'CountRows(Distinct(ForAll({columns}, Lower(Text(Value.name))), Value)) = CountRows({columns})',
        f'CountRows(Distinct(ForAll({measures}, Lower(Text(Value.name))), Value)) = CountRows({measures})',
        f'CountIf({columns} As c, !And({allowed_keys(col, COLUMN_KEYS)}, {string_check(col + ".name", 256, True)}, '
        f'{string_check(col + ".type", 64, True)}, {string_check(col + ".description")}, JSON({col}.hidden) in ["true","false"])) = 0',
        f'CountIf({measures} As m, !And({allowed_keys(measure, MEASURE_KEYS)}, {string_check(measure + ".name", 256, True)}, '
        f'{string_check(measure + ".description")}, {string_check(measure + ".formatString")}, JSON({measure}.expressionAvailable) = "false")) = 0',
    ]
    checks.append(f'CountIf(Table({snapshot}.tables) As t, !And({",".join(table_checks)})) = 0')
    # Variadic And avoids a deeply left-nested && tree exceeding the native evaluator's call-depth bound.
    return "=IfError(And(" + ",".join(checks) + "), false)"


PROBE_EXPRESSION = '''= "EVALUATE ROW(""AccessProbe"", 1 + " &
Concat(Table(Topic.Config.snapshot.tables) As t,
    With({n:"'" & Substitute(Text(t.Value.name), "'", "''") & "'",
          cols:Filter(Table(t.Value.columns), !StartsWith(Text(Value.name), "RowNumber-"))},
        "COUNTROWS(TOPN(0, " &
        If(CountRows(cols) = 0, n,
            "SELECTCOLUMNS(" & n & ", " &
            Concat(Sequence(CountRows(cols)) As i,
                """c" & Text(i.Value - 1, "0", "en-US") & """, " & n & "[" &
                Substitute(Text(Index(cols, i.Value).Value.name), "]", "]]") & "]", ", ") & ")") &
        "))"), " + ") & ")"'''


def catalog_expression():
    # Only materialized after the full-reference probe succeeds.
    constants = ", ".join(k + ":" + fx_text(v) for k, v in CATALOG_POLICY.items())
    return '''=JSON({modelAlias:"primary", snapshotHash:Topic.ConfigSnapshotHash,
preparedAtUtc:Topic.ConfigPreparedAtUtc, ''' + constants + ''',
tables:ForAll(Table(Topic.Config.snapshot.tables),
    {name:Text(Value.name), hidden:Boolean(Value.hidden),
     columns:CountRows(Table(Value.columns)), measures:CountRows(Table(Value.measures))}),
measures:ParseJSON("[" & Concat(Filter(ForAll(Table(Topic.Config.snapshot.tables) As t,
    {Part:Concat(Table(t.Value.measures) As m,
        JSON({table:Text(t.Value.name), name:Text(m.Value.name), description:Text(m.Value.description),
              formatString:Text(m.Value.formatString), expressionAvailable:false}), ",")}),
    !IsBlank(Part)), Part, ",") & "]"),
relationships:Topic.Config.snapshot.relationships, guidance:Topic.Config.snapshot.guidance})'''


class ConfigurationBoundary:
    def __init__(self, prefix):
        self.names = environment_names(prefix)

    require_metadata = (
        '=IsBlank(Global.SchemaConfiguration) || Global.SchemaConfiguration <> Topic.ConfigDocument || '
        'Global.SchemaSnapshot <> Topic.ConfigSnapshotHash || IsBlank(System.LastMessage.Id) || '
        'IsBlank(System.User.Id) || Global.SchemaTurn <> System.LastMessage.Id || Global.SchemaUser <> System.User.Id'
    )
    metadata_result = (
        '="{""utcNow"":""" & Topic.UtcNow & """,""schema"":" & If(Topic.view = "catalog", Topic.CatalogJson, '
        '"{""snapshotHash"":" & JSON(Topic.ConfigSnapshotHash) & ",""preparedAtUtc"":" & JSON(Topic.ConfigPreparedAtUtc) & '
        '",""tables"":[" & Concat(Filter(Topic.SchemaRows, Name in Topic.SelectedNames), Payload, ",") & "]}") & "}"'
    )

    def initialize(self, metadata):
        chunks = ", ".join(f"{{Index:{i}, Raw:Coalesce(Env.{name}, {fx_text(UNCONFIGURED)})}}"
                           for i, name in enumerate(self.names[1:], 1))
        header_checks = [
            f'Text(Topic.ConfigManifest.contract) = {fx_text(CONTRACT)}',
            allowed_keys("Topic.ConfigManifest", MANIFEST_KEYS),
            'CountRows(ColumnNames(Topic.ConfigManifest)) = 8',
            'Text(Topic.ConfigManifest.environmentId) = Lower(Text(System.Bot.EnvironmentId))',
            'IsMatch(Text(Topic.ConfigManifest.snapshotHash), "^[0-9a-f]{64}$")',
            f'Value(Topic.ConfigManifest.chunkCount) >= 1 && Value(Topic.ConfigManifest.chunkCount) <= {CHUNK_COUNT}',
            'Value(Topic.ConfigManifest.chunkCount) = RoundDown(Value(Topic.ConfigManifest.chunkCount), 0)',
            'IsMatch(JSON(Topic.ConfigManifest.chunkCount), "^[1-9][0-9]*$")',
            'IsMatch(JSON(Topic.ConfigManifest.payloadLength), "^[1-9][0-9]*$")',
            f'Value(Topic.ConfigManifest.payloadLength) >= 1 && Value(Topic.ConfigManifest.payloadLength) <= {MAX_DOCUMENT}',
        ]
        for field in ("revision", "environmentId", "workspaceId", "datasetId"):
            header_checks += [
                f'IsMatch(Text(Topic.ConfigManifest.{field}), {fx_text(GUID_PATTERN)})',
                f'!IsMatch(Text(Topic.ConfigManifest.{field}), "^[0\\-]+$")',
            ]
        bind_checks = [
            allowed_keys("Topic.Config", DOCUMENT_KEYS), 'CountRows(ColumnNames(Topic.Config)) = 7',
            *(f'Text(Topic.Config.{k}) = Text(Topic.ConfigManifest.{k})' for k in MANIFEST_KEYS[:6]),
        ]
        actions = [
            set_value("stage", "configuration_validation", "ConfigStage_f92LmN"),
            set_value("Global.AnalyticsStage", "configuration_validation", "ConfigGlobalStage_d32HbP"),
            set_value("ConfigManifestText", f'=Coalesce(Env.{self.names[0]}, "")', "ConfigManifest_h72KmQ"),
            _closed("ConfigMissing_b62KwE", '=IsBlank(Topic.ConfigManifestText) || Topic.ConfigManifestText = "NOT_CONFIGURED"', "NOT_CONFIGURED"),
            _closed("ConfigManifestSize_k23LmD", "=Len(Topic.ConfigManifestText) > 2000", "CONFIG_TOO_LARGE"),
            set_value("ConfigManifest", '=IfError(ParseJSON(Topic.ConfigManifestText), ParseJSON("{}"))', "ConfigParse_n93LkQ"),
            _closed("ConfigHeader_e32HtR", "=!IfError(And(" + ",".join(header_checks) + "), false)", "CONFIG_INVALID_MANIFEST_OR_TARGET"),
            set_value("ConfigChunks", "=Table(" + chunks + ")", "ConfigChunks_v82JyW"),
            _closed("ConfigChunks_g92KsT",
                '=CountIf(Topic.ConfigChunks, If(Index > Value(Topic.ConfigManifest.chunkCount), Raw <> "NOT_CONFIGURED", '
                f'Len(Raw) <= {CHUNK_HEADER} || Len(Raw) > {CHUNK_HEADER + CHUNK_PAYLOAD} || '
                f'Left(Raw,{CHUNK_HEADER}) <> Text(Topic.ConfigManifest.revision) & "|" & Text(Index,"000","en-US") & "|" & '
                'Text(Value(Topic.ConfigManifest.chunkCount),"000","en-US") & "|" || '
                f'(Index < Value(Topic.ConfigManifest.chunkCount) && Len(Raw) <> {CHUNK_HEADER + CHUNK_PAYLOAD}))) > 0',
                "CONFIG_INCOMPLETE_OR_MIXED_REVISION"),
            set_value("ConfigDocument", f'=Concat(Filter(Topic.ConfigChunks, Index <= Value(Topic.ConfigManifest.chunkCount)), Mid(Raw,{CHUNK_HEADER + 1},{CHUNK_PAYLOAD}))', "ConfigJoin_p32TgJ"),
            _closed("ConfigLength_z52RkT", "=Len(Topic.ConfigDocument) <> Value(Topic.ConfigManifest.payloadLength)", "CONFIG_LENGTH_MISMATCH"),
            set_value("Config", '=IfError(ParseJSON(Topic.ConfigDocument), ParseJSON("{}"))', "ConfigDocument_w62PsL"),
            _closed("ConfigBinding_c82DfR", "=!IfError(And(" + ",".join(bind_checks) + "), false)", "CONFIG_INVALID_DOCUMENT_OR_BINDING"),
            set_value("ConfigSnapshotValid", snapshot_valid_expression(), "ConfigShape_y72VqS"),
            _closed("ConfigSnapshot_b52NpR", "=!Topic.ConfigSnapshotValid", "CONFIG_INVALID_METADATA"),
            set_value("ConfigSnapshotHash", "=Text(Topic.Config.snapshotHash)", "ConfigHash_t92JhM"),
            set_value("ConfigPreparedAtUtc", "=Text(Topic.Config.snapshot.retrievedAtUtc)", "ConfigTimestamp_g22BtD"),
            # Clear authorization on exact content changes, not just owner-supplied revision/hash changes.
            {"kind": "ConditionGroup", "id": "ConfigInvalidate_x32QhJ", "conditions": [{
                "id": "ConfigChanged_r23GhY", "condition": "=Global.LoadedConfiguration <> Topic.ConfigDocument",
                "actions": [set_value("Global." + n, "", "ClearConfig_" + n) for n in
                            ("SchemaSnapshot", "SchemaTurn", "SchemaUser", "SchemaConfiguration", "MetadataFailureKey")],
            }]},
            set_value("Global.LoadedConfiguration", "=Topic.ConfigDocument", "ConfigLoaded_f62NjR"),
        ]
        if metadata:
            # Invalidate before EVERY fresh probe, even if a previous same-turn probe succeeded.
            actions += [set_value("Global." + n, "", "InvalidateProbe_" + n)
                        for n in ("SchemaSnapshot", "SchemaTurn", "SchemaUser", "SchemaConfiguration")]
            actions += [set_value("ConfigProbe", PROBE_EXPRESSION, "ConfigProbe_m82TrV")]
        stage = "metadata_input_validation" if metadata else "query_input_validation"
        actions += [set_value("stage", stage, "ConfigReadyStage_n32BxL"),
                    set_value("Global.AnalyticsStage", stage, "ConfigReadyGlobal_h92KgM")]
        return actions

    def authorized(self):
        return [
            set_value("Global.SchemaConfiguration", "=Topic.ConfigDocument", "AuthorizeConfig_a82PqW"),
            set_value("ConfigSchemaRows",
                '=ForAll(Table(Topic.Config.snapshot.tables), {Name:Lower(Text(Value.name)), Payload:JSON(Value)})',
                "ConfigRows_v32NtY"),
            set_value("ConfigCatalogJson", catalog_expression(), "ConfigCatalog_u72VrQ"),
        ]


def environment_variable_declarations(environment_prefix):
    """Authoring EnvironmentVariableDefinitionNoKind objects (not botcomponents)."""
    return [{"schemaName": name, "displayName": name, "type": "String",
             "defaultValue": UNCONFIGURED} for name in environment_names(environment_prefix)]


def global_variable_declarations(schema_name, topics):
    """Full authoring declarations; native botcomponent.data is the nested Variable."""
    validate_names(schema_name, schema_name, schema_name)
    names = set(re.findall(r"Global\.([A-Za-z][A-Za-z0-9_]*)", compact(topics)))
    return {
        name: {"kind": "GlobalVariableComponent", "schemaName": schema_name + ".globalvariable." + name,
               "description": "Internal native analytics provenance/configuration state; never supplied by callers.",
               "variable": {"name": name, "scope": "Conversation", "aIVisibility": "Hidden",
                            "isExternalInitializationAllowed": False, "isOutputToExternalCallers": False,
                            "defaultValue": 0 if name in ("MetadataAttempts", "QueryAttempts") else ""}}
        for name in sorted(names)
    }


def native_botcomponent_declarations(schema_name, topics, globals_):
    """Verified native metadata and data bodies, excluding parent-owned GPT/bot.

    Type 12 = Bot variable (V2); its data is `kind: Variable`, NOT a full
    GlobalVariableComponent wrapper and not an invented ExternalVariable kind.
    parentbotid is a solution schema-key lookup, not a Dataverse REST GUID binding.
    """
    validate_names(schema_name, schema_name, schema_name)
    result = []
    for name, body in topics.items():
        result.append({
            "schemaname": schema_name + ".topic." + name, "componenttype": BOTCOMPONENT_TYPES["topic"],
            "name": body.get("modelDisplayName", "Generated query error"),
            "parentbotid": {"schemaname": schema_name}, "statecode": 0, "statuscode": 1,
            "data": copy.deepcopy(body),
        })
    for name, declaration in globals_.items():
        if declaration["schemaName"] != schema_name + ".globalvariable." + name:
            raise ValueError("Global declaration belongs to a different agent schema.")
        result.append({
            "schemaname": declaration["schemaName"], "componenttype": BOTCOMPONENT_TYPES["globalVariable"],
            "name": name, "parentbotid": {"schemaname": schema_name}, "statecode": 0, "statuscode": 1,
            "data": {"kind": "Variable", **copy.deepcopy(declaration["variable"])},
        })
    return result


def environment_variable_links(schema_name, topics, definitions):
    """Native botcomponent_environmentvariabledefinitionset relationship records.

    Keys exactly match Microsoft's public native solution source attributes.
    Each topic is linked to only the Env definitions its body actually references.
    """
    validate_names(schema_name, schema_name, schema_name)
    available = {definition["schemaName"] for definition in definitions}
    result = []
    for name, body in topics.items():
        references = set(re.findall(r"\bEnv\.([A-Za-z][A-Za-z0-9_]*)", compact(body)))
        if not references <= available:
            raise ValueError("Topic references an undeclared environment variable.")
        result.extend({
            "botcomponentid.schemaname": schema_name + ".topic." + name,
            "environmentvariabledefinitionid.schemaname": reference, "iscustomizable": 1,
        } for reference in sorted(references))
    return result


def source_files(bundle):
    """Return 148 authored YAML source strings for offline validation/hashing.

    This is not a PAC project writer. Native solution botcomponent data must come
    from bundle['botcomponents'], not the full globals wrappers in this source map.
    """
    from studio_yaml import dumps
    return {
        **{f"topics/{name}.mcs.yml": dumps(body) for name, body in bundle["topics"].items()},
        **{f"variables/{name}.mcs.yml": dumps(body) for name, body in bundle["globals"].items()},
        **{f"environmentvariables/{body['schemaName']}.mcs.yml":
           dumps({"kind": "EnvironmentVariableDefinition", **body}) for body in bundle["environmentVariables"]},
    }


def build_portable_bundle(*, schema_name, environment_prefix, connection_reference):
    """Package-builder API: four native topics, globals, env definitions and manifest.

    Input is public component naming ONLY. No model or target IDs or snapshot accepted.
    environmentVariables entries use BotDefinition.environmentVariables NoKind shape.
    """
    validate_names(schema_name, environment_prefix, connection_reference)
    boundary = ConfigurationBoundary(environment_prefix)
    config = {"connectionReference": connection_reference,
              "workspaceId": "=Text(Topic.Config.workspaceId)", "datasetId": "=Text(Topic.Config.datasetId)"}
    topics = {
        "ModelMetadata": build_metadata_topic(config, None, runtime=boundary),
        "GeneratedDaxQuery": build_query_topic(config, None, runtime=boundary),
        "GeneratedDaxAdvice": build_query_topic(config, None, advice=True, runtime=boundary),
        "GeneratedQueryError": build_error_topic(),
    }
    # Unexpected config expression errors must not echo unpublished snapshot contents.
    error_actions = topics["GeneratedQueryError"]["beginDialog"]["actions"]
    error_actions.insert(0, _closed("ConfigUnexpected_u32PsV",
        '=Global.AnalyticsStage = "configuration_validation"', "CONFIG_EVALUATION_ERROR"))
    globals_ = global_variable_declarations(schema_name, topics)
    env = environment_variable_declarations(environment_prefix)
    native = native_botcomponent_declarations(schema_name, topics, globals_)
    links = environment_variable_links(schema_name, topics, env)
    return {
        "topics": topics, "globals": globals_, "environmentVariables": env,
        "botcomponents": native, "environmentVariableLinks": links,
        "contract": {
            "version": CONTRACT, "environmentPrefix": environment_prefix, "schemaName": schema_name,
            "connectionReference": connection_reference, "chunkCount": CHUNK_COUNT,
            "chunkPayloadCharacters": CHUNK_PAYLOAD, "chunkHeaderCharacters": CHUNK_HEADER,
            "maxDocumentCharacters": MAX_DOCUMENT, "maxValueCharacters": VALUE_LIMIT,
            "unconfiguredValue": UNCONFIGURED, "unusedChunkValue": UNCONFIGURED,
            "botcomponentTypes": dict(BOTCOMPONENT_TYPES),
            "environmentVariableDefinitionType": 100000000,
            "environmentVariableRelationship": "botcomponent_environmentvariabledefinition",
            "counts": {
                "topics": len(topics), "globals": len(globals_), "environmentDefinitions": len(env),
                "nativeBotcomponentsExcludingGpt": len(native), "environmentVariableLinks": len(links),
                "externalVariableBotcomponents": 0, "sourceFiles": len(topics) + len(globals_) + len(env),
            },
            "configurationPublication": "Update private current environment values, then explicitly publish in Studio.",
            "runtimeBackend": "Native Copilot Studio topics and end-user Power BI connector; no Python service.",
        },
    }

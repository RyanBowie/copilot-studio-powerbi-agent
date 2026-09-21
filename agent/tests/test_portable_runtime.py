"""Offline-only portable configuration contracts; all data here is synthetic."""
import copy
import json
from pathlib import Path
import re
import unittest
from unittest.mock import Mock, patch
import urllib.parse
from uuid import UUID

from configure_portable import (
    Destination, changeset, prepare, private_output, validate_package,
)
from general_runtime import (
    build_metadata_topic, build_query_topic, build_error_topic, fx_text,
    metadata_catalog, schema_probe, snapshot_hash,
)
from portable_runtime import (
    CHUNK_COUNT, CHUNK_HEADER, CHUNK_PAYLOAD, CONTRACT, GUID_PATTERN, MAX_DOCUMENT,
    ConfigurationBoundary, PROBE_EXPRESSION, build_portable_bundle, catalog_expression,
    compact, decode_configuration, environment_names, make_configuration,
    reviewed_snapshot, snapshot_valid_expression, environment_variable_declarations,
    global_variable_declarations, native_botcomponent_declarations, environment_variable_links, source_files,
    build_portable_instructions,
)

ROOT = Path(__file__).resolve().parents[1]
# Deterministic synthetic identities, never literals requiring a publication-scanner exemption.
ENV, WORKSPACE, DATASET, REVISION, TENANT, AGENT = (str(UUID(int=i)) for i in range(1, 7))
PREFIX = "test_Analytics"
SCHEMA_NAME = "test_Analyst"
CONNECTION = "test_PowerBI"
TARGET = dict(tenantId=TENANT, environmentId=ENV, dataverseUrl="https://synthetic.crm.dynamics.com",
              agentId=AGENT, schemaName=SCHEMA_NAME, environmentPrefix=PREFIX,
              connectionReference=CONNECTION, workspaceId=WORKSPACE, datasetId=DATASET)


def snapshot():
    result = json.loads((ROOT / "metadata.example.json").read_text(encoding="utf-8"))
    result.pop("example")
    result["sourceBinding"] = dict(tenantId=TENANT, workspaceId=WORKSPACE, datasetId=DATASET)
    return reviewed_snapshot(result)


def values_for(s=None, **overrides):
    args = dict(environment_id=ENV, workspace_id=WORKSPACE, dataset_id=DATASET, revision=REVISION, prefix=PREFIX)
    args.update(overrides)
    return make_configuration(s or snapshot(), **args)


def fixture_document(s, revision=REVISION):
    """Independent synthetic wire document, including deliberately oversized fixtures."""
    s = reviewed_snapshot(s)
    return dict(contract=CONTRACT, revision=revision, environmentId=ENV,
                workspaceId=WORKSPACE, datasetId=DATASET, snapshotHash=snapshot_hash(s), snapshot=s)


def snapshot_with_payload_length(length):
    """Use bounded descriptions to hit an exact ASCII JSON transport length."""
    s = snapshot()
    s["relationships"] = []
    s["tables"] = [
        dict(name=f"Boundary{i:03}", description="", hidden=False, columns=[], measures=[])
        for i in range(64)
    ]
    remaining = length - len(compact(fixture_document(s)))
    if not 0 <= remaining <= len(s["tables"]) * 4096:
        raise ValueError("Requested fixture length exceeds its bounded description capacity.")
    for table in s["tables"]:
        size = min(remaining, 4096)
        table["description"] = "X" * size
        remaining -= size
    assert remaining == 0
    assert len(compact(fixture_document(s))) == length
    return s


def unicode_snapshot():
    """Actual non-BMP/control characters; one JSON Unicode escape crosses a chunk boundary."""
    s = snapshot()
    s["relationships"] = []
    sample = 'quote " backslash \\ newline\n carriage\r tab\t null\0 BMP \u03a9\u6f22 combining e\u0301 astral \U0001f680\U0001f642 separators \u2028\u2029 '
    s["tables"] = [
        dict(name="O'Brien_\u03a9_\U0001f680", description=sample * 16, hidden=False,
             columns=[dict(name="A]B_\u6f22_\U0001f642", type="string", description=sample, hidden=False)],
             measures=[dict(name="Measure_\u03a9", description=sample, formatString='0.00 "\u20ac"',
                            expressionAvailable=False)]),
        dict(name="Empty_\u6f22", description="", hidden=False, columns=[], measures=[]),
    ]
    document = compact(fixture_document(s))
    encoded_sample = json.dumps(sample, ensure_ascii=True)[1:-1]
    escape_at = document.index(encoded_sample) + encoded_sample.index("\\u03a9")
    padding = (CHUNK_PAYLOAD - 1 - escape_at) % CHUNK_PAYLOAD
    s["tables"][0]["description"] = "X" * padding + s["tables"][0]["description"]
    return reviewed_snapshot(s)


def overflow_fixture_values():
    """Forge a valid JSON document into 128 slots with a 1901-character final payload."""
    s = snapshot_with_payload_length(MAX_DOCUMENT + 1)
    document = compact(fixture_document(s))
    names = environment_names(PREFIX)
    values = values_for()
    manifest = json.loads(values[names[0]])
    manifest.update(chunkCount=CHUNK_COUNT, payloadLength=len(document), snapshotHash=snapshot_hash(s))
    values[names[0]] = compact(manifest)
    for index, name in enumerate(names[1:], 1):
        end = index * CHUNK_PAYLOAD if index < CHUNK_COUNT else len(document)
        values[name] = f"{REVISION}|{index:03}|{CHUNK_COUNT:03}|" + document[(index - 1) * CHUNK_PAYLOAD:end]
    return values


def bundle():
    return build_portable_bundle(schema_name=SCHEMA_NAME, environment_prefix=PREFIX, connection_reference=CONNECTION)


def flattened(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from flattened(child)
    elif isinstance(value, list):
        for child in value:
            yield from flattened(child)


def fx_context(document, expression, *, extra="", global_state=None):
    fields = "Config:ParseJSON(" + fx_text(compact(document)) + ")"
    if extra:
        fields += "," + extra
    outer = "Global:" + (global_state or "{SchemaConfiguration:\"\",SchemaSnapshot:\"\",SchemaTurn:\"\",SchemaUser:\"\"}")
    outer += ', System:{Bot:{EnvironmentId:' + fx_text(ENV) + ',TenantId:' + fx_text(TENANT) + '},LastMessage:{Id:"turn"},User:{Id:"user"}}'
    return "With({" + outer + "},With({Topic:{" + fields + "}}," + expression.lstrip("=") + "))"


def native_configuration_transport_cases():
    """Exact generated config guards/join/parse/shape expressions, no topic/connector execution."""
    actions = {a["id"]: a for a in ConfigurationBoundary(PREFIX).initialize(metadata=True)}

    def value(identifier):
        return actions[identifier]["value"].removeprefix("=")

    def condition(identifier):
        return actions[identifier]["conditions"][0]["condition"].removeprefix("=")

    def context(values, expression):
        names = environment_names(PREFIX)
        chunks = "Table(" + ",".join(
            "{Index:" + str(i) + ",Raw:" + fx_text(values[name]) + "}"
            for i, name in enumerate(names[1:], 1)) + ")"
        return ("With({System:{Bot:{EnvironmentId:" + fx_text(ENV) + ",TenantId:" + fx_text(TENANT) +
                "}}},With({Topic:{ConfigManifest:ParseJSON(" + fx_text(values[names[0]]) +
                "),ConfigChunks:" + chunks + "}}," + expression + "))")

    def pipeline(values):
        # Each nested record models the preceding SetVariable output, preserving the
        # generated expressions verbatim. This does not emulate the AdaptiveDialog host.
        parsed = (
            "With({Topic:{ConfigManifest:Topic.ConfigManifest,ConfigDocument:Topic.ConfigDocument,Config:" +
            value("ConfigDocument_w62PsL") + "}},If(" + condition("ConfigBinding_c82DfR") +
            ',"binding",If(' + value("ConfigShape_y72VqS") + ',JSON(Topic.Config),"shape")))'
        )
        joined = (
            "With({Topic:{ConfigManifest:Topic.ConfigManifest,ConfigDocument:" +
            value("ConfigJoin_p32TgJ") + "}},If(" + condition("ConfigLength_z52RkT") +
            ',"length",' + parsed + "))"
        )
        return context(values, "If(" + condition("ConfigHeader_e32HtR") + ',"manifest",If(' +
                       condition("ConfigChunks_g92KsT") + ',"chunks",' + joined + "))")

    def deserialize(values):
        # Runtime nodes materialize ConfigDocument and Config separately. Folding the
        # subsequent shape validator into all these With/If scopes adds artificial
        # call depth in RecalcEngine for snapshots with columns. Check those stages
        # separately below; do not raise runner limits or change runtime expressions.
        return context(values, "With({Topic:{ConfigDocument:" + value("ConfigJoin_p32TgJ") +
                       "}},JSON(" + value("ConfigDocument_w62PsL") + "))")

    maximum_snapshot = snapshot_with_payload_length(MAX_DOCUMENT)
    maximum = values_for(maximum_snapshot)
    unicode_s = unicode_snapshot()
    unicode_values = values_for(unicode_s)
    small_revision = str(UUID(int=128))
    small = values_for(revision=small_revision)
    small_count = json.loads(small[environment_names(PREFIX)[0]])["chunkCount"]
    partial = dict(maximum)
    partial.update({name: small[name] for name in environment_names(PREFIX)[:small_count + 1]})
    complete = {**maximum, **small}
    overflow = overflow_fixture_values()
    cases = [
        {"name": "portable-boundary-max-128-chunks-accepted",
         "expression": context(maximum, condition("ConfigChunks_g92KsT")), "expected": False},
        {"name": "portable-boundary-max-243200-exact-join",
         "expression": context(maximum, value("ConfigJoin_p32TgJ")),
         "expected": compact(fixture_document(maximum_snapshot))},
        {"name": "portable-boundary-max-deserialized-config-valid",
         "expression": pipeline(maximum), "parseResultJson": True,
         "expected": fixture_document(maximum_snapshot)},
        {"name": "portable-boundary-plus-one-manifest-rejected",
         "expression": pipeline(overflow), "expected": "manifest"},
        {"name": "portable-boundary-plus-one-final-payload-rejected",
         "expression": context(overflow, condition("ConfigChunks_g92KsT")), "expected": True},
        {"name": "portable-boundary-unicode-split-escape-exact-join",
         "expression": context(unicode_values, value("ConfigJoin_p32TgJ")),
         "expected": compact(fixture_document(unicode_s))},
        {"name": "portable-boundary-unicode-deserialized-config-valid",
         "expression": deserialize(unicode_values), "parseResultJson": True,
         "expected": fixture_document(unicode_s)},
        {"name": "portable-boundary-unicode-probe-preserved",
         "expression": fx_context(fixture_document(unicode_s), PROBE_EXPRESSION),
         "expected": schema_probe(unicode_s)},
        {"name": "portable-boundary-unicode-catalog-preserved",
         "expression": fx_context(fixture_document(unicode_s), catalog_expression(),
             extra="ConfigSnapshotHash:" + fx_text(snapshot_hash(unicode_s)) +
                   ",ConfigPreparedAtUtc:" + fx_text(unicode_s["retrievedAtUtc"])),
         "parseResultJson": True, "expected": metadata_catalog(unicode_s)},
        {"name": "portable-boundary-large-to-small-all-slots-replaced",
         "expression": deserialize(complete), "parseResultJson": True,
         "expected": fixture_document(snapshot(), small_revision)},
        {"name": "portable-boundary-large-to-small-stale-trailing-rejected",
         "expression": pipeline(partial), "expected": "chunks"},
    ]
    for name, values, document in (
        ("unicode", unicode_values, fixture_document(unicode_s)),
        ("large-to-small", complete, fixture_document(snapshot(), small_revision)),
    ):
        cases.extend([
            {"name": "portable-boundary-" + name + "-deserialized-shape-valid",
             "expression": fx_context(document, snapshot_valid_expression()), "expected": True},
            {"name": "portable-boundary-" + name + "-deserialized-binding-valid",
             "expression": fx_context(document, condition("ConfigBinding_c82DfR"),
                 extra="ConfigManifest:ParseJSON(" + fx_text(values[environment_names(PREFIX)[0]]) + ")"),
             "expected": False},
        ])
    cases.append({"name": "portable-boundary-large-to-small-reset-chunks-accepted",
                  "expression": context(complete, condition("ConfigChunks_g92KsT")), "expected": False})
    for name, values in (("maximum", maximum), ("unicode", unicode_values)):
        names = environment_names(PREFIX)
        manifest = json.loads(values[names[0]])
        cases.append({
            "name": "portable-boundary-" + name + "-native-value-lengths",
            "expression": context(values,
                "JSON({payloadCharacters:Len(" + value("ConfigJoin_p32TgJ") +
                "),manifestCharacters:Len(" + fx_text(values[names[0]]) +
                "),chunks:ForAll(Topic.ConfigChunks,{index:Index,characters:Len(Raw)})})"),
            "parseResultJson": True,
            "expected": {
                "payloadCharacters": manifest["payloadLength"],
                "manifestCharacters": len(values[names[0]]),
                "chunks": [{"index": i, "characters": len(values[n])}
                           for i, n in enumerate(names[1:], 1)],
            },
        })
    return cases


def native_portable_cases():
    """Expressions evaluated by the Microsoft.PowerFx runner, NOT a simulated live agent."""
    values = values_for()
    document = decode_configuration(values, PREFIX, ENV)
    s = document["snapshot"]
    cases = [
        {"name": "portable-full-reference-probe-equals-demonstrated-generator",
         "expression": fx_context(document, PROBE_EXPRESSION), "expected": schema_probe(s)},
        {"name": "portable-snapshot-shape-valid", "expression": fx_context(document, snapshot_valid_expression()), "expected": True},
        {"name": "portable-catalog-equals-demonstrated-metadata",
         "expression": fx_context(document, catalog_expression(),
             extra="ConfigSnapshotHash:" + fx_text(snapshot_hash(s)) + ",ConfigPreparedAtUtc:" + fx_text(s["retrievedAtUtc"])),
         "expected": metadata_catalog(s), "parseResultJson": True},
    ]
    for name, mutate in [
        ("missing-columns", lambda d: d["snapshot"]["tables"][0].pop("columns")),
        ("wrong-column-type", lambda d: d["snapshot"]["tables"][0]["columns"][0].update(type=5)),
        ("extra-secret-field", lambda d: d["snapshot"]["tables"][0].update(partitions=[{"secret": "not for output"}])),
        ("mismatched-source", lambda d: d["snapshot"]["sourceBinding"].update(datasetId=ENV)),
        ("empty-tables", lambda d: d["snapshot"].update(tables=[])),
        ("broken-relationship", lambda d: d["snapshot"]["relationships"][0].update(fromColumn="missing")),
        ("non-utc-timestamp", lambda d: d["snapshot"].update(retrievedAtUtc="2026-01-01T00:00:00-05:00")),
        ("wrong-tenant", lambda d: d["snapshot"]["sourceBinding"].update(tenantId=ENV)),
        ("malformed-guidance", lambda d: d["snapshot"].update(guidance={"authoredInstructions": {"private": "not text"}})),
        ("malformed-relationship", lambda d: d["snapshot"]["relationships"][0].update(isActive={"private": "not Boolean"})),
    ]:
        changed = copy.deepcopy(document)
        mutate(changed)
        cases.append({"name": "portable-shape-rejects-" + name,
                      "expression": fx_context(changed, snapshot_valid_expression()), "expected": False})
    escaped = copy.deepcopy(document)
    escaped["snapshot"]["relationships"] = []
    escaped["snapshot"]["tables"] = [{
        "name": "O'Brien", "description": "", "hidden": False,
        "columns": [{"name": "A]B", "type": "string", "description": "", "hidden": False},
                    {"name": "RowNumber-skipped", "type": "int64", "description": "", "hidden": True}],
        "measures": [],
    }, {"name": "Empty", "description": "", "hidden": False, "columns": [], "measures": []}]
    cases.append({"name": "portable-probe-escapes-identifiers-and-keeps-empty-tables",
                  "expression": fx_context(escaped, PROBE_EXPRESSION),
                  "expected": schema_probe(escaped["snapshot"])})
    boundary = ConfigurationBoundary(PREFIX)
    actions = {a["id"]: a for a in boundary.initialize(metadata=True)}
    original_manifest = json.loads(values[environment_names(PREFIX)[0]])
    for name, mutate in [
        ("valid", lambda m: None),
        ("wrong-environment", lambda m: m.update(environmentId=WORKSPACE)),
        ("zero-workspace", lambda m: m.update(workspaceId=str(UUID(int=0)))),
        ("bad-version", lambda m: m.update(contract="unknown")),
        ("string-count", lambda m: m.update(chunkCount="1")),
        ("fractional-count", lambda m: m.update(chunkCount=1.5)),
        ("oversized-count", lambda m: m.update(chunkCount=129)),
        ("bad-hash", lambda m: m.update(snapshotHash="bad")),
        ("missing-field", lambda m: m.pop("revision")),
        ("extra-field", lambda m: m.update(other="untrusted")),
    ]:
        manifest = copy.deepcopy(original_manifest)
        mutate(manifest)
        cases.append({"name": "portable-manifest-" + name,
            "expression": fx_context(document, actions["ConfigHeader_e32HtR"]["conditions"][0]["condition"],
                extra="ConfigManifest:ParseJSON(" + fx_text(compact(manifest)) + ")"),
            "expected": name != "valid"})
    for name, change, expected in [
        ("valid", {}, False), ("target-change", {"workspaceId": ENV}, True),
        ("revision-change", {"revision": ENV}, True), ("extra-key", {"other": "bad"}, True),
    ]:
        cases.append({"name": "portable-document-" + name,
            "expression": fx_context({**document, **change}, actions["ConfigBinding_c82DfR"]["conditions"][0]["condition"],
                extra="ConfigManifest:ParseJSON(" + fx_text(compact(original_manifest)) + ")"),
            "expected": expected})
    condition = actions["ConfigChunks_g92KsT"]["conditions"][0]["condition"]
    for name, mutate in [
        ("valid", lambda v: None),
        ("missing", lambda v: v.update({environment_names(PREFIX)[1]: ""})),
        ("mixed-revision", lambda v: v.update({environment_names(PREFIX)[1]: v[environment_names(PREFIX)[1]].replace(REVISION, ENV)})),
        ("wrong-index", lambda v: v.update({environment_names(PREFIX)[1]: v[environment_names(PREFIX)[1]].replace("|001|", "|002|", 1)})),
        ("oversized", lambda v: v.update({environment_names(PREFIX)[1]: "X" * 2001})),
        ("unexpected-trailing", lambda v: v.update({environment_names(PREFIX)[-1]: "junk"})),
    ]:
        changed = dict(values)
        mutate(changed)
        chunk_table = "Table(" + ",".join("{Index:" + str(i) + ",Raw:" + fx_text(changed[n]) + "}"
                                       for i, n in enumerate(environment_names(PREFIX)[1:], 1)) + ")"
        extra = "ConfigManifest:ParseJSON(" + fx_text(changed[environment_names(PREFIX)[0]]) + "),ConfigChunks:" + chunk_table
        cases.append({"name": "portable-chunks-" + name, "expression": fx_context(document, condition, extra=extra),
                      "expected": name != "valid"})
    for name, old, same_user, expected in [
        ("same-provenance", compact(document), True, False),
        ("different-config-same-hash", compact({**document, "workspaceId": ENV}), True, True),
        ("different-user", compact(document), False, True),
        ("never-authorized", "", True, True),
    ]:
        global_state = "{SchemaConfiguration:" + fx_text(old) + ",SchemaSnapshot:" + fx_text(document["snapshotHash"]) + \
                       ',SchemaTurn:"turn",SchemaUser:' + fx_text("user" if same_user else "other") + "}"
        cases.append({"name": "portable-auth-" + name, "expression": fx_context(document, boundary.require_metadata,
            extra="ConfigDocument:" + fx_text(compact(document)) + ",ConfigSnapshotHash:" + fx_text(document["snapshotHash"]),
            global_state=global_state), "expected": expected})
    return cases + native_configuration_transport_cases()


class PortableGptTests(unittest.TestCase):
    def test_real_instructions_and_other_settings_preserved_without_source_mutation(self):
        import yaml
        source_path = ROOT / "agent.mcs.yml"
        original_bytes = source_path.read_bytes()
        original = yaml.safe_load(original_bytes)
        gpt = build_portable_instructions()
        self.assertEqual(gpt["kind"], "GptComponentMetadata")
        self.assertTrue(gpt["instructions"].endswith(original["instructions"]))
        self.assertEqual(gpt["instructions"].count(original["instructions"]), 1)
        self.assertNotIn("model", gpt["aISettings"])
        self.assertEqual(gpt["aISettings"], {k: v for k, v in original["aISettings"].items() if k != "model"})
        unchanged_keys = set(original) - {"aISettings", "instructions", "conversationStarters"}
        self.assertEqual({k: gpt[k] for k in unchanged_keys}, {k: original[k] for k in unchanged_keys})
        self.assertEqual(set(gpt), set(original))
        self.assertEqual(source_path.read_bytes(), original_bytes)
        # Returned metadata is independent; mutations cannot poison subsequent builds.
        gpt["gptCapabilities"]["webBrowsing"] = True
        self.assertFalse(build_portable_instructions()["gptCapabilities"]["webBrowsing"])

    def test_configuration_behavior_is_conditional_and_starters_are_model_agnostic(self):
        gpt = build_portable_instructions()
        instructions = gpt["instructions"]
        self.assertIn("explicitly reports NOT_CONFIGURED", instructions)
        self.assertIn("When configuration is valid and metadata visibility is verified", instructions)
        self.assertIn("perform the requested analysis", instructions)
        self.assertIn("do not relabel them NOT_CONFIGURED", instructions)
        self.assertNotIn("UNCONFIGURED STARTER", instructions.upper())
        self.assertNotIn("real source deployment", instructions.lower())
        self.assertEqual(len(gpt["conversationStarters"]), 5)
        starters = compact(gpt["conversationStarters"]).lower()
        for assumption in ("risk", "tool count", "used agents", "creators", "recorded interactions", "authoring surface"):
            self.assertNotIn(assumption, starters)
        source = compact(gpt)
        for forbidden in ("PreviewModels", "modelNameHint", "Env.", "ConfigDocument"):
            self.assertNotIn(forbidden, source)
        self.assertFalse(set(gpt["aISettings"]) & {"model", "modelNameHint", "provider"})
        self.assertIsNone(re.search(GUID_PATTERN.removeprefix("^").removesuffix("$"), source))

    def test_missing_invalid_or_historical_source_fails_instead_of_synthesizing(self):
        import yaml
        with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                build_portable_instructions()
        for source in (
            {"kind": "AdaptiveDialog", "instructions": "Not agent metadata."},
            {"kind": "GptComponentMetadata", "instructions": ""},
            {"kind": "GptComponentMetadata", "instructions": "UNCONFIGURED STARTER: always stop."},
        ):
            with patch("pathlib.Path.read_text", return_value=yaml.safe_dump(source)):
                with self.assertRaises(ValueError):
                    build_portable_instructions()


class PortableRuntimeTests(unittest.TestCase):
    def test_package_api_native_shapes_and_counts(self):
        import yaml
        b = bundle()
        self.assertEqual(b["contract"]["counts"], {
            "topics": 4, "globals": 15, "environmentDefinitions": 129,
            "nativeBotcomponentsExcludingGpt": 19, "environmentVariableLinks": 387,
            "externalVariableBotcomponents": 0, "sourceFiles": 148,
        })
        self.assertEqual(environment_variable_declarations(PREFIX), b["environmentVariables"])
        self.assertEqual(global_variable_declarations(SCHEMA_NAME, b["topics"]), b["globals"])
        self.assertEqual(native_botcomponent_declarations(SCHEMA_NAME, b["topics"], b["globals"]), b["botcomponents"])
        self.assertEqual(environment_variable_links(SCHEMA_NAME, b["topics"], b["environmentVariables"]),
                         b["environmentVariableLinks"])
        self.assertEqual(len(source_files(b)), 148)
        self.assertEqual(yaml.safe_load(source_files(b)["variables/SchemaConfiguration.mcs.yml"]),
                         b["globals"]["SchemaConfiguration"])
        for component in b["botcomponents"]:
            self.assertEqual(component["parentbotid"], {"schemaname": SCHEMA_NAME})
            self.assertEqual((component["statecode"], component["statuscode"]), (0, 1))
            if component["componenttype"] == 12:
                self.assertEqual(component["data"]["kind"], "Variable")
                self.assertEqual(component["data"]["scope"], "Conversation")
                self.assertEqual(component["data"]["aIVisibility"], "Hidden")
                self.assertNotIn("variable", component["data"])
            else:
                self.assertEqual(component["componenttype"], 9)
                self.assertEqual(component["data"]["kind"], "AdaptiveDialog")

    def test_environment_links_are_exact_native_topic_dependencies(self):
        b = bundle()
        expected_names = set(environment_names(PREFIX))
        for name in ("ModelMetadata", "GeneratedDaxQuery", "GeneratedDaxAdvice"):
            links = [l for l in b["environmentVariableLinks"]
                     if l["botcomponentid.schemaname"] == SCHEMA_NAME + ".topic." + name]
            self.assertEqual({l["environmentvariabledefinitionid.schemaname"] for l in links}, expected_names)
            self.assertTrue(all(l["iscustomizable"] == 1 for l in links))
        self.assertFalse(any(l["botcomponentid.schemaname"].endswith(".GeneratedQueryError")
                             for l in b["environmentVariableLinks"]))
        with self.assertRaisesRegex(ValueError, "undeclared"):
            environment_variable_links(SCHEMA_NAME, b["topics"], b["environmentVariables"][:-1])
        with self.assertRaisesRegex(ValueError, "different agent"):
            native_botcomponent_declarations("other_Agent", b["topics"], b["globals"])

    def test_roundtrip_and_limits(self):
        values = values_for()
        self.assertEqual(len(values), CHUNK_COUNT + 1)
        self.assertLessEqual(max(map(len, values.values())), 2000)
        doc = decode_configuration(values, PREFIX, ENV)
        self.assertEqual(doc["snapshot"], snapshot())
        self.assertEqual(doc["snapshotHash"], snapshot_hash(snapshot()))
        self.assertEqual(len(f"{REVISION}|001|128|"), CHUNK_HEADER)
        self.assertEqual(MAX_DOCUMENT, CHUNK_PAYLOAD * CHUNK_COUNT)

    def test_exact_maximum_128_occupied_chunks_roundtrip(self):
        s = snapshot_with_payload_length(MAX_DOCUMENT)
        package = prepare(s, TARGET, REVISION)
        # Exercise actual JSON persistence/deserialization, not only in-memory values.
        restored = json.loads(json.dumps(package, ensure_ascii=True))
        values = restored["values"]
        names = environment_names(PREFIX)
        manifest = json.loads(values[names[0]])
        self.assertEqual((manifest["chunkCount"], manifest["payloadLength"]), (128, 243200))
        self.assertEqual(len(values), 129)
        for index, name in enumerate(names[1:], 1):
            raw = values[name]
            self.assertTrue(raw.startswith(f"{REVISION}|{index:03}|128|"))
            self.assertEqual(len(raw), CHUNK_HEADER + CHUNK_PAYLOAD)
            self.assertEqual(len(raw[CHUNK_HEADER:]), 1900)
            self.assertNotEqual(raw, "NOT_CONFIGURED")
        joined = "".join(values[name][CHUNK_HEADER:] for name in names[1:])
        self.assertEqual(joined, compact(fixture_document(s)))
        self.assertEqual(len(joined), 243200)
        self.assertTrue(joined.isascii())
        self.assertEqual(len(joined.encode("utf-8")), 243200)
        self.assertEqual(len(joined.encode("utf-16-le")) // 2, 243200)
        self.assertEqual(decode_configuration(values, PREFIX, ENV), fixture_document(s))
        self.assertEqual(validate_package(restored, environment_id=ENV, dataverse_url=TARGET["dataverseUrl"],
                                         tenant_id=TENANT, agent_id=AGENT), TARGET)
        for raw in values.values():
            self.assertTrue(raw.isascii())
            self.assertEqual(len(raw), len(raw.encode("utf-16-le")) // 2)
            self.assertLessEqual(len(raw), 2000)

    def test_one_ascii_unit_over_maximum_rejected_before_and_after_serialization(self):
        s = snapshot_with_payload_length(MAX_DOCUMENT + 1)
        document = compact(fixture_document(s))
        self.assertEqual(len(document), 243201)
        self.assertTrue(document.isascii())
        self.assertEqual(len(document.encode("utf-16-le")) // 2, 243201)
        self.assertEqual(json.loads(document)["snapshot"], s)
        with self.assertRaisesRegex(ValueError, "CONFIG_TOO_LARGE"):
            values_for(s)
        forged = json.loads(json.dumps(overflow_fixture_values()))
        # A value can be below the platform slot limit but above this contract's payload limit.
        self.assertEqual(len(forged[environment_names(PREFIX)[-1]]), CHUNK_HEADER + 1901)
        self.assertLessEqual(max(map(len, forged.values())), 2000)
        with self.assertRaisesRegex(ValueError, "CONFIG_CHUNK_REVISION"):
            decode_configuration(forged, PREFIX, ENV)
        package = dict(contract=CONTRACT, destination=TARGET, values=forged)
        with self.assertRaises(ValueError):
            validate_package(package, environment_id=ENV, dataverse_url=TARGET["dataverseUrl"],
                             tenant_id=TENANT, agent_id=AGENT)

    def test_large_to_small_changeset_resets_every_stale_current_chunk(self):
        large = values_for(snapshot_with_payload_length(MAX_DOCUMENT))
        small = values_for(revision=str(UUID(int=128)))
        names = environment_names(PREFIX)
        count = json.loads(small[names[0]])["chunkCount"]
        self.assertLess(count, CHUNK_COUNT)
        self.assertTrue(all(large[name] != "NOT_CONFIGURED" for name in names[1:]))
        self.assertTrue(all(small[name] == "NOT_CONFIGURED" for name in names[count + 1:]))
        definitions, names_by_id = {}, {}
        for index, name in enumerate(names, 1):
            row_id = str(UUID(int=2000 + index))
            names_by_id[row_id] = name
            definitions[name] = {
                "environmentvariabledefinitionid": str(UUID(int=1000 + index)),
                "environmentvariabledefinition_environmentvariablevalue": [{
                    "environmentvariablevalueid": row_id, "value": large[name], "@odata.etag": 'W/"123"'}],
            }
        body, _ = changeset(TARGET["dataverseUrl"], small, definitions)
        blocks = body.decode("utf-8").split("Content-ID: ")[1:]
        self.assertEqual(len(blocks), 129)
        current, touched = dict(large), set()
        for block in blocks:
            match = re.search(r"PATCH [^\r\n]*/environmentvariablevalues\(([^)]+)\) HTTP/1.1", block)
            self.assertIsNotNone(match)
            self.assertIn('If-Match: W/"123"', block)
            name = names_by_id[match.group(1)]
            self.assertNotIn(name, touched)
            touched.add(name)
            payload = json.loads(next(line for line in block.splitlines() if line.startswith("{")))
            self.assertEqual(set(payload), {"value"})
            current[name] = payload["value"]
        self.assertEqual(touched, set(names))
        self.assertEqual(current, small)
        self.assertTrue(all(current[name] == "NOT_CONFIGURED" for name in names[count + 1:]))
        self.assertEqual(decode_configuration(json.loads(json.dumps(current)), PREFIX, ENV),
                         fixture_document(snapshot(), str(UUID(int=128))))
        partial = dict(large)
        partial.update({name: small[name] for name in names[:count + 1]})
        with self.assertRaisesRegex(ValueError, "CONFIG_TRAILING_CHUNK"):
            decode_configuration(partial, PREFIX, ENV)

    def test_unicode_json_escapes_roundtrip_as_ascii_and_equal_utf16_units(self):
        s = unicode_snapshot()
        description = s["tables"][0]["description"]
        self.assertGreater(len(description.encode("utf-16-le")) // 2, len(description))
        values = json.loads(json.dumps(values_for(s), ensure_ascii=True))
        names = environment_names(PREFIX)
        manifest = json.loads(values[names[0]])
        document = "".join(values[name][CHUNK_HEADER:] for name in names[1:manifest["chunkCount"] + 1])
        self.assertEqual(document, compact(fixture_document(s)))
        for escaped in ('\\"', "\\\\", "\\n", "\\r", "\\t", "\\u0000", "\\u03a9",
                        "\\u6f22", "\\u0301", "\\ud83d\\ude80", "\\u2028", "\\u2029"):
            self.assertIn(escaped, document)
        # Ensure the fixture actually splits an escape rather than merely including Unicode.
        self.assertTrue(any(
            match.start() < boundary < match.end()
            for match in re.finditer(r"\\u[0-9a-f]{4}", document)
            for boundary in range(CHUNK_PAYLOAD, len(document), CHUNK_PAYLOAD)))
        self.assertEqual(decode_configuration(values, PREFIX, ENV), fixture_document(s))
        self.assertEqual(manifest["payloadLength"], len(document))
        for raw in [document, *values.values()]:
            self.assertTrue(raw.isascii())
            self.assertEqual(len(raw), len(raw.encode("utf-8")))
            self.assertEqual(len(raw), len(raw.encode("utf-16-le")) // 2)
        self.assertLessEqual(max(map(len, values.values())), 2000)

    def test_native_configuration_transport_boundary_case_inventory(self):
        cases = native_configuration_transport_cases()
        self.assertEqual(len(cases), 18)
        self.assertEqual(len({case["name"] for case in cases}), 18)
        self.assertTrue(all(case["name"].startswith("portable-boundary-") for case in cases))

    def test_fail_closed_documents(self):
        for mutate in (
            lambda v: v.pop(environment_names(PREFIX)[2]),
            lambda v: v.update({environment_names(PREFIX)[0]: "NOT_CONFIGURED"}),
            lambda v: v.update({environment_names(PREFIX)[0]: "{"}),
            lambda v: v.update({environment_names(PREFIX)[1]: ""}),
            lambda v: v.update({environment_names(PREFIX)[1]: "x" * 2001}),
            lambda v: v.update({environment_names(PREFIX)[-1]: "x"}),
            lambda v: v.update({environment_names(PREFIX)[1]: v[environment_names(PREFIX)[1]].replace(REVISION, ENV)}),
        ):
            values = values_for()
            mutate(values)
            with self.assertRaises((ValueError, KeyError)):
                decode_configuration(values, PREFIX, ENV)
        with self.assertRaises(ValueError):
            decode_configuration(values_for(), PREFIX, WORKSPACE)

    def test_oversized_and_private_definition_shapes_rejected(self):
        for mutate in (
            lambda s: s.update(example=True),
            lambda s: s["tables"][0].update(partitions=[]),
            lambda s: s["tables"][1]["measures"][0].update(expression="COUNTROWS('Event')"),
            lambda s: s["tables"][0]["columns"][0].update(type=3),
            lambda s: s["sourceBinding"].update(datasetId=ENV),
        ):
            s = snapshot()
            mutate(s)
            with self.assertRaises(ValueError):
                values_for(s)
        s = snapshot()
        s["relationships"] = []
        s["tables"] = [{**copy.deepcopy(s["tables"][0]), "name": "Table" + str(i),
                        "description": "X" * 4096} for i in range(65)]
        with self.assertRaisesRegex(ValueError, "CONFIG_TOO_LARGE"):
            values_for(s)

    def test_bundle_is_unconfigured_public_native_code_not_synthetic_runtime(self):
        b = bundle()
        self.assertEqual(set(b["topics"]), {"ModelMetadata", "GeneratedDaxQuery", "GeneratedDaxAdvice", "GeneratedQueryError"})
        self.assertEqual(b["environmentVariables"][0]["defaultValue"], "NOT_CONFIGURED")
        self.assertTrue(all(v["defaultValue"] == "NOT_CONFIGURED" for v in b["environmentVariables"]))
        self.assertEqual(b["contract"]["unusedChunkValue"], "NOT_CONFIGURED")
        self.assertEqual(len(b["environmentVariables"]), 129)
        source = compact(b)
        self.assertIsNone(re.search(GUID_PATTERN.removeprefix("^").removesuffix("$"), source))
        for private in (ENV, WORKSPACE, DATASET, REVISION, "Synthetic entity dimension", "2026-01-01"):
            self.assertNotIn(private, source)
        for variable in b["globals"].values():
            self.assertEqual(variable["variable"]["aIVisibility"], "Hidden")
            self.assertFalse(variable["variable"]["isExternalInitializationAllowed"])

    def test_config_never_declared_as_ai_input_or_external_variable(self):
        b = build_portable_bundle(schema_name="poc_PowerBIQueryRuntime",
            environment_prefix="poc_PowerBIQueryRuntime_Config",
            connection_reference="poc_PowerBIQueryRuntime_PowerBI")
        self.assertNotIn("ExternalVariable", compact(b))
        for definition in b["environmentVariables"]:
            self.assertNotIn("aIVisibility", definition)
            self.assertEqual(definition["defaultValue"], "NOT_CONFIGURED")
        for topic in b["topics"].values():
            for part in ("inputs", "inputType", "outputType", "modelDescription", "modelDisplayName"):
                self.assertNotIn("Env.", compact(topic.get(part)))
                self.assertNotIn("ConfigDocument", compact(topic.get(part)))
            self.assertNotIn("externalVariables", topic)
        self.assertTrue(all(v["variable"]["aIVisibility"] == "Hidden" and
                            not v["variable"]["isOutputToExternalCallers"] for v in b["globals"].values()))

    def test_query_and_advice_retain_all_non_configuration_actions(self):
        config = {"connectionReference": CONNECTION, "workspaceId": WORKSPACE, "datasetId": DATASET}
        b = bundle()
        for name, advice in (("GeneratedDaxQuery", False), ("GeneratedDaxAdvice", True)):
            original = build_query_topic(config, snapshot(), advice)["beginDialog"]["actions"]
            portable = b["topics"][name]["beginDialog"]["actions"]
            by_id = {a["id"]: a for a in portable}
            for old in original:
                if old["id"] in ("RequireMetadata", "ExecuteGeneratedQuery"):
                    continue
                self.assertEqual(old, by_id[old["id"]], old["id"])
            self.assertEqual([a["id"] for a in portable if a["id"] in {v["id"] for v in original}],
                             [a["id"] for a in original])
        self.assertFalse(any(n.get("kind") == "InvokeConnectorAction" for n in flattened(b["topics"]["GeneratedDaxAdvice"])))

    def test_metadata_retains_probe_decoder_and_all_other_core_nodes(self):
        config = {"connectionReference": CONNECTION, "workspaceId": WORKSPACE, "datasetId": DATASET}
        old = build_metadata_topic(config, snapshot())
        new = bundle()["topics"]["ModelMetadata"]
        by_id = {a["id"]: a for a in new["beginDialog"]["actions"]}
        changed = {"VerifyCallerSchemaVisibility", "setGlobalSchemaSnapshot", "setSchemaRows", "setCatalogJson", "setresult_2"}
        for action in old["beginDialog"]["actions"]:
            if action["id"] not in changed:
                self.assertEqual(action, by_id[action["id"]], action["id"])

    def test_authorization_and_outputs_only_after_probe(self):
        b = bundle()
        actions = b["topics"]["ModelMetadata"]["beginDialog"]["actions"]
        ids = [a["id"] for a in actions]
        self.assertLess(ids.index("ConfigMissing_b62KwE"), ids.index("VerifyCallerSchemaVisibility"))
        self.assertLess(ids.index("RequireVerifiedVisibility"), ids.index("AuthorizeConfig_a82PqW"))
        self.assertLess(ids.index("RequireVerifiedVisibility"), ids.index("ConfigCatalog_u72VrQ"))
        self.assertLess(ids.index("RequireVerifiedVisibility"), ids.index("ConfigRows_v32NtY"))
        for name in ("ModelMetadata", "GeneratedDaxQuery", "GeneratedDaxAdvice"):
            self.assertFalse(any("Config" in k for k in b["topics"][name]["outputType"]["properties"]))
        for n in flattened(b["topics"]):
            if n.get("kind") == "InvokeConnectorAction":
                self.assertEqual(n["connectionProperties"], {"mode": "Invoker"})
                self.assertEqual(n["input"]["binding"]["impersonatedUserName"], "=Blank()")
                self.assertEqual(n["input"]["binding"]["groupid"], "=Text(Topic.Config.workspaceId)")
                self.assertEqual(n["input"]["binding"]["datasetid"], "=Text(Topic.Config.datasetId)")

    def test_schema_reference_invalidation_and_error_sanitization(self):
        b = bundle()
        for name in ("ModelMetadata", "GeneratedDaxQuery", "GeneratedDaxAdvice"):
            for n in flattened(b["topics"][name]):
                if n.get("kind") == "SendActivity":
                    self.assertNotIn("{Topic.Config", n["activity"])
            actions = b["topics"][name]["beginDialog"]["actions"]
            branch = next(a for a in actions if a["id"] == "ConfigInvalidate_x32QhJ")
            self.assertIn("Global.LoadedConfiguration <> Topic.ConfigDocument", branch["conditions"][0]["condition"])
        error = b["topics"]["GeneratedQueryError"]["beginDialog"]["actions"]
        self.assertTrue(error[0]["id"].startswith("ConfigUnexpected"))
        self.assertEqual(error[1:], build_error_topic()["beginDialog"]["actions"])

    def test_failure_memory_survives_probe_invalidation(self):
        actions = bundle()["topics"]["ModelMetadata"]["beginDialog"]["actions"]
        ids = [a["id"] for a in actions]
        self.assertLess(ids.index("ConfigLoaded_f62NjR"), ids.index("StopRepeatedMetadataFailure"))
        self.assertLess(ids.index("InvalidateProbe_SchemaConfiguration"), ids.index("VerifyCallerSchemaVisibility"))
        self.assertFalse(any(a.get("variable") == "Global.MetadataFailureKey" for a in actions))
        invalidator = next(a for a in actions if a["id"] == "ConfigInvalidate_x32QhJ")
        self.assertEqual(invalidator["conditions"][0]["condition"], "=Global.LoadedConfiguration <> Topic.ConfigDocument")


class PortableHelperTests(unittest.TestCase):
    def fake_destination(self, change=None):
        """Only in-memory GET responses; never construct an authenticated Destination."""
        from studio_yaml import dumps
        b = bundle()
        components = [{"botcomponentid": str(UUID(int=100 + i)), "schemaname": c["schemaname"],
                       "componenttype": c["componenttype"], "data": dumps(c["data"])}
                      for i, c in enumerate(b["botcomponents"])]
        state = {"components": components, "dropLink": False, "defaultValue": "NOT_CONFIGURED"}
        if change:
            change(state)
        dest = Destination.__new__(Destination)
        dest.target = dict(TARGET)

        def get(path):
            if path.startswith("bots("):
                return dict(schemaname=SCHEMA_NAME, authenticationmode=2, authenticationtrigger=1, accesscontrolpolicy=2)
            if path.startswith("connectionreferences?"):
                return {"value": [{"connectionid": "synthetic-bound-connection",
                                   "connectorid": "/providers/Microsoft.PowerApps/apis/shared_powerbi"}]}
            if path.startswith("botcomponents?"):
                return {"value": state["components"]}
            if ")/botcomponent_environmentvariabledefinition?" in path:
                names = environment_names(PREFIX)
                return {"value": [{"schemaname": n} for n in (names[:-1] if state["dropLink"] else names)]}
            if path.startswith("environmentvariabledefinitions?"):
                query = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)
                name = query["$filter"][0].split("'")[1]
                return {"value": [{"environmentvariabledefinitionid": AGENT, "schemaname": name,
                                  "type": 100000000, "defaultvalue": state["defaultValue"],
                                  "environmentvariabledefinition_environmentvariablevalue": []}]}
            raise AssertionError("Unexpected endpoint: " + path)

        dest.get = Mock(side_effect=get)
        return dest

    def test_preflight_checks_native_components_links_and_explicit_defaults(self):
        dest = self.fake_destination()
        self.assertEqual(set(dest.preflight()), set(environment_names(PREFIX)))
        self.assertEqual(sum(")/botcomponent_environmentvariabledefinition?" in c.args[0]
                             for c in dest.get.call_args_list), 3)
        for change in (
            lambda s: s.update(dropLink=True),
            lambda s: s.update(defaultValue=""),
            lambda s: s["components"][-1].update(data="kind: Variable\nname: Wrong"),
            lambda s: s["components"].pop(),
            lambda s: s["components"].append(copy.deepcopy(s["components"][0])),
            lambda s: s["components"].append({**s["components"][0], "schemaname": SCHEMA_NAME + ".topic.Stale"}),
        ):
            with self.assertRaises(RuntimeError):
                self.fake_destination(change).preflight()

    def package(self):
        return prepare(snapshot(), TARGET, REVISION)

    def test_explicit_target_required_and_checked_without_auth(self):
        package = self.package()
        args = dict(environment_id=ENV, dataverse_url=TARGET["dataverseUrl"], tenant_id=TENANT, agent_id=AGENT)
        self.assertEqual(validate_package(package, **args), TARGET)
        for key in args:
            changed = {**args, key: "different"}
            with self.assertRaisesRegex(ValueError, "EXPLICIT_DESTINATION_MISMATCH"):
                validate_package(package, **changed)
        with self.assertRaises(ValueError):
            private_output(ROOT / "bad.private.json")

    def test_discovery_validates_url_tenant_environment_and_state(self):
        live = dict(Id=AGENT, EnvironmentId=ENV, TenantId=TENANT, Url=TARGET["dataverseUrl"],
                    ApiUrl="https://synthetic.api.crm.dynamics.com", State=0)
        Destination.verify_discovery(TARGET, live)
        for key, value in (("EnvironmentId", WORKSPACE), ("TenantId", ENV), ("State", 1),
                           ("Url", "https://other.crm.dynamics.com")):
            with self.assertRaises(RuntimeError):
                Destination.verify_discovery(TARGET, {**live, key: value})

    def test_transaction_contains_only_value_writes_with_concurrency(self):
        values = values_for()
        definitions = {
            name: {"environmentvariabledefinitionid": AGENT,
                   "environmentvariabledefinition_environmentvariablevalue": []}
            for name in values
        }
        first = next(iter(values))
        definitions[first]["environmentvariabledefinition_environmentvariablevalue"] = [
            {"environmentvariablevalueid": ENV, "@odata.etag": 'W/"123"'}]
        body, content_type = changeset(TARGET["dataverseUrl"], values, definitions)
        text = body.decode()
        self.assertIn('If-Match: W/"123"', text)
        self.assertEqual(text.count("Content-ID:"), len(values))
        self.assertIn("multipart/mixed; boundary=batch_", content_type)
        self.assertIn("EnvironmentVariableDefinitionId@odata.bind", text)
        for forbidden in ("botcomponents(", "PvaPublish", "connectionreferences(", "bots("):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()

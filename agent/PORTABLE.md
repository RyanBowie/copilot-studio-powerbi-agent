# Configure an imported native runtime without replacing its topics

This is the **agent-side configuration boundary** for the full demonstrated native
Power BI runtime. It is not a stop-only starter, a synthetic data source, a Python
runtime, an external service, a Fabric data agent, or a claim of new live validation.
**Agent365 is a custom example model/report, not Microsoft's Agent 365 product.**

The package builder owns the native solution ZIP and its import verification. This
module supplies real portable topic definitions and the configuration contract.
Import the ZIP first; bind the adopter's connection, choose the supported agent
model in Studio, prepare/review private model metadata, update configuration values,
and explicitly publish in Studio. No model-specific topic regeneration or replacement
is part of this path. `general_runtime.generate()` / `deploy.py` remain a separate,
backwards-compatible legacy source-deployment path.

## Supported platform boundary

- Copilot Studio supports **read-only environment variables**. Non-secret values are
  captured at agent publication; updating them alone does **not** update the published
  runtime. Republish, then start a new conversation.
  [Variables overview](https://learn.microsoft.com/microsoft-copilot-studio/authoring-variables-about#environment-variables).
- Microsoft ships actual native topic YAML reading `Env.fac_DiningWebAppUrl` in
  a `SetVariable` Power Fx expression.
  [Microsoft CopilotStudioSamples native topic](https://github.com/microsoft/CopilotStudioSamples/blob/main/EmployeeSelfServiceAgent/Facilities/EmployeeGetDiningMenu/topic.yaml).
  We use the same `Env.<definition-schema-name>` access, not an invented
  environment-variable loader kind or a JSON object disguised as a variable reference.
- A platform environment-variable value is limited to **2,000 characters**.
  [Environment variables limitations](https://learn.microsoft.com/power-apps/maker/data-platform/environmentvariables#current-limitations).
  A realistic model snapshot cannot be squeezed into one such value.
- The installed authoring schema was checked with `schema-lookup.bundle.js` for
  `GlobalVariableComponent`, `VariableNoKind`, `EnvironmentVariableDefinition`,
  `EnvironmentVariableType`, `SetVariable`, `ConditionGroup`, and
  `InvokeConnectorAction`. Hidden provenance variables use the nested `variable`
  form and `aIVisibility: Hidden`, **not** the obsolete flat global-variable example.

### AI visibility and external-variable declarations

The checked authoring schema has **no `ExternalVariable` definition**, and
`EnvironmentVariableDefinition` does **not** accept `aIVisibility` (additional
properties are forbidden). Do not add either an invented `ExternalVariable` kind
or `aIVisibility` to environment-variable definitions.

The supported `aIVisibility: Hidden` property is on `VariableNoKind`, nested within
each `GlobalVariableComponent`. Those declarations also explicitly disable
`isExternalInitializationAllowed` and `isOutputToExternalCallers`.

This bundle reads configuration via `Env` **inside deterministic topic nodes**.
It does not add config/catalog values to GPT instructions, AI-visible global
variables, topic inputs, external inputs, descriptions, or pre-gate tool outputs.
Configuration and assembled snapshots remain internal topic state; the two
conversation-wide configuration comparisons use explicitly hidden globals.
Only the existing post-probe `result` output exposes selected catalog/table metadata.
This verifies the authored exposure boundary, not an observation of the service's
internal orchestrator context. The exact artifact's native import/readback passed
and verified persistence of its component bodies and configuration links; see
[import evidence](../solution/import-verification.json). Publication, complete
topic execution and service-internal environment-variable visibility remain
separate unperformed checks. Do not claim a stronger visibility control than the
schema provides or treat import-only evidence as production readiness.

Environment configuration is trusted owner/admin input, not chat input. Restrict
Dataverse configuration-write permissions accordingly. Environment variables are not
secret storage: do not put tokens, passwords, raw definitions, source queries,
partitions or roles in them. The configuration helper rejects those schema shapes.

## Pure package-builder API

Import `agent/portable_runtime.py` on the Python path:

```python
from portable_runtime import build_portable_bundle
bundle = build_portable_bundle(
    schema_name=imported_agent_schema_name,
    environment_prefix=package_configuration_prefix,
    connection_reference=imported_powerbi_reference_logical_name,
)
```

This call has no file reads of private configuration, file writes, credentials, or
network calls. It accepts **component naming only**, never workspace/dataset IDs or
a source snapshot.

For the separately named release selected by the parent, call with
`schema_name="poc_PowerBIQueryRuntime"` and
`connection_reference="poc_PowerBIQueryRuntime_PowerBI"`.
`poc_PowerBIQueryRuntime_Config` is a compatible proposed configuration prefix;
the parent must use its selected prefix consistently. The parent owns the distinct
solution lineage `poc_PowerBIQueryRuntime`, display name **Power BI Query Runtime**,
version **1.0.0.0**, and **PowerBIQueryRuntime_unmanaged.zip**. This does not rename
the historical starter or inherit its import-verification claim.

| Returned key | Contents / parent integration |
|---|---|
| `topics` | Dictionary of the complete `ModelMetadata`, `GeneratedDaxQuery`, `GeneratedDaxAdvice`, `GeneratedQueryError` AdaptiveDialog bodies. Serialize with existing `studio_yaml.dumps`; package as the four active native topic data bodies, schema names `<schema_name>.topic.<name>`. Do not package stale legacy fixed-query topics. |
| `globals` | Dictionary of full schema-checked `GlobalVariableComponent` authoring declarations, schema names `<schema_name>.globalvariable.<name>`. `variable` is the nested `VariableNoKind` body. All are Conversation-scoped, Hidden, with external initialization and output disabled. Counters default to 0; strings default to empty. Do **not** use this full wrapper as native botcomponent data; the native representation is supplied below. |
| `environmentVariables` | `BotDefinition.environmentVariables` **NoKind** declaration objects: `schemaName`, `displayName`, `type: String`, `defaultValue`. Package as ordinary Dataverse Text definitions (`100000000`). These are **not** botcomponents and are not conversation globals. |
| `botcomponents` | 19 native descriptors: four type-9 topics plus fifteen type-12 globals. Each supplies `schemaname`, `componenttype`, `name`, `parentbotid: {schemaname: <agent>}`, `statecode: 0`, `statuscode: 1`, and complete native `data`. Serialize **only `data`** into each native data file. Global data is `kind: Variable`, with the nested variable's fields flattened under it. GPT is intentionally excluded; obtain its Author-owned data from `build_portable_instructions()` below and package as type 15. |
| `environmentVariableLinks` | 387 native topic-to-definition association records. Keys are `botcomponentid.schemaname`, `environmentvariabledefinitionid.schemaname`, and `iscustomizable: 1`. Package in `Assets/botcomponent_environmentvariabledefinitionset.xml`; each record becomes a `botcomponent_environmentvariabledefinition` element with the first two keys as attributes and `iscustomizable` as a child. |
| `contract` | Public JSON object with version, component naming, prefix and size/count constants. Publish it beside the ZIP so adopters use the exact prefix/reference. No private values. |

Callable declaration helpers:

```python
environment_variable_declarations(environment_prefix)              # 129
global_variable_declarations(schema_name, topics)                   # 15
native_botcomponent_declarations(schema_name, topics, globals_)     # 19
environment_variable_links(schema_name, topics, definitions)        # 387
source_files(bundle)                                               # 148 path -> YAML strings
```

`source_files()` is a **pure authored-source map for offline validation/hashing**,
not a PAC project or clone writer. It contains 4 `topics/`, 15 `variables/` (full
authoring wrappers), and 129 `environmentvariables/` declarations. It creates no
files and includes no agent/settings file, GPT, contract JSON, ZIP, or current values.
Native packaging must use the supplied `botcomponents[*].data`, not reinterpret the
source map as native solution data.

The native source subtotal represented by this API is **168 files** when the parent
uses one `botcomponent.xml` plus one `data` file per component (38), one XML per
environment definition (129), and one association-set XML (1). Parent-owned bot,
GPT, connection reference and solution manifest files are additional. Adding GPT's
two files makes that subtotal 170, **not the complete package file count**.

### Author-owned portable GPT data

The package builder must use this helper rather than mutate GPT instructions,
retain a historical starter-stop prefix, or replace instructions through a later
source deployment:

```python
from portable_runtime import build_portable_instructions
from studio_yaml import dumps

gpt_data = build_portable_instructions()  # complete GptComponentMetadata dictionary
gpt_yaml = dumps(gpt_data)               # native type-15 GPT component data
```

This **build-time-only** helper reads the real public `agent.mcs.yml` adjacent to
`portable_runtime.py`. It does not read template/download copies or private
configuration, write files, or call a service. It rejects a missing/invalid source
or a historical `UNCONFIGURED STARTER` prompt rather than synthesize a replacement.
It leaves the source file unchanged.

- Retains the complete original analyst instruction text **verbatim**.
- Prepends brief conditional configuration guidance: report `NOT_CONFIGURED` only
  when a native tool returns it; stop that request without inventing schema/data.
  Other errors keep their actual provenance. Valid configuration and verified
  metadata proceed into the retained full analyst behavior.
- Removes the entire tenant-dependent `aISettings.model` selection; it does not
  choose another provider/model. The adopter chooses a supported model in Studio.
- Uses five model-agnostic conversation starters, with no assumed agent-usage,
  risk, creator, interaction or platform fields.
- Preserves all other GPT metadata, including disabled web browsing, code
  interpreter, model knowledge and file analysis.

The return value is the **full data body**, not a string and not a botcomponent
wrapper. Parent packaging still supplies the proven native GPT component identity
and XML, but must serialize this body without an additional instruction mutation.
The package display name belongs in the native bot/component metadata, not an
invented `displayName` field in `GptComponentMetadata`.

This helper is intentionally separate: `build_portable_bundle()` still returns 19
non-GPT native components, and `source_files(bundle)` still returns 148 sources.
Adding this GPT source gives **149 authored sources / 20 native botcomponents**.
Fingerprint the GPT body separately or include it in the parent's whole-package
manifest; the unchanged topic/config bundle hash does not cover GPT instructions.

### Verified native mapping, not ExternalVariable

- The official [botcomponent table reference](https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/botcomponent#componenttype)
  defines **9 = Topic (V2), 12 = Bot variable (V2), 15 = Custom GPT**. Type 12 is
  **not** an ExternalVariable type.
- Microsoft's [native variable component XML](https://github.com/microsoft/Templates-for-Power-Platform/blob/main/Solutions/mpa_AwardsRecognitionCopilot/src/botcomponents/mpa_awardsAndRecognition.component.RatingsCount/botcomponent.xml)
  verifies type 12, `parentbotid/schemaname` linking and active state/status.
  Its adjacent [native data file](https://github.com/microsoft/Templates-for-Power-Platform/blob/main/Solutions/mpa_AwardsRecognitionCopilot/src/botcomponents/mpa_awardsAndRecognition.component.RatingsCount/data)
  verifies `kind: Variable` and `aIVisibility: Hidden`. Our Conversation scope and
  defaults are additionally checked against the installed `Variable` schema.
- Microsoft's [native environment association-set XML](https://github.com/microsoft/contoso-real-estate-power-platform/blob/main/src/portal/solution/ContosoRealEstatePortal/src/Assets/botcomponent_environmentvariabledefinitionset.xml)
  verifies the direct topic-to-definition relationship and schema-key attributes.
  The associated native Search topic reads `Env` directly. The official
  [relationship reference](https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/botcomponent#BKMK_botcomponent_environmentvariabledefinition)
  confirms the collection navigation property `botcomponent_environmentvariabledefinition`.

Exactly three topics read all 129 definitions, giving **387 links**. The error
topic has no Env reads and receives no such links. There are **zero environment-backed
ExternalVariable botcomponents**: configuration uses supported native `Env` references,
ordinary Text definitions, and the verified native association set. Never create
129 type-12 configuration globals or invent an ExternalVariable kind to satisfy
these dependencies.

The helpers deliberately do not create or overwrite `agent.mcs.yml`, an authentication
configuration, a connector definition, a ZIP, or a new agent. Use the Author-owned
GPT helper above and the proven native bot/connection-reference shape.
Adopters configure their own agent model and connection in Studio. Both native
Power BI calls remain **Invoker**, with `impersonatedUserName = Blank()`.

### Public definition defaults

There are **129** Text definitions:

1. `<prefix>_Manifest`, default `NOT_CONFIGURED`.
2. `<prefix>_Chunk001` through `<prefix>_Chunk128`, default `NOT_CONFIGURED`.

Every definition has a **nonempty** default, including unused chunk slots. This
avoids a blank value being treated as a missing default during publication/test.
`make_configuration()` also writes `NOT_CONFIGURED` for unused current-value slots;
do not omit these definitions or replace their defaults with empty strings.

**No 129-field manual-entry setup is required.** The importer may expose all 129
configuration defaults; leave them at the shipped `NOT_CONFIGURED` values rather
than entering metadata or chunk values individually. After import, the batch
configuration helper updates only current values for all 129 entries, including
resetting every unused chunk slot to `NOT_CONFIGURED`. It leaves the definitions
and their defaults unchanged.

Ship **no current value rows** and no private default values. The unconfigured guard
is data-driven: a reviewed configured manifest/chunk set reaches the retained runtime.
The prefix is explicit to prevent accidental sharing of configuration by two agents.
Do not change the prefix or slot count after import: those are package-contract
changes, unlike changing configuration values.

### Private value format and limits

The manifest is compact JSON with:

```
contract, revision, environmentId, workspaceId, datasetId,
snapshotHash, chunkCount, payloadLength
```

The private document has the same first six binding fields plus `snapshot`.
`snapshotHash` is the existing SHA-256 hash of governed tables and relationships.
The helper recomputes it before writing. `revision` is a new canonical UUID for each
configuration publication. The snapshot includes a `sourceBinding` of tenant,
workspace and dataset supplied by the owner preparation tool.

Each occupied chunk is:

```
<36-character-revision>|<three-digit-index>|<three-digit-count>|<payload>
```

- Header: **45** characters.
- Payload: at most **1,900** ASCII JSON characters (`ensure_ascii=True`).
- Occupied value: at most **1,945**, below the platform's 2,000 limit.
- Maximum assembled document: **243,200** characters in 128 slots, including
  escaped text and binding overhead. This is a deliberate v1 limit, not a claim
  that every semantic model fits. The helper rejects excess data; it never silently
  trims tables/columns to make them fit.
- All non-final occupied chunks must be full sized; unused slots must contain
  exactly `NOT_CONFIGURED`.
  Slot headers must agree with manifest revision, index and count.
- 1–256 tables; at most 2,048 columns/measures per table and 2,048 relationships,
  all further bounded by total document size. Names are at most 256 characters.
  Descriptions/format strings/guidance strings are at most 4,096.
  Table names cannot contain commas because the retained 1–4-table selector uses
  a comma separator.
- Metadata responses remain at most **64,000** characters, independent of total
  configuration size. A catalog that exceeds this fails with the retained
  metadata-response budget check; reduce/review the governed snapshot, not runtime
  safety limits. This boundary does not guarantee a very large catalog is usable.
- This helper currently supports **commercial-cloud Dataverse** and canonical bare
  lowercase GUID environment IDs. It rejects `Default-...` IDs and sovereign-cloud
  URLs rather than silently retargeting. Extend those explicitly in a future contract.

If a reviewed model does not fit, stop and report the size. Do not truncate away
inaccessible columns, suppress the full-reference probe, or add a backend as a shortcut.

## Runtime sequence and preserved guarantees

At the start of each metadata, query and advice tool:

1. Initialize output/provenance flags, then enter `configuration_validation`.
2. Read the manifest and fixed slot inventory from native `Env` variables. Reject
   absent, oversized, incomplete, mixed-revision, misordered, nonempty trailing,
   malformed or incorrectly bound configuration. Unused slots are accepted only
   as `NOT_CONFIGURED`, not arbitrary trailing data.
3. Validate document bindings and reviewed metadata shapes before forming any DAX.
   Check destination environment and source tenant/model against trusted system/config
   values. Configuration is not a tool input and is never a tool output.
4. Compare the **entire assembled document**, not merely a caller-provided hash or
   revision, with hidden `Global.LoadedConfiguration`. A change clears previous
   schema authorization and remembered metadata failures. Separate loaded-config
   and successful-probe state preserves the identical-failed-request guard.
5. Metadata invalidates its old authorization before every fresh probe, constructs
   the same escaped full-reference `EVALUATE ROW("AccessProbe", 1 + ...)` zero-row
   probe from the governed table/column lists, and calls Power BI as the end user.
   There is no configurable arbitrary probe query. Column `RowNumber-` handling,
   zero-column table references, escaping, probe output schema and decoder are the
   demonstrated contract.
6. Only after the existing `AccessProbe=1` validation succeeds are schema rows and
   catalog materialized for outputs. Authorization records the full configuration
   document, schema hash, current user and current turn. A query/advice tool with
   different configuration, user, turn or missing authorization rejects locally.

The compiler, expression/token/nesting checks, UTC date handling, DISTINCT projection,
sorting, 100-row / 16-alias / 256-text-cell bounds, retry ceiling, envelope validation,
and real-error handling are retained. Business result `firstTableRows` stays **Any**;
the dynamic array itself is serialized, preserving numeric precision. Business-query
`includeNulls=false` is unchanged. Advice compiles but never invokes the business
query connector; metadata grounding is still a separate zero-row probe.

`snapshotHash` is an owner-prepared description of content, **not** a signature or a
runtime live-model version check. Native Power Fx does not recompute SHA-256.
The helper verifies it, while runtime authorization uses exact document equality
and the caller probe. A malicious admin able to change the agent/configuration is
outside this boundary. Hidden variables prevent orchestrator use and external
initialization, not administrator access.

Errors use explicit `NOT_CONFIGURED` / `CONFIG_*` messages with
`connectorAttempted=false` and no disclosed snapshot. Unexpected errors in
configuration evaluation are sanitized before the existing error handler. The
prior native local/provider provenance distinction remains intact.

## Adopter setup (commands shown, not executed here)

1. Import the public unmanaged solution using the documented package procedure.
   If the importer displays the 129 configuration defaults, leave them as
   `NOT_CONFIGURED`; step 7 sets their current values in one batch after import.
2. Bind its existing Power BI connection reference to your approved connection.
   Keep user authentication and Invoker mode. Configure the supported agent
   reasoning model in Studio. No helper changes identities or permissions.
3. Copy `portable-target.example.json` **outside the repository** and replace every
   placeholder. Use the exact imported schema name/reference/prefix from the public
   package contract, and explicit destination tenant/environment/agent IDs and URL.
4. Use the existing owner-authorized `prepare-model.py` with reviewed private
   `resources.json` for the desired source workspace/dataset. This still requires
   the documented existing Fabric read+write rights to read model definition; it
   grants no rights. It now records `sourceBinding` but otherwise preserves its
   sanitized snapshot shape. Review the output, including descriptions and guidance.
   Older snapshots without this binding must be prepared again, not guessed.
5. Prepare the private configuration offline:

```powershell
python agent\configure_portable.py prepare `
  --snapshot agent\model-schema.private.json `
  --target-config C:\PrivateAnalytics\portable-target.json `
  --out C:\PrivateAnalytics\configuration-v1.private.json
```

This creates a new private file outside the repo, never overwrites an existing file,
and makes **no network calls**. It prints sizes, not metadata. `--revision` is
optional; by default a fresh UUID is generated. Don't use example metadata for a
real configuration.

6. Explicitly check the destination before writing:

```powershell
python agent\configure_portable.py check `
  --configuration C:\PrivateAnalytics\configuration-v1.private.json `
  --tenant-id <tenant-guid> --environment-id <destination-environment-guid> `
  --dataverse-url https://<destination-org>.crm.dynamics.com --agent-id <imported-agent-guid>
```

The explicit arguments must match the private package before any authentication
or network access. The helper:

- Uses existing Azure CLI authentication with explicit resource and tenant; never
  changes the active account, PAC profile, default environment, or auth configuration.
- Resolves the selected environment through the
  [Global Discovery Service](https://learn.microsoft.com/power-apps/developer/data-platform/discovery-service)
  and verifies tenant, environment ID, enabled state and exact Dataverse origin.
  Dataverse `WhoAmI` must agree with discovery's organization ID. HTTP redirects
  are refused, not followed with credentials.
- Checks exact imported agent schema and authentication/privacy settings, existing
  Power BI connection binding, all four runtime topic bodies and fifteen hidden
  native variable bodies, absence of unexpected active topics/variables, all 387
  topic-to-environment links, each imported Text definition with its explicit
  `NOT_CONFIGURED` default, and uniqueness of each current value. Missing/ambiguous
  values are not resolved by guesswork.

7. After privately reviewing the values, perform the separate configuration write:

```powershell
python agent\configure_portable.py apply `
  --configuration C:\PrivateAnalytics\configuration-v1.private.json `
  --tenant-id <tenant-guid> --environment-id <destination-environment-guid> `
  --dataverse-url https://<destination-org>.crm.dynamics.com --agent-id <imported-agent-guid>
```

`apply` writes only current `environmentvariablevalue` rows in **one transactional
Dataverse changeset**, using ETags for existing rows, then verifies readback.
No topic, GPT instruction, bot auth, connection reference or definition is changed.
No publish action is called. Quiesce concurrent imports/configuration edits during
the transaction, especially when first creating current value rows; duplicates
are detected and block verification. Never publish an unverified partial/conflicting set.

8. Explicitly **publish in Copilot Studio**, start a new conversation, and run the
   approved end-user tests. Updating current values alone leaves the prior published
   configuration active. Never claim a configuration update revoked old conversation
   metadata or changed an already published runtime.

Sources for value writes:
[Microsoft environment-value update/create example](https://learn.microsoft.com/dynamics365/finance/business-performance-analytics/uninstall-bpa#automatic-data-cleanup-version-28-and-later),
[Web API conditional updates](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/perform-conditional-operations-using-web-api),
[Web API batch changesets](https://learn.microsoft.com/power-apps/developer/data-platform/webapi/execute-batch-operations-using-web-api).

## Local verification and remaining release gates

```powershell
$env:PYTHONPATH = (Resolve-Path agent).Path
python -m unittest discover -s agent\tests -p 'test_*.py'
python agent\tests\run_portable_powerfx.py --library-directory <existing-PowerFx-DLL-directory>
```

The second command evaluates synthetic configuration/probe/catalog/provenance cases
in **Microsoft.PowerFx.RecalcEngine**, using already installed local DLLs. It does
not connect to an authoring service. The runner needs Core, Interpreter, Json and
Microsoft.Bcl.AsyncInterfaces assemblies. `RegEx`/JSON functions are enabled.

Tests compare retained node bodies, exact zero-row DAX and catalog semantics, local
guards, explicit destination mismatches, transactional value-only requests, privacy
bounds and malformed configuration. A separate baseline comparison verified all
four **legacy generated YAML bodies remain byte-identical** to the prior committed
generator for the same input.

Offline schema validation checks the generated topic/global/environment declaration
shapes. It does **not** prove native ZIP mapping, import, environment dependency links,
Studio publication, connector runtime permissions, or end-to-end user answers.
Those require the parent's explicitly approved sandbox import and subsequent
separately approved publication/Test-agent evaluation. None were performed by this
agent-side implementation. Do not use live LSP validation, a default authoring
session, or a cloud smoke test as an implicit substitute for that approval.

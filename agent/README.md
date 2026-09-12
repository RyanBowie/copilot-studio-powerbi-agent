# Metadata-grounded generated DAX in Copilot Studio

This publication copy contains generators, placeholder configuration, and synthetic offline
metadata, not live generated topics, credentials, or a preauthenticated solution export.
Use a private deployment copy. Keep this repository private and Pages disabled until the
[public-release review](../docs/public-release.md) is complete.

> **Example naming:** Agent365 is this demonstration's custom semantic model/report, **not the
> Microsoft Agent 365 product**. This clarification belongs in documentation, not runtime instructions.

This implementation replaces the earlier fixed-query/five-metric runtime. A standard Copilot Studio
orchestrator is configured to author **new DAX table expressions** from machine-readable model metadata. Native
Power Fx topics validate the expression boundary and build a bounded DAX execution envelope. The
standard Power BI connector runs it with **Invoker/end-user authentication**.

### Current release: caller-backed probe output-type correction, not an E2E claim

**The user's subsequent Studio catalog-only test still failed at
`schema_probe_output_validation`. The normalization change did not resolve that caller failure.**
Delayed transcripts became available for both the earlier and latest known Studio failures.
The earlier transcript's activity timestamps—not its later database creation time—place it
at 21:27–21:28 BST. That **actual caller trace** records `ProbeRows` as `[{"[AccessProbe]":1}]`, but
the following `ProbeJson` as `[{"Value":null}]`. The marker was discarded, not simply nested inside
a populated `Value` wrapper. The earlier synthetic wrapper tests did not establish this behavior.
The **21:53 BST caller trace now confirms the same loss after normalization**: `ProbeRows` still
contains the numeric marker, `connectorReturned=true`, but `ProbeJson` is `[null]` and
`probeResultStatus=missing_marker`. This establishes a local serialization/type problem, not a
missing response or observed provider denial. That execution predates the output-type correction;
its transcript was persisted later.

The native connector declares `firstTableRows` as `Table(Value:Any)`, which does not describe those
actual probe rows. The metadata probe now uses the documented action-local `dynamicOutputSchema`
to declare its fixed `[AccessProbe]` numeric column. This does not modify the shared connector,
change the full-column probe, remove schema references or accept an additional response shape.
The published native compiler also accepts a direct typed `[AccessProbe]` field check, and parsed
readback verifies the override. **The resulting current caller behavior still needs observation.**

The automation connection-manager card is a separate channel limitation, not a reason to tell the
already-connected Studio user to reconnect. No new automated conversations were attempted.

The metadata failure branch also appends a safe **D1 diagnostic JSON block**
to the existing deterministic error. The block reports the actual runtime result status, raw table
state/count, normalized array count, root/first-value kinds, known marker presence/type/conversion
result, known `Value` wrapper depth, unbracketed-marker indicators, response-container indicators and
an error-member-presence flag. It never returns raw rows/JSON, unknown column names, error contents,
identities or credentials. A separate `TypedMarkerIsOne` Boolean reports the direct typed field check.
The full query text, input/output binding paths, normalizer, acceptance predicate and private Invoker
authentication are unchanged; only the probe's output type is corrected. The generated-query action
and its runtime response handling remain unverified and unchanged in this narrow release.

Interpretation limits are explicit: `blank_or_unbound` cannot distinguish a missing output value
from a null typed table; `-1` means an unavailable count. Power Fx `IsBlank` includes null/empty text.
The `IsOne` flags reflect the existing `Value(...) = 1` conversion, not strict JSON numeric typing;
native tests expose the existing numeric-string/Boolean coercion without changing it.
An error-shaped member is not an established provider denial. Actual connector exceptions remain
on the existing separate OnError path.

**Single next observation:** refresh Studio and repeat the same catalog-only prompt once in its
existing authenticated test pane. Report whether metadata succeeds; if it still fails, copy only the
`Diagnostic: {..."version":"D1"...}` block and `TypedMarkerIsOne` flag from the final message.
No dataset selection, reconnection, permission change or business-data query is requested.
Native compile/readback validates the diagnostic expression and message binding; delivery of its
values in the user's Studio conversation still requires that observation.

### Previous change: native connector row normalization

The live connector schema declares `firstTableRows` as a single-column Power Fx table:
`Value: Any`. Ordinary `JSON(...)` therefore produced the synthetic equivalent of
`[{"Value":{"[AccessProbe]":1}}]`, while our decoder expected `[{"[AccessProbe]":1}]`.
Native Microsoft Power Fx execution reproduces the resulting false visibility rejection.
Both metadata-probe and generated-query results now use the documented
`JSON(..., JSONFormat.FlattenValueTables)` option. No columns were removed from the probe,
no permission check was bypassed, and connector targets/authentication are unchanged.

Metadata advances to `schema_probe_output_validation` only after the connector returns.
`connectorReturned` and `probeResultStatus` distinguish that boundary from the connector node
and identify missing output, unexpected row counts, missing markers and unexpected markers.
Exactly one usable `AccessProbe=1` row is still required before disclosing any prepared metadata.
An invalid response sends a deterministic output-contract error and cancels the current dialog
stack; it does not ask users to change datasets or grant Read/Build/RLS/OLS permissions.

**Previous verification boundary:** native compilation/publication and parsed readback passed. The unchanged
full-reference zero-row probe returns its expected constant through separate direct authorized REST
testing; that is not chat/Invoker proof. A separate metadata-only evaluation reached the connector
boundary but returned the platform's connection-manager card. The user's later Studio test returned
and failed the probe validator instead. Neither result establishes a Power BI permission denial.
No successful requesting-user metadata result or cloud-generated query/answer has been observed.

### Earlier repair: blank fixed-model alias

The observed “Only the onboarded primary model is available…” error came from local input
validation **before** the schema-visibility connector node. It was not a Power BI authorization
failure. The fixed alias had been declared as a `ManualTaskInput`, but the observed topic input
was blank. Metadata, generated-query and advice topics now use a supported non-prompting
`AutomaticTaskInput` with `defaultValue: primary`, plus explicit native initialization
`Coalesce(Topic.modelAlias, "primary")`. Nonempty invalid aliases are preserved and rejected;
connector workspace/model IDs remain fixed trusted configuration.

Outputs now identify `stage`, `connectorAttempted`, `visibilityVerified` and `resolvedModelAlias`.
A connector attempt is not proof that Power BI received or authorized a request. Identical failed
metadata requests in the same user message are stopped using `CancelAllDialogs`; an eight-attempt
message budget also bounds metadata calls while permitting catalog-plus-table retrieval.
These guards are native-compiled; cancellation has not yet been observed in chat.

Native authoring readback confirms the new input/default, fallback, provenance outputs and terminal
actions. An earlier evaluation returned the previous error/output contract three times and fallback;
its revision discrepancy was not explained. The subsequent metadata-only evaluation now resolves a
blank alias to `primary`, passes the local guard and reaches the connection-manager boundary.
That is observed alias-routing progress, not a completed metadata or usage/creator/date answer.

**Deployment is not a chat-success claim.** Unit and direct Power BI checks pass. The corrected SDK
client now forwards custom prompts to the published endpoint, but its conversation-start request
returns **403 Forbidden: “The caller is not authorized to perform the request.”** The existing token
has `CopilotStudio.Copilots.Test`, not `CopilotStudio.Copilots.Invoke`; no conversation or prompt turn
was created. This is a published-client authorization blocker, not a demonstrated Power BI
connection failure. No additional permissions were requested.

The earlier evaluation fallback had a concrete serialization cause: the native Studio parser
dropped the generic topics' triggers/actions despite their presence in stored YAML. Following repair,
fresh evaluation traces selected `ModelMetadata` and generated its input arguments. This is actual
planner evidence, not a completed metadata authorization or query result. Fully non-prompting
metadata attempt reached the client's 120-second timeout without returned activities. An extended
attempt, with a 300-second client budget and an explicit catalog request, returned **HTTP 504**
(`UnexpectedError`, “An unexpected error occurred.”). Neither failure establishes an
authentication failure or proves that the connector was reached.
Those timeouts are historical; the latest user-observed boundary is the unresolved probe validation
failure described above. No cloud-generated DAX/tool-argument/result conversation has been verified.

### Model-selection and parser correction

The real UI showed GPT-4.1 while raw Dataverse YAML retained `PreviewModels/GPT5Reasoning`.
The same authenticated authoring component API used by Studio returned **no parsed `aISettings`**;
the UI therefore resolved the catalog's default GPT-4.1. Preserving the raw YAML was insufficient.
The live model catalog includes GPT-5 Reasoning. After repairing YAML serialization, native
authoring readback returns `PreviewModels/GPT5Reasoning` both before and after successful publication.
This verifies the selector's backend, not model-execution telemetry or an independently observed
rendered dropdown.

`studio_yaml.py` uses indented sequences and literal multiline strings. `studio_authoring.py`
checks parsed model settings, exact instruction text, starters, topic triggers, input counts and
action counts; deployment now performs those checks before and after publication. Native compilation
also exposed and resolved unsupported `System.Activity.Id`, regex escaping, deprecated table
projection and duplicate action IDs. The shared guard now uses documented `System.LastMessage.Id`.
The screenshot's single **Agent Status** warning text has not been independently retrieved;
successful publication is not evidence that this separate warning disappeared.

## Actual runtime

```text
User question
    → standard generative orchestrator
    → Get model metadata: requesting-user schema visibility probe, then governed snapshot
    → orchestrator authors DAX table expression + output aliases + ordering + optional date expressions
    → Run generated DAX: structural checks, attempt budget, generic execution envelope
    → Power BI ExecuteDatasetQuery, fixed model/workspace, Invoker
    → validate owned Summary row, returned count, bounds and response size
    → explain actual results, or report the actual failure
```

**Compile DAX advice** uses the same expression/envelope checks without executing the proposed
business query. Metadata authorization still uses a zero-row Power BI probe. Advice is labelled
UNEXECUTED; syntax/semantic correctness is not established by contract validation alone.

**Generated query error** is a native OnError topic. It exposes bounded actual error information,
does not claim results, and distinguishes access failures from model absence. Instructions allow
one corrective attempt; a runtime counter limits execution to two attempts per user activity.
If platform error handling terminates the turn, no automatic retry is claimed.

The three obsolete fixed connector tools (smoke, governance counts and top-100) were **deleted**,
not merely disabled. They are absent from both Dataverse and the native authoring inventory. A
private backup and IDs were retained; unchanged content, no references, platform deletion dependencies,
child records and other-agent associations were checked first. The shared connection was not deleted.
The three other legacy bounded topics remain inactive. Current generic capabilities appear under
**Topics**, not as the old connector rows under **Tools**. Private historical source is under
`legacy\`; the original top-100 DAX is an offline regression fixture, not a runtime dependency.

Technical inputs do not prompt users to supply DAX, aliases or optional metadata/date parameters.
They are optional at the platform-input boundary because required inputs must enable prompting;
native runtime checks still reject missing expressions/aliases and invalid contracts before execution.
Observed planner binding events establish that non-prompting inputs can still be AI-filled.

## What is genuinely generated

The runtime contains **no metric, grouping, filter-field or owner-field enumeration**. The LLM can
author expressions using actual fields/measures and arbitrary supported DAX combinations, including
`VAR/RETURN`, `FILTER`, `CALCULATETABLE`, `SUMMARIZECOLUMNS`, `ADDCOLUMNS`, `SELECTCOLUMNS`, `UNION`,
relationship operations and derived calculations.

The input contract is a **table expression**, not an arbitrary full `EVALUATE/DEFINE/ORDER BY`
script. The expression is inserted as a validated expression operand in a standard DAX envelope;
the system does not truncate or attempt to repair arbitrary full-query syntax.

Projection and sorting are free output aliases, not business-query templates. Results are DISTINCT
by the declared projection. Include an actual key if record identity/multiplicity matters.
An explanation or proposed measure formula can be supplied as unexecuted advice; no measure is
created or saved in the model.

## Metadata acquisition and permissions

Only the **original model, alias `primary`**, is currently onboarded: its prepared definition contains
21 tables, 244 columns, 166 measure names and 13 relationships. The separately tested second model is
**not** a runtime option. Do not describe this release as multi-model routing.

`prepare-model.py` uses the documented Fabric semantic-model `getDefinition?format=TMSL` read
operation and its asynchronous operation endpoint. This API requires existing model read+write
permissions. It is a **governed owner preparation/refresh operation**, not a requirement imposed on
agent users; this implementation grants no permissions.

Only table/column names, types, descriptions, measure names/format strings and relationships are
retained. Raw definitions, partitions, source expressions/queries, connection material and roles
are not persisted or returned. Exact measure expressions are deliberately not published by this
preparation path, so name discovery is not an explanation of an existing measure's implementation.
Model-authored instructions and verified answers remain unverified. Linguistic-metadata presence
is detected, not treated as executable guidance.

Before any snapshot is returned, a native Invoker query references every prepared analytical column
inside zero-row expressions and returns only `AccessProbe=1`. A missing/inaccessible column causes
the probe to fail, and the snapshot is not disclosed. Narrower OLS users may therefore require a
role-appropriate governed snapshot; automatic per-role schema discovery is **not implemented**.
The subsequent business query is independently authorized by Power BI.

Snapshots have a preparation timestamp and a content fingerprint, not a claimed live model-version
guarantee. Refresh and republish after model changes. Missing snapshot content, changed schema,
authorization errors and genuine absence must not be conflated. No invented owner/creator exclusion
is imposed; access follows the actual model and requesting-user permissions.

## Enforced boundaries and honest limitations

| Boundary | Enforcement |
|---|---|
| Model/workspace | Fixed trusted configuration; only `primary`; no AI-supplied IDs |
| Authentication | Integrated private agent, existing connection reference, Invoker, blank impersonation |
| Read-only | Power BI ExecuteDatasetQuery; no model-management/write action |
| Expression boundary | Lexer strips quoted literals/identifiers/comments for structural checks; balanced delimiters; reserved envelope names and full-query/introspection/external-model commands rejected |
| Input resources | 12,000 expression characters, 4,000 code characters, nesting bounds; 1–16 output aliases |
| Result resources | 1–100 rows; deterministic complete-key ordering; extra ties fail closed; 256 characters per text cell with explicit truncation flag |
| Response | Required Summary/status/count envelope; 64,000-character preview budget; excessive responses rejected, not silently dropped |
| Attempts | Maximum two execution attempts per user activity |
| Time | Connector request timeout 30 seconds; not a guarantee that server computation is cancelled |

The lexer is **not a complete DAX parser, semantic validator or cost estimator**. Power BI remains
the parser and authorization boundary. Complex valid DAX can still be costly or wrong; capacity
governance remains necessary.

The native connector exposes `firstTableRows`, not the full raw REST error envelope. Native errors
go through OnError; the owned Summary/count/budget checks reject missing/partial results. The direct
verification transport additionally checks errors inside HTTP 200 responses. These mechanisms
must not be described as access to raw connector error details that the connector does not expose.

The envelope preserves numeric/date/Boolean values and caps text cells. Always disclose `__hasMore`
and `__textTruncated`. A successful zero-row envelope means no matching returned rows in that scope,
not no activity outside it or a complete telemetry history.

## Dates

The executor captures `UTCNOW()` and defines trusted `UTC_TODAY`. The LLM can generate paired
date expressions for varied periods: days, weeks, complete months, quarters, years or explicit dates.
Examples of scalar expressions include `UTC_TODAY-89`, `EOMONTH(UTC_TODAY,-2)+1` and
`DATE(YEAR(UTC_TODAY),1,1)`. These are language primitives, not finite business-query mappings.

Date-scoped requests must supply both expressions and use `QUERY_START` and `QUERY_END` in the table
expression. Common date-bearing prompts without resolved bounds are rejected rather than run
against all history. This is a reference/intent guard, not proof that arbitrary DAX filters express
the user's meaning correctly.

The Summary reports the engine UTC anchor and evaluated requested dates. State the chosen calendar
interpretation. UTC anchoring does not establish the source-event timezone. Observed first/last
events are not refresh timestamps or proof of continuous coverage. Never widen an empty/error period.

## Validation

The current unit suite covers unrestricted expression combinations, ownership-field references,
lexer/envelope escapes, aliases/sorting/bounds, relative date expressions, shared native-template
generation, metadata authorization gating and advice without business-query execution. Additional
tests cover Studio-compatible YAML, native-readback rejection of dropped model/topic fields,
obsolete-tool deletion guards, blank/invalid alias input gates, error provenance, retry termination
contracts, safe diagnostic output and client diagnostics: **43 Python tests and 5 Node tests**. The scalar input-gate
regressions execute a small offline evaluator over the generated expressions, not the native
Power Fx runtime; native compilation/readback and actual chat observations are reported separately.

An additional **40 synthetic native Microsoft Power Fx checks** cover the original 20 parser checks,
17 safe diagnostic cases and three fixed-probe typed-output cases. They reproduce the original Value-wrapper
defect and exercise the exact generated marker, diagnostic and query-envelope expressions. Missing/duplicate/
invalid markers and malformed envelope counts remain fail-closed. The installed JSON assembly throws
for its own `ParseJSON(null)` representation: that specific exception is recorded explicitly, and
the null-marker decoder is tested separately. This does not establish Studio's actual null-value
representation or a completed connector invocation.

To repeat those synthetic checks, use .NET 10 and existing Microsoft Power Fx Core, Interpreter and
Json assemblies, their dependencies (including `Microsoft.Bcl.AsyncInterfaces`) and `en-US` resource
satellites. Supply dependencies before building; clean/rebuild if resolving a missing assembly.
No runtime binaries are included here:

```powershell
python -c "import json,sys;from pathlib import Path;sys.path.insert(0,'tests');from test_probe_contract import native_cases;from test_probe_diagnostics import native_diagnostic_cases;Path('native-cases.private.json').write_text(json.dumps(native_cases()+native_diagnostic_cases()),encoding='utf-8')"
dotnet run --project tests\powerfx-contract\PowerFxContract.csproj -p:PowerFxLibraryDirectory="<existing-local-library-directory>" -- native-cases.private.json native-results.private.json
```

Direct authorized checks cover:

- multiple groupings plus multiple filters, with an independent aggregate cross-check;
- a derived tool-intensity ratio;
- owner/creator fields as aggregate counts, without printing identities;
- the familiar top-100 query, matching the original membership and ordering;
- explicit-date rankings and relative complete-month comparisons;
- another model table outside the old compiler's contract;
- successful empty envelopes and genuine unsupported-column errors.

These are **LLM-authored test fixtures applied to the generic contract**, not evidence of cloud chat
generation. Runtime code does not contain these business queries. Metadata-topic selection and
AI-filled metadata arguments have now been observed. Actual generated-DAX execution and user-facing
analytical answers still need verification in an authenticated Studio session.
Do not publish business rows, identity values, raw schema snapshots or fabricated screenshots.

The SDK test harness previously ignored `--prompt` outside `--maker-test` and always sent a retired
smoke-test request. That defect is fixed. Five isolated client-harness tests verify prompt forwarding
on both routes, the published target, fresh-conversation behavior, body-free diagnostics, and that a
conversation-start failure is not reported as a sent prompt or successful chat.

## Owner workflow

1. Configure your existing private agent and authorized model in `resources.json`; use the example
   file supplied with the publication bundle. No credentials belong in that file.
2. Install dependencies: `pip install -r requirements.txt` and `npm ci`.
3. Inspect/capture live state with `python deploy.py --capture`.
4. Run `python prepare-model.py` using an already-authorized model owner. Review the private snapshot.
5. Run `python general_runtime.py`, then `npm test`.
6. Apply reviewed source with `python deploy.py --apply --publish`. It refuses concurrent cloud edits,
   retains current cloud settings/auth, verifies the native model-selector and topic contracts,
   and never deploys stale `settings.mcs.yml`. A stored-YAML comparison alone is not sufficient.
7. Run `python verify-generated.py` for authorized direct checks.
8. Start a **fresh** Studio test conversation and inspect the activity plan, actual generated inputs,
   authorization, Summary flags and explanation. Existing sessions may retain an old dialog stack.

`node test-agent.cjs --prompt "What tables and measures are in this model?" --save-evidence` uses
the SDK's published SSE endpoint. `--maker-test` explicitly selects the separate evaluation JSON
endpoint. Both forward the same prompt; the default is metadata, not the retired smoke query.
Diagnostics report HTTP statuses, routes and activity types without headers, business rows or raw
generated expressions. `runtime-probe.private.json` is body-free private evidence, not a transcript
or a publication artifact. Structured component/DAX hashes are hints, not automatic execution proof.

The evaluation channel is not proof that the normal Studio/published channel works.
`test-studio.cjs` uses a separate project-local Edge profile, never
the shared MCP browser. It does not enter credentials or fabricate UI.

Private generated topics and metadata stay under `.generated-private\` and `*.private.json`.
The sanitized publication package contains generators and synthetic metadata for offline tests,
not live generated metadata topics. Reuse with another compatible semantic model requires owner
preparation, configuration, permissions and validation; it is not automatic support for any model.

## Documentation and sources

- [Copilot Studio topic inputs/outputs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-managing-topic-inputs-outputs)
- [System variables, including LastMessage.Id](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-variables-about#system-variables)
- [Primary model selection and default behavior](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-select-agent-model)
- [Power BI connector](https://learn.microsoft.com/en-us/connectors/powerbi/#run-a-query-against-a-dataset)
- [Power Fx JSON and FlattenValueTables](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-json)
- [Power Fx ColumnNames and Column for dynamic records](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-columnnames-column)
- [Execute Queries REST contract](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries)
- [Fabric model definition API and permission requirement](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/get-semantic-model-definition)

No hosted backend, new connection, app registration, secret, Fabric data agent or permission grant
was created. Normal Copilot Studio and Power BI usage/capacity charges still apply.

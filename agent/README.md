# Metadata-grounded generated DAX in Copilot Studio

This sanitized source includes [four complete synthetic native topic definitions](example-topics/README.md).
For the newer parent-run channel observations and actual screenshots, see
[M365 testing](../docs/m365-testing.md). The separately import-verified
[unmanaged starter solution](../docs/solution-import.md) intentionally contains onboarding stops,
not the demonstration's private metadata or connection bindings.

> **Example naming:** Agent365 is this demonstration's custom semantic model/report, **not the
> Microsoft Agent 365 product**. This clarification belongs in documentation, not runtime instructions.

This implementation replaces the earlier fixed-query/five-metric runtime. A standard Copilot Studio
orchestrator is configured to author **new DAX table expressions** from machine-readable model metadata. Native
Power Fx topics validate the expression boundary and build a bounded DAX execution envelope. The
standard Power BI connector runs it with **Invoker/end-user authentication**.

### Current status: user-observed scoped success

The user has observed **metadata retrieval, a dated usage ranking and a contextual creator/owner
follow-up** working in Studio. The follow-up retained the date window and usage ordering.
Displayed values have not been independently matched, and the original combined one-turn,
two-scope request remains unverified. This is scoped success, not universal semantic correctness.

The user has also published the agent to M365 Copilot. M365 UI tests and screenshots are separate
from this source/label audit; no channel permissions or sharing settings are changed here.
No additional user test is requested by this documentation update.

### Current generic dynamic-result implementation

Metadata success is now established by the user's Studio result and matching caller traces.
The subsequent ranking question reached **two actual executions**. Each returned **one successful
Summary plus 25 Data rows**; the local `ResultJson` then contained **26 null entries**. The recorded
Summary had `status=ok`, the matching returned count and no text/more-row truncation flags. This is
confirmed local type-projection loss—not evidence of an invalid DAX query or provider denial.
Execution timestamps precede the later transcript storage timestamps.

`ExecuteDatasetQuery` now has an action-local `firstTableRows: Any` output schema. The native topic
counts `Table(Topic.RawRows)` but serializes the **dynamic array itself**, never a declared
`Table(Value:Any)` projection. Arbitrary generated aliases and original numbers, Booleans, strings,
empty strings and ISO date strings survive. `serializerSettings.includeNulls=false` is explicit:
missing declared aliases represent DAX BLANK/null, not missing model fields. This agrees with the
connector's documented default and avoids serializing dynamic null fields in affected Power Fx
versions. The full metadata gate is unchanged.

**TOJSON was evaluated and rejected.** Despite explicit row limits and successful type/ordering
checks, direct synthetic and actual-model comparisons exposed numeric truncation to four decimal
places (for example, synthetic `1/7` became `0.1428`). It is absent from the final generated DAX.
The original DISTINCT, projection, TOPN, complete-key ordering, date expressions, tie checks and
text limits are unchanged. No business-query mapping or per-question tool was added.

Missing/unreadable rowsets, malformed markers and invalid count/status/flag contracts now stop
locally using `CancelAllDialogs`. They do not suggest provider permissions or another DAX retry.
Actual execution errors retain at most one correction; a response-budget rejection alone may use
one smaller preview within the existing two-attempt ceiling. No credentials, grants, privacy
settings, shared connector definition or hosted resources were changed.

**Verification:** native compilation/publication/readback pass, including the dynamic type and null
policy. Full-precision fractional/tiny/large values and an integer above 2^53 pass native checks.
Separate authorized direct-model checks pass for multiple filters/groupings, derived calculations,
owner/creator aggregates, dates, empty results, genuine unsupported-column errors and the original
top-100 membership/order. These are not proof of the final caller-visible answer.

The scoped Studio successes above are now user-observed. They do not establish universal correctness
or reverify the combined one-turn/two-scope question. No new conversations or channel tests are part
of this source/label audit.

## Inspect the complete source and current capabilities

| Artifact | What it contains |
|---|---|
| `agent.mcs.yml` | Full behavioral instructions, capability settings, conversation starters and model configuration |
| `general_runtime.py` | Complete native topic builders and runtime Power Fx guards |
| `generated_dax.py` | General expression validation and bounded DAX envelope |
| `query_transport.py` | Dynamic result schema and decoder contracts |
| `example-topics\ModelMetadata.mcs.yml` | Complete synthetic **Get model metadata** topic |
| `example-topics\GeneratedDaxQuery.mcs.yml` | Complete synthetic **Run generated DAX** topic |
| `example-topics\GeneratedDaxAdvice.mcs.yml` | Complete synthetic **Compile DAX advice** topic |
| `example-topics\GeneratedQueryError.mcs.yml` | Complete synthetic **Generated query error** handler |
| `example-topics\index.json` | Input/output schemas, triggers, connector operations and file index |
| `example-topics\README.md` | Reference-only safety notes and regeneration/configuration steps |

The reference YAML is generated from **built-in synthetic metadata and placeholder configuration**.
It is not a deployed snapshot and contains no live model schema or resource identifiers.
Run `python example_topics.py` to regenerate it locally; this never reads private configuration or
metadata and makes no network calls. Real deployments use the separate owner workflow below.
All four complete examples were checked against the pinned Microsoft authoring schema as well as
round-tripped against their current builders. This is structural validation, not a deployment test
against the placeholder model.

### Studio labels and screenshot targets

Open the agent's **Topics** page for **Get model metadata**, **Run generated DAX**, **Compile DAX
advice**, and the automatic **Generated query error** handler. The first three are generatively
selectable; the last runs on errors. Do not expect these replacements to appear as the old connector
cards on **Tools**.

The three obsolete fixed tools are deleted. **Model analytics**, **Model DAX advice**, and **Model
question clarification** are inactive legacy topics, not current query capabilities.
The remaining “Top 100 agents” label was a **conversation starter**, not an active tool. Its title is
now **Analyze agent usage**, with the prompt “Review the semantic model and provide the top 20 used
agents and their creators.” The original top-100 examples and offline ordering regression remain.
The current generic capability names, schema identities and behavior are unchanged.
The starter can be seen under the Overview's starter/suggested-prompt configuration.
Publishing a label update does not independently prove that an installed M365 app has refreshed;
its presentation should be recorded separately by the channel owner.

### Earlier metadata output-type correction

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
readback verifies the override. Subsequent Studio metadata success is now observed.

The automation connection-manager card is a separate channel limitation, not a reason to tell the
already-connected Studio user to reconnect. No new automated conversations were attempted.

The metadata failure branch also appends a safe **D1 diagnostic JSON block**
to the existing deterministic error. The block reports the actual runtime result status, raw table
state/count, normalized array count, root/first-value kinds, known marker presence/type/conversion
result, known `Value` wrapper depth, unbracketed-marker indicators, response-container indicators and
an error-member-presence flag. It never returns raw rows/JSON, unknown column names, error contents,
identities or credentials. A separate `TypedMarkerIsOne` Boolean reports the direct typed field check.
That metadata correction left its full query text, binding paths, normalizer, acceptance predicate
and private Invoker authentication unchanged. The later generic-query correction is described above.

Interpretation limits are explicit: `blank_or_unbound` cannot distinguish a missing output value
from a null typed table; `-1` means an unavailable count. Power Fx `IsBlank` includes null/empty text.
The `IsOne` flags reflect the existing `Value(...) = 1` conversion, not strict JSON numeric typing;
native tests expose the existing numeric-string/Boolean coercion without changing it.
An error-shaped member is not an established provider denial. Actual connector exceptions remain
on the existing separate OnError path.

Metadata D1 diagnostics remain available on failures; no extra metadata-only test is requested.
Dated ranking and contextual creator follow-up are now user-observed successes; the combined case
remains unverified.

### Previous change: native connector row normalization

The live connector schema declares `firstTableRows` as a single-column Power Fx table:
`Value: Any`. Ordinary `JSON(...)` therefore produced the synthetic equivalent of
`[{"Value":{"[AccessProbe]":1}}]`, while our decoder expected `[{"[AccessProbe]":1}]`.
Native Microsoft Power Fx execution reproduces the resulting false visibility rejection.
At that stage both paths used `JSON(..., JSONFormat.FlattenValueTables)`. The final generic-query
path instead serializes a dynamic `Any` array directly, as described above. No columns were removed from the probe,
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
At that earlier point no successful requesting-user metadata/query answer had been observed.
The later scoped successes at the top of this document supersede that historical boundary.

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
failure described above. Caller-generated queries returned successful envelopes before local
serialization loss. Later dated-ranking and contextual creator responses are user-observed successes,
without an independent value match or a universal correctness claim.

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
contracts, safe diagnostic output, synthetic-reference generation and client diagnostics:
**54 Python tests and 5 Node tests**. The scalar input-gate
regressions execute a small offline evaluator over the generated expressions, not the native
Power Fx runtime; native compilation/readback and actual chat observations are reported separately.

An additional **55 synthetic native Microsoft Power Fx checks** cover 15 probe/parser checks,
17 safe diagnostic cases, three fixed-probe typed-output cases and 20 current dynamic-query cases.
They reproduce the original Value-wrapper
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
python -c "import json,sys;from pathlib import Path;sys.path.insert(0,'tests');from test_probe_contract import native_cases;from test_probe_diagnostics import native_diagnostic_cases;from test_query_transport import native_transport_cases;Path('native-cases.private.json').write_text(json.dumps(native_cases()+native_diagnostic_cases()+native_transport_cases()),encoding='utf-8')"
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
AI-filled metadata arguments and caller-generated DAX execution are now observed in real traces.
The user has since observed a dated ranking and creator follow-up working. This does not reverify
the original combined two-scope question or independently validate every displayed value.
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

Authoring readback can require the specific audience reported by that service rather than the
runtime/evaluation audience. `AADSTS500131` at that boundary is an authoring-token audience mismatch,
not a Power BI model denial; do not change agent authentication or grant permissions to address it.

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
- [DAX TOJSON, evaluated but rejected for numeric fidelity](https://learn.microsoft.com/en-us/dax/tojson-function-dax)
- [Execute Queries REST contract](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries)
- [Fabric model definition API and permission requirement](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/get-semantic-model-definition)

No hosted backend, new connection, app registration, secret, Fabric data agent or permission grant
was created. Normal Copilot Studio and Power BI usage/capacity charges still apply.

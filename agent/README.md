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

### Latest repair: blank fixed-model alias

The observed "Only the onboarded primary model is available..." error came from local input
validation before the schema-visibility connector node, not a Power BI authorization failure.
Metadata, generated-query and advice topics now use non-prompting `AutomaticTaskInput` with
`defaultValue: primary`, plus native initialization `Coalesce(Topic.modelAlias, "primary")`.
Nonempty invalid aliases remain invalid; connector workspace/model IDs remain trusted configuration.

Outputs identify `stage`, `connectorAttempted`, `visibilityVerified` and `resolvedModelAlias`.
A connector attempt does not prove that Power BI received or authorized it. Identical failed
metadata requests within a user message stop via `CancelAllDialogs`; an eight-attempt message
budget permits catalog-plus-table retrieval. These guards are native-compiled, but cancellation
has not yet been observed in chat.

Native authoring readback confirms the repair after publication. However, a fresh evaluation
still returned the previous error and output contract three times, then fallback. The runtime/source
revision discrepancy remains unresolved; caching is only a hypothesis. Neither the blank-alias
runtime fix nor the requested dated usage/creator ranking is end-to-end verified.

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
No cloud-generated DAX/tool-argument/result conversation has been verified.

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
obsolete-tool deletion guards, alias input gates, error provenance, retry termination and safe client
diagnostics: **32 Python tests and 5 Node tests**. Scalar input-gate tests use a small offline
evaluator over generated expressions, not the native Power Fx runtime.

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
- [Execute Queries REST contract](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries)
- [Fabric model definition API and permission requirement](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/get-semantic-model-definition)

No hosted backend, new connection, app registration, secret, Fabric data agent or permission grant
was created. Normal Copilot Studio and Power BI usage/capacity charges still apply.

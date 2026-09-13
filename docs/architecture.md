# Metadata-grounded generated-DAX architecture

**The core workflow is user-observed working:** metadata retrieval, a dated usage ranking, and
a contextual creator/owner follow-up. This is not proof of universal query correctness or scaling.
See [verification](verification.md) for evidence levels, the unresolved combined request, and
historical preview/SDK blockers.

The example named `Agent365` is a custom Power BI model/report, not Microsoft Agent 365.
That distinction belongs in documentation, not runtime prompts.

## Message to answer

![Message flows through Copilot Studio and topics, then the Power BI tool Run a query against a dataset, to an explained answer.](assets/architecture-simple.svg)

Copilot Studio retrieves governed metadata, generates DAX, invokes the native query topic and
explains the returned rows. The diagram explicitly separates the **Power BI tool**:
**Run a query against a dataset** (`ExecuteDatasetQuery`). It is a connector action embedded in
the topics, not a separate deployment or a new tool for every question. It runs as the requesting user. Advice instead
returns proposed DAX without executing the business query; metadata authorization may still probe.

[Editable simple diagram](assets/architecture-simple.excalidraw) |
[Detailed diagram](assets/architecture.svg) |
[Actual topic and connector configuration](topic-and-tool-reference.md).

## What replaces the earlier query templates

The six fixed/bounded legacy components are retired from the active design. Native topic capabilities
now provide:

1. **Get model metadata**: authorize schema visibility as the caller, then return catalog or selected-table metadata from the prepared snapshot.
2. **Run generated DAX**: accept a generated table expression, output aliases/order, and optional date expressions; validate the boundary and execute a standard envelope.
3. **Compile DAX advice**: use the same contract without executing the proposed business query.
4. **Generated query error**: handle actual runtime failures without fabricated results or false model-absence claims.

These are topic-based capabilities, not the old three connector-tool cards. Appearance in the
portal's Tools section is not, by itself, evidence that topic discovery or chaining works.

There is no runtime list of five approved metrics or one permitted grouping/filter. The LLM is
expected to generate new expressions from metadata. The execution format is still a controlled
**table-expression contract**, not every possible full DAX script.

## Two separate identity paths

### Governed preparation

An already-authorized model owner runs `prepare-model.py` against the documented Fabric
`getDefinition?format=TMSL` read operation. This requires existing read/write model rights and the
appropriate delegated scope. No new rights are granted.

The preparation path retains table/column names, types, descriptions, measure names/format strings,
and relationships. It excludes raw definitions, source/partition queries, connection material,
roles, and exact measure expressions. A timestamp and content fingerprint describe the snapshot;
they are not a live model-version guarantee.

Only `primary` is currently onboarded: 21 tables, 244 columns, 166 measure names, 13 relationships.
The separately tested second model is not added to runtime routing.

### Requesting-user runtime

Before returning snapshot content, an Invoker Power BI query references the prepared analytical
columns inside zero-row expressions and returns only a visibility-probe result. An unavailable
column makes the probe fail; the snapshot is not disclosed.

This is deliberately fail-closed. A narrower OLS identity may need a role-appropriate governed
snapshot. Automatic per-role schema discovery is not implemented. The subsequent business query
is independently authorized by Power BI.

No maker-execution fallback, arbitrary model ID, user impersonation input, or anonymous endpoint
is exposed. No hosted backend or Fabric data agent was created.

## Query construction and execution

The orchestrator supplies a table expression and free output aliases, not a business-template ID.
Native Power Fx topics check structural boundaries and form a standard DAX envelope.

The expression contract supports combinations such as `VAR/RETURN`, `FILTER`,
`CALCULATETABLE`, `SUMMARIZECOLUMNS`, `ADDCOLUMNS`, `SELECTCOLUMNS`, and derived calculations.
The system does not try to splice or truncate an arbitrary full query script.

The envelope projects declared output fields, uses distinct projected rows and deterministic
ordering, and bounds returned data. Include a genuine key when record identity or multiplicity
matters; projection without a key can collapse otherwise distinct rows.

The lexer is **not a complete DAX parser, semantic checker, or cost estimator**. Power BI remains
the language parser and data authorization boundary. A well-formed expression can still implement
the wrong business meaning or consume excessive resources.

## Result/error contract

The metadata action declares its fixed numeric probe column. The business-query action instead
declares `firstTableRows:Any` and serializes that dynamic array directly, avoiding the field loss
observed with `Table(Value:Any)`. Generated aliases remain unrestricted by business mappings.
Explicit `includeNulls=false` omits DAX BLANK/null properties; absent declared output fields are
blank values, not evidence of missing model columns. Empty strings and original numeric values
are retained. A TOJSON alternative was rejected after observed fractional truncation.

Malformed local output contracts terminate without a DAX retry or provider-permission blame.
Actual execution errors may receive one correction; a smaller response preview remains bounded
by the same two-attempt ceiling. Dated ranking and contextual creator answers are user-observed;
the combined single-turn request remains outside the verified scope.

- Up to 100 rows and 16 declared columns.
- Up to 256 characters per text cell, with a truncation flag.
- Required Summary/status/count envelope and a 64,000-character preview budget.
- At most two execution attempts per user activity.
- A 30-second connector timeout, not a server-cancellation guarantee.

The native connector exposes `firstTableRows`, not the entire REST error envelope. Native failures
go through OnError; the owned Summary/count/budget checks reject missing or inconsistent output.
Direct verification scripts can additionally inspect raw REST errors, including errors in HTTP 200.

Missing data is not no activity. An unavailable schema field is not necessarily absent from the
model. A permission error must remain an access explanation.

## Dates and advice

The DAX envelope captures `UTCNOW()` and defines `UTC_TODAY`. The model generates scalar date
expressions and uses `QUERY_START`/`QUERY_END` in the business expression. This can represent days,
weeks, complete months, quarters, years, and explicit periods without adding a business-query template.

References and common date-intent guards prevent obvious unresolved date requests from becoming
all history. They do not prove that arbitrary generated filter logic faithfully implements the
user's intent. UTC anchoring does not establish the source-event timezone.

Advice uses the same compilation contract without executing the business query. Its metadata
visibility probe still touches Power BI. The proposed DAX is **unexecuted**, and no measure is saved.
Exact implementation explanations of existing measures are limited because exact measure
expressions are not in this prepared snapshot.

## Local source versus cloud runtime

Python modules prepare metadata, generate native topic source, deploy reviewed changes, and run
offline/direct checks. They are not a hosted service. Private generated topics and real snapshots
are excluded from GitHub; the publication package includes generators and synthetic metadata.

The editable [Excalidraw diagram](assets/architecture.excalidraw) and
[walkthrough](index.html#architecture) describe this design. Neither is evidence of successful chat
selection. Topic discovery, planner outputs, native Power Fx, consent/resumption, and final answers
must still be observed in a working channel.

# Capabilities, metadata, and scaling limits

**This is an experimental generated-DAX implementation, not a verified general conversational
analyst.** The source contract has moved beyond the retired five-metric compiler, but successful
cloud metadata retrieval -> generated expression -> execution -> final answer has not been observed.

The custom model/report called `Agent365` is not Microsoft Agent 365.

## Current versus retired design

| Area | Current generated-expression design | Retired bounded design |
|---|---|---|
| Business query vocabulary | Actual metadata fields/measures and generated DAX combinations | Five metrics, enumerated groupings and filters |
| Grounding | Owner-prepared machine-readable snapshot, gated at runtime | Hand-maintained approved subset in instructions/context |
| Multiple groupings/filters | Expressible in generated DAX | One grouping and one exact categorical filter |
| Derived calculations | Expressible without a new business template | Required extending mappings |
| Owner/creator fields | Actual metadata and requesting-user permissions | Blanket demo exclusion |
| Dates | Generated scalar expressions over a trusted UTC anchor | Paired dates or a fixed last-30-days resolver |
| Top-100 ranking | Generic-contract regression scenario | Specialized fixed tool |
| Chat proof | Not achieved | User reported successful original ranking; not proof of the new path |

Removing a finite list does not guarantee a correct answer to every question. Missing data, ambiguous
definitions, permission boundaries, language constraints, and incorrect generated logic still matter.

## Model metadata, not instructions for every question

The current primary snapshot contains 21 tables, 244 columns, 166 measure names, and 13 relationships.
The orchestrator is expected to retrieve the catalog and then relevant table context, rather than
receive a giant hard-coded business-query instruction list.

Preparation retains names, types, descriptions, measure format strings, and relationships. It does
not retain exact measure expressions, source queries, partitions, connection material, roles, or raw
definitions. A measure name alone does not establish its implementation or business meaning.

The snapshot has a preparation timestamp and content fingerprint. Schema changes require governed
refresh and republishing. Automatic drift recovery or a live model-version guarantee is not provided.
Model-authored instructions and verified answers remain unverified; arbitrary row text is not
agent instruction.

## Identity and schema visibility

`prepare-model.py` retrieves a documented Fabric model definition using an already-authorized owner.
This is a read operation that requires existing read/write model permissions. No permission is
granted by the implementation.

Runtime metadata retrieval first uses the caller's Power BI connection for a zero-row schema
visibility probe. If a referenced prepared column is unavailable, metadata is withheld.
Business-query execution is independently authorized by Power BI.

This fail-closed complete-snapshot check may reject a user who could query only a narrower OLS view.
A role-appropriate snapshot may be needed. Automatic per-role metadata discovery is not implemented.
Do not solve this by substituting a privileged maker connection.

The generic contract no longer invents an owner-field ban. That does not authorize publication of
private data, access beyond the model's permissions, or inference that inaccessible fields are absent.

## What "generate DAX" means here

The runtime accepts a **table expression**, output aliases/order, and optional paired scalar date
expressions. It constructs a standard execution envelope. This supports new combinations without
authoring a tool per question, but it is not an arbitrary full `EVALUATE/DEFINE/ORDER BY` script endpoint.

The lexer checks expression boundaries, delimiters, reserved names, and disallowed command forms.
It is not a complete parser, semantic validator, authorization engine, or query-cost estimator.
Power BI parses and authorizes the actual query.

Projection is distinct by the declared output fields. Include a real key if identity or multiplicity
matters. The system must disclose result/text truncation and cannot pretend a bounded result is the
entire model.

## Implemented resource controls

| Boundary | Current contract |
|---|---|
| Models | Trusted fixed workspace/model mapping; alias `primary` only |
| Expression size | 12,000 characters overall; 4,000 code characters after lexical handling |
| Output | 1-100 rows; 1-16 aliases/columns |
| Text cells | 256-character cap with an explicit truncation flag |
| Response preview | 64,000-character budget; excessive responses rejected |
| Attempts | At most two executions per user activity |
| Timeout | 30-second connector request timeout; no server-cancellation guarantee |
| Mutations | No Power BI model-management or data-write operation |

These controls do not prevent all expensive valid queries or establish production concurrency.
Per-activity guards must also be verified across consent/resumption and topic chaining.

## Advice and dates

Advice compiles the same proposed expression without executing the business query. Metadata
authorization may still perform a zero-row query. The answer must label suggested DAX unexecuted,
and must not claim to save a measure or know an unavailable measure expression.

Dates use the engine's `UTC_TODAY` and generated scalar bounds, with `QUERY_START`/`QUERY_END`
references in the query expression. UTC is the anchor convention, not proof of source-event timezone.
Reference checks do not prove that arbitrary filter logic matches the question. See [date semantics](date-filtering.md).

## Power BI limits are separate from our controls

The documented Execute Queries limits include:

- One query and one result table per call.
- 100,000 rows or 1,000,000 values, whichever comes first.
- 15 MB per query.
- 120 requests per minute per user.
- DAX-only execution, with documented INFO/DMV restrictions.

The connector reference additionally documents 100 calls per connection per 60 seconds.
The native connector exposes `firstTableRows`, not all raw REST error fields. Native errors,
Summary validation, and direct-test HTTP-envelope checks are different mechanisms.

These are platform constraints, not a model-count ceiling or measured agent throughput.

## Multiple models and scalable onboarding

Only `primary` is onboarded. A separate authorized second-model experiment demonstrated generic
constant execution and structural-definition retrieval: 78 tables, 694 columns, 17 measures, and
79 relationships, including hidden/generated objects. It did not onboard that model into this agent.

To extend the design, use an authorized model catalog, explicit routing, governed metadata refresh,
and per-model permissions. No new metric template should be needed merely because the model differs,
but the model's metadata, semantics, and accuracy still need validation.

Cross-model comparison requires separate queries and alignment of dates, units, grain, and definitions.
A single Execute Queries call does not arbitrarily join separate datasets.

## What remains unverified

- Cloud selection of the generated-query capability (metadata selection is observed).
- Actual cloud-authored expression and argument correctness.
- Successful full chat results and explanations.
- Role-specific metadata access and representative RLS/OLS behavior.
- Existing-measure implementation explanations and model-authored guidance retrieval.
- Automatic schema drift handling, multi-model routing, realistic load, and concurrency.

The published SDK returned 403 before its prompt was sent. After a serialization repair, evaluation
selects metadata and AI-fills arguments, but its latest attempt returned HTTP 504. The same repair
restored GPT-5 Reasoning in native selector readback; rendered-picker state, inference telemetry and
the original UI warning remain unverified. Do not collapse these into one Power BI authentication
diagnosis or call them a successful conversation.

## Suggested evaluation matrix

Measure schema coverage, manual preparation effort, model/topic routing, generated-query agreement
with known answers, latency by stage, permission behavior, and failure explanations separately.

Include a metadata-only question, new derived calculation, multiple filters/groupings, dates,
familiar ranking, advice-only request, unavailable field, permission failure, stale snapshot,
oversized result, and semantically ambiguous measure.

See [verification](verification.md) and [the second-model experiment](scalability-experiment.md).

## Microsoft references

- [Execute Queries](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries)
- [Power BI connector](https://learn.microsoft.com/en-us/connectors/powerbi/)
- [Fabric definition permissions and behavior](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/get-semantic-model-definition)
- [Copilot Studio topic inputs and outputs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-managing-topic-inputs-outputs)

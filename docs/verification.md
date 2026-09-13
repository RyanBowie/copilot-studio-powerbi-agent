# Verification: what was observed, and what was not

## Current status

**Published M365 UI testing completed three scenarios:** top-20 agents with creators,
same-period top-five follow-up, and explicitly unexecuted model-grounded DAX advice.
The ranking contained 20 distinct descending numeric usage values; the follow-up matched the prior
first five. Requested table/code-block formatting was not fully followed. These are visible-output
and consistency checks, not an independent model-value, DAX-semantic or no-execution audit.
See [exact prompts and genuine redacted captures](m365-testing.md).

**The core PoC workflow is now user-observed successful:** metadata retrieval, a dated usage
ranking, and a contextual creator/owner follow-up retaining the date window and usage order.
Matching post-correction traces and every displayed value have not been independently checked.
The original combined single-turn two-scope request remains unresolved; this is not universal
query correctness, a load benchmark, or a multi-model validation claim.

**Deferred correctness concern:** a subsequent ranking repeats the same display name, creator label
and usage value across its visible rows. The user correctly challenged this result. Until the
executed DAX, returned rows and independent per-agent counts are compared, neither the ranking's
accuracy nor a semantic-model defect is established. Investigation distinguishes lost DAX filter
context, duplicate source labels/grain, model relationships and final-answer duplication.
Earlier user-observed success confirms the response path, not numerical correctness for this case.
The user explicitly deferred this investigation. Later successful M365 samples do not resolve it.

The Studio model selector showed GPT-4.1 despite raw YAML retaining a reasoning-model hint.
Native Studio parsing had dropped `aISettings` and topic bodies. Corrected YAML serialization
restored parsed GPT-5 Reasoning settings and full topic contracts before and after publication.
The current rendered picker has now independently been observed as GPT-5 Reasoning (Preview).
Inference telemetry remains unverified. The current warning grid identifies preview-model suitability
and no formal Studio evaluation. These need not be the same as the previously unidentified warning.

## Current generic-contract evidence

| Check | Observation |
|---|---|
| Owner-prepared primary metadata | 21 tables, 244 columns, 166 measure names, 13 relationships |
| Offline expression, serialization, authoring, cleanup, alias, row-decoding, and diagnostic suite | 50 Python tests |
| Corrected client-harness suite | 5 tests |
| Synthetic native Microsoft Power Fx checks | 55; null-serialization caveat below |
| Varied direct expression cases | Eight passed against the primary model |
| Original ranking regression | Generic-contract result matched original top-100 membership/order directly |
| Deliberately invalid column | Actual direct Power BI error observed |
| Cloud-generated expression/tool arguments | Recorded in actual caller traces; raw DAX/arguments remain private |
| Metadata-topic selection and AI-filled metadata arguments | Observed after serialization repair |
| Successful metadata answer | User-observed catalog, corroborated by caller traces |
| Successful provider query envelopes | Two executions, each with one ok Summary and 25 Data rows |
| User-visible dated ranking | User confirmed success; explicit metric, UTC anchor, dates and descending usage order |
| Contextual creator/owner follow-up | User confirmed success; same date window and usage ordering |
| Original combined single-turn request | Still unresolved; not superseded by narrower successful cases |

Direct cases include multiple groupings/filters, a derived ratio, owner/creator aggregate counts,
the familiar ranking, explicit dates, complete-month comparisons, a table outside the old compiler,
and empty output. They are **LLM-authored test fixtures used by the test executor**, not evidence
that the cloud agent generated those expressions.

No business rows, identity values, or fabricated success screenshots are published.

## Three separate runtime observations

### Evaluation endpoint: fallback repaired, completion still unresolved

A metadata question originally returned:

> Sorry, I am not able to find a related topic. Can you rephrase and try again?

The native parser had omitted topic triggers/actions. After repair, traces selected `ModelMetadata`
and AI-filled its metadata arguments. Technical inputs were also made non-prompting, with runtime
validation retained. A subsequent attempt reached a 120-second client timeout; an extended request
with a 300-second budget returned HTTP 504 `UnexpectedError`. Metadata authorization, connector
completion, and cloud-generated DAX execution remain unverified. The timeout does not establish an
authentication failure or even that the connector was reached.

### Corrected published SDK client

The old SDK harness ignored custom prompts outside the maker-test branch and sent a retired
smoke-test request. That defect was fixed.

The corrected published SDK attempt then received **HTTP 403 Forbidden** at conversation start:
"The caller is not authorized to perform the request." Its token had `CopilotStudio.Copilots.Test`,
not `CopilotStudio.Copilots.Invoke`.

The metadata prompt was **not sent**, activities were empty, and no capability ran. This is a
published-client authorization blocker, not a demonstrated Power BI connector login failure.
No missing permission was requested or bypassed.

### Studio and UI state

An independent browser could not reliably reach the authoring view. User screenshots confirmed
publication and new instructions, but also showed GPT-4.1 and dimmed legacy tool entries.

The three obsolete connector tools were subsequently deleted after backup and dependency checks;
they are absent from both native authoring inventory and Dataverse. Three legacy bounded topics
remain inactive. Current generic capabilities appear under Topics, not the old Tools rows.

The parsed selector backend retains GPT-5 Reasoning after successful publication at 16:54:36 UTC
on 12 September 2026. Authentication, Invoker binding, and cross-geo/privacy settings were not
changed. The original warning text was not retrieved; publication does not prove it disappeared.
At that stage the rendered picker was not independently observed. The later M365 testing visit
confirmed its current GPT-5 Reasoning (Preview) selection and captured the two current warnings;
effective inference telemetry remains unverified.

### Subsequent user-observed metadata validation failure

A Studio request for a dated top-20 usage ranking with creator information repeatedly selected
the metadata catalog. The selected activity showed a blank `modelAlias`, blank `tableNames`,
and `view=catalog`. Blank table names are valid for the catalog; the configured primary alias
was expected to be supplied internally.

The final response quoted the local validation error:

> Only the onboarded primary model is available. Choose catalog or tables; no arbitrary model IDs.

That check runs before the schema-visibility connector action. The agent's accompanying claim
that the platform rejected the visibility probe was therefore incorrect for this rejection.
This is evidence of an input-validation failure, not a demonstrated Power BI permission failure.
It also shows that at least the quoted error reached the final response; blank fields in a selected
in-progress activity alone do not establish that every topic output is unbound.

The correction was published at 19:14:03 UTC on 12 September 2026. It adds a primary input default
and explicit runtime blank fallback across metadata/query/advice, preserves invalid-alias rejection,
exposes error-stage/connector-attempt outputs, and adds duplicate-failure cancellation plus an
eight-attempt metadata budget. Native compilation/readback passes; GPT-5 Reasoning, Invoker and
privacy settings are unchanged.

However, fresh evaluation still returned the old error/output contract three times, then fallback.
This does not establish execution of the repaired revision; the reason for that discrepancy is
unresolved. No connector progress, effective retry cancellation, or successful ranking was observed.
Passing offline scalar-gate tests is not native Power Fx execution evidence.

### Later Studio run reaches the visibility stage

A later user screenshot shows one metadata call completing in 5.10 seconds. Its final answer
reports `stage=schema_visibility_probe`, `connectorAttempted=true`, `visibilityVerified=false`,
and `status=rejected`. This is new evidence of the repaired diagnostic path being reached,
rather than the previous local-input error. The screenshot does not expose the connector's
actual returned rows or provider error, and does not establish successful metadata authorization.

The investigation separates connector/provider failure from output binding or response-shape
validation failure. The answer's generic recommendation to change permissions or choose a dataset
is not supported by these flags alone. No permissions, model routing, or execution identity are
changed on that basis. One completed topic is not a successful analytical answer or proof that
every retry guard works.

### Row-normalization defect repaired; latest conversation waits for connection verification

The native connector declares `firstTableRows` as `Table(Value:Any)`. Default JSON serialization
preserves a `Value` wrapper that the previous metadata and query decoders did not expect.
Synthetic native Microsoft Power Fx execution reproduces rejection of a valid wrapped probe.
This establishes a concrete decoder defect, but the exact pre-repair Studio caller response
was not captured.

Both normalizers now use `JSONFormat.FlattenValueTables`. Exactly one usable `AccessProbe=1`
is still required; invalid output produces an explicit output-contract failure and ends the
current dialog stack. The unchanged all-column probe separately returned the expected constant
through authorized direct REST. That is not proof of the requesting user's connector access.

The correction was compiled, published, and read back at 20:42:31 UTC on 12 September 2026.
Thirty-seven Python and five Node tests pass. Twenty synthetic native Power Fx checks reproduce
the wrapper defect and exercise marker/envelope handling. The installed JSON assembly throws
`NotSupportedException` for its own `ParseJSON(null)` representation; that case is recorded as
a limitation, not validation success. A separate null-marker decoder check does not establish
Studio's actual null serialization.

The latest fresh metadata-only evaluation resolves the blank alias to `primary`, passes local
validation, and reaches a platform connection-manager card requesting credential verification.
Its trace records `connectorAttempted=true`, `connectorReturned=false`,
`probeResultStatus=not_attempted`, and `visibilityVerified=false`. This is a waiting conversation,
not a completed rejected connector result. No provider denial or returned rows were observed.

Use an already connected Studio session, or verify the existing Invoker connection if the platform
requests it, before testing metadata again. This is not a recommendation to grant permissions,
change datasets, or substitute maker credentials. No generated business query was attempted
because metadata retrieval had not completed.

### Earlier user retest: the output-contract failure persisted

The user's subsequent catalog-only Studio request returned the new deterministic
`schema_probe_output_validation` failure message: the connector returned, but the validator did
not find exactly one usable `AccessProbe=1` row. Thus the normalization repair has not resolved
the actual caller's failure. This user session progressed beyond the separate automated client's
connection-manager boundary; it should not be diagnosed from that client's waiting state.

The screenshot does not reveal the row count, marker type, normalization result, or exact
`probeResultStatus`. Those actual runtime observations are needed to distinguish a missing
binding, empty response, unexpected structure, or marker failure. The complete visibility gate
remains in place and no metadata is claimed. Further changes must follow that evidence rather
than assume another synthetic fixture represents the caller's response.

## Actual caller trace: numeric marker lost during serialization

Delayed transcripts for the user's earlier and 21:53 BST Studio runs show one returned row with
numeric `AccessProbe=1`. Before normalization, local JSON became `[{"Value":null}]`; after
normalization it became `[null]`, with `probeResultStatus=missing_marker`. This is observed local
type/serialization loss, not a missing connector response or provider permission denial.
Transcript database creation time was later than execution time and must not be mistaken for
a post-correction test.

At 22:20:21 BST, the metadata connector action was republished with an action-local
`dynamicOutputSchema` declaring the actual fixed `[AccessProbe]` column as Number. The probe,
binding paths, normalization, acceptance predicate, Invoker identity, and other components are
unchanged. Safe D1 facts and a direct `TypedMarkerIsOne` check are retained in the failure message.

The user subsequently confirmed success at 22:55 BST: the Studio answer listed 21 tables,
166 measures, snapshot freshness, and relationship information. This establishes user-visible
metadata retrieval after the correction. No reconnect or permission change was required to explain
the earlier local marker loss. The raw model screenshot is not copied into this publication.

### Earlier business-query retest: generic result validation failed

The next user request asked for a top-20 usage ranking with creators and a top-five last-30-days
view. Its response reported schema grounding, a generated combined expression, an initial execution
and one corrective retry. The displayed executor diagnostics were `stage=query_result_validation`,
`connectorAttempted=true`, `connectorReturned=true`, `visibilityVerified=true`, and `status=rejected`,
with a missing/invalid-envelope error.

This is progress beyond the metadata blocker, not a successful ranked answer. The response's
narrative alone does not establish the exact generated DAX or provider result. Actual caller trace
inspection is needed to distinguish provider errors from the generic path's known dynamic-type
projection risk. No permission change or repeated user prompt is indicated by these flags.
This prompted the generic result-handling investigation described next.

### Actual query trace and final dynamic-output correction

Delayed caller traces for the business-query run establish both generated arguments and two
executions. Each returned one Summary with `status=ok` plus 25 Data rows, matching counts and
no more-row/text-truncation flags. Local `ResultJson` then contained 26 null entries. This confirms
local projection loss rather than a need to rewrite the DAX or change permissions.

The final correction was published at 22:59:48 UTC on 12 September 2026. The generic action
declares `firstTableRows:Any`, counts through `Table(dynamic)`, and serializes the dynamic array
itself. The original DAX builder, metadata gate, DISTINCT projection, ordering, tie/date/text
bounds and two-attempt ceiling are preserved. Explicit `includeNulls=false` omits DAX blank
fields; missing declared aliases mean blank values, not missing schema. Empty strings survive.
Malformed local result contracts cancel the turn rather than trigger a DAX rewrite or blame
provider permissions.

A TOJSON string-transport candidate was tested and briefly published, then removed: exact
comparisons exposed fractional truncation to four decimal places. It is absent from the final
runtime, and its results must not be used as evidence for the final correction. The dynamic
path passes native fractional/tiny/large numeric, integer-above-2^53, Boolean, ISO-date, Unicode,
empty-string and null-omission cases. Eight direct-model regressions pass, including original
top-100 membership/order and physical-versus-decoded cell comparisons.

No post-correction caller-visible ranking has yet been observed. At 00:20 BST on 13 September,
the user supplied another failure showing the same envelope-error and retry wording, and explicitly
confirmed that it was a new response after refreshing Studio and starting a new test session.
It must not be dismissed as an earlier answer still displayed in the pane.

The next investigation correlates that execution's timestamp, actual topic contract, returned shape
and normalized result with the published correction. Native authoring readback alone is insufficient
to establish what ran. No additional refresh/retry, permission change, dataset switch or speculative
type change is indicated before that reconciliation. Actual identity/business rows remain private.

## User-observed success after the final correction

At 00:26 BST on 13 September, the user confirmed a successful last-30-days usage ranking.
The answer defined usage as audit-log interaction counts, used UTC anchor 12 September,
stated the inclusive 14 August-12 September window, and displayed descending usage counts.
The screenshot is cropped, with 19 numbered entries visible in an answer described as top 20;
it does not establish every returned row or independently verify every number.

At 00:27 BST, the user asked "now get me their creator details" and confirmed success.
The answer resolved the reference to the previously ranked agents and retained the same
date window and usage ordering while adding creator/owner details. This demonstrates the
requested contextual follow-up behavior, not a field-specific fixed-query tool.

No names, emails, identifiers or business values are copied here. Matching post-publication
traces were not yet available during the bounded read-only check, so the prior combined-request
failure is not attributed to caching, an old session or unsupported creator fields. No live/source
changes, republishing, retests or further user requests followed these successful observations.

## Historical fixed-query evidence

The earlier fixed/bounded implementation passed its own 25-test suite and direct regressions.
The user reported liking its original top-100 answer. It also produced incorrect all-history
responses to date-scoped questions and incorrectly inferred model-wide field absence from tool scope.

That architecture has been replaced. Its test count is not the current suite, its successful fixed
query is not proof of generated query routing, and its screenshots are labeled historical.

The custom `Agent365` product-naming clarification remains in documentation only.

## Second model

The [separate experiment](scalability-experiment.md) proved a distinct second model could execute a
constant and expose structural metadata through an authorized Fabric definition request.
Read/write preparation permissions were already present. That model is not a runtime alias,
and no second-model conversational onboarding is claimed.

## What a passing end-to-end test must show

1. A fresh authenticated conversation using the intended current agent.
2. Actual metadata capability selection and successful visibility check.
3. Metadata returned to the orchestrator.
4. A newly authored DAX expression and actual argument values.
5. Execution through the expected Invoker connection and configured model.
6. Successful result-envelope validation.
7. A final answer faithful to the values, dates, units, and truncation flags.

Observe this for metadata, a new calculation, multiple groupings/filters, a relative period,
top-100 presentation, and advice-only behavior. Test representative restricted identities separately.

## Documentation checks

The site is locally rendered in light/dark desktop and narrow mobile layouts. Embedded images,
tab/keyboard behavior, overflow, and JavaScript errors are checked. Those are documentation tests,
not evidence of Copilot Studio runtime correctness.

# Verification: what was observed, and what was not

## Current status

**The broader generated-DAX runtime is deployed but not end-to-end verified.** No observed
conversation establishes metadata retrieval, cloud-authored DAX arguments, Power BI execution,
and an explained result as a complete chain.

The Studio model selector showed GPT-4.1 despite raw YAML retaining a reasoning-model hint.
Native Studio parsing had dropped `aISettings` and topic bodies. Corrected YAML serialization
restored parsed GPT-5 Reasoning settings and full topic contracts before and after publication.
This is selector-backend evidence, not an independently observed rendered picker or inference telemetry.

## Current generic-contract evidence

| Check | Observation |
|---|---|
| Owner-prepared primary metadata | 21 tables, 244 columns, 166 measure names, 13 relationships |
| Offline expression, serialization, authoring, cleanup, alias, and row-decoding suite | 37 Python tests |
| Corrected client-harness suite | 5 tests |
| Synthetic native Microsoft Power Fx checks | 20; null-serialization caveat below |
| Varied direct expression cases | Eight passed against the primary model |
| Original ranking regression | Generic-contract result matched original top-100 membership/order directly |
| Deliberately invalid column | Actual direct Power BI error observed |
| Cloud-generated expression/tool arguments | Not observed |
| Metadata-topic selection and AI-filled metadata arguments | Observed after serialization repair |
| Complete new-runtime chat answer | Not verified |

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
Fresh rendered-picker state and effective inference telemetry are not independently observed.

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

## Historical evidence is not current-runtime proof

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

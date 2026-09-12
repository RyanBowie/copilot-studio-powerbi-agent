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
| Offline expression, serialization, authoring, and cleanup suite | 25 Python tests |
| Corrected client-harness suite | 5 tests |
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

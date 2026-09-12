# Evidence and limitations

This page separates observations from illustrations and planned checks. It is not a security certification or production-readiness claim.

## Evidence categories

| Category | Meaning |
|---|---|
| Direct API/connector test | A query ran outside a full agent conversation. |
| Agent runtime test | A conversation actually invoked a tool and produced a result. |
| User observation | The user reported or showed behavior in the authoring interface. |
| Synthetic illustration | Deliberately invented demo names and numbers; not execution evidence. |

## Initial PoC evidence

- A constant-only DAX query executed successfully against the chosen model.
- Direct count and ranking queries succeeded.
- The top-100 query returned 100 rows using the model's audited Interactions metric.
- The user confirmed they liked the top-100 output.
- Early deployment defects were corrected: callable connector Tools replaced topic-only registration.
- A connected environment connection and per-agent approval were separate requirements.

## Screenshot provenance

The tool-list and connection-approval images are crops of an actual user-supplied Copilot Studio screenshot. They demonstrate registered tools and the end-user consent experience, respectively. They **do not** demonstrate completed query execution.

Any image captioned "synthetic" or "illustrative" is a documentation illustration, not a product screenshot or test transcript.

## Generalized enhancement

The same agent was updated and published with reusable analytics, DAX advice, and model clarification. The original top-100 tool and existing connection were preserved. The custom-`Agent365` naming distinction now belongs to the README/public documentation, not runtime instructions.

| Check | Recorded result |
|---|---|
| Offline validation of packaged sanitized source | **25 tests passed**, rerun from this repository's `agent` folder |
| Reusable analytics direct-query cases | **Seven passed** in the development model, as recorded by the implementation handoff |
| Original smoke/count/ranking regressions | Passed directly; original top-100 source preserved |
| Publication and private solution-export consistency | Confirmed by implementation handoff; private export deliberately not included |
| Automated full analytics conversation | **Not verified**: evaluation-channel connection approval remained a blocker |
| Live user-facing DAX-advice response | **Not verified** |
| Restricted-user/RLS scenarios | Not established by the current evidence |

Direct-query tests cover compiled DAX against the model, not every branch of the runtime Power Fx compiler. Full agent testing is still needed in an approved session/channel.

The source's [labeled examples](../agent/examples.json) retain the verified constant result, a sanitized connection-response description, a clearly unexecuted DAX illustration, and the user's top-100 observation. They do not contain business result rows.

The documentation site was checked in desktop light/dark themes and a narrow mobile viewport, with embedded-image, tab, keyboard-navigation, overflow, and JavaScript-error checks.

## Scope-explanation correction

Published and synchronized on 12 September 2026. Instructions, unsupported-input explanations, clarification behavior, and DAX-advice wording now distinguish:

- A capability exposed by the approved tools.
- A field excluded from or unknown to that partial contract.
- Absence established by authoritative metadata for a particular model/version and visibility.
- An actual permission failure.

Owner/creator details remain outside the demonstration's tools, without asserting that the underlying model lacks them. The correction did not add identity queries, another model, or new permissions.

The implementation handoff verified the user's selected cloud reasoning model and authentication/Invoker connection state before and after deployment; they were unchanged. Protected specialized queries and top-100 wording were preserved.

The 17 offline tests include explanation/guardrail assertions and generated-source parity; they are not live conversation evidence. Three fixed and seven reusable direct-query regressions passed. Previously blocked chat channels were not repeatedly retried, and no new full-chat pass is claimed.

## Date-routing correction and documentation-only naming note

Published and synchronized on 12 September 2026. The fixed ranking's broad description conflicted with the reusable date route, and relative dates had depended on supplied ISO strings rather than a deterministic resolver.

The corrected runtime routes dated/filtered rankings to ModelAnalytics, resolves `last30Days` using a captured UTC calendar clock, rejects unresolved/conflicting dates, and reports requested bounds separately from observed event bounds. The original fixed ranking DAX is unchanged.

The latest suite passes 25 tests in the packaged source. Three fixed, seven reusable, and five date-specific direct queries passed. These do not prove successful live topic selection or final-answer behavior.

The exact capability selected in the user's failed screenshot remains unproven. An attempted advice probe returned no activities, a conversation read returned 404, and the shared authenticated browser was unavailable. No new authentication-failure diagnosis or chat E2E success is inferred.

The user's selected cloud reasoning model and Invoker configuration were preserved. Product-disambiguation prose was removed from runtime instructions and the runtime grounding disclaimer field; actual schema and business definitions remain. The README/site retain the explanation.

See [date filtering](date-filtering.md) for supported inputs, calendar conventions, example boundaries, and evidence limits.

## Limits of the evidence

### Second approved model

A [separate read-only experiment](scalability-experiment.md) confirmed a genuinely different semantic model, three successful constant-query calls, and automatic structural-definition retrieval through Fabric `getDefinition`. The retrieved structure contained 78 tables, 694 columns, 17 measures, and 79 relationships including hidden/generated objects.

That metadata route required the tested identity's existing read/write permissions. It did not establish read-only-user metadata access, authored-guidance discovery, runtime model routing, compiler portability, realistic business-question correctness, or second-model agent E2E. The available MCP schema connection still failed with an artifact/access error, which must not be interpreted as model absence.

The observed PoC behavior does not establish accuracy for arbitrary DAX, arbitrary semantic models, every channel, or every identity. It does not establish that RLS has been tested across representative users.

The repository excludes raw conversation captures and tenant-bound verification files to avoid publishing sensitive details. Keep private operational evidence in the deployment environment.

The latest enhancement's scope is finite and model-specific; do not infer arbitrary schema support solely from the example prompts.

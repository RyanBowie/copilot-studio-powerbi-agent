# Architecture

## Model-independent pattern, model-specific example

The example's `Agent365` name belongs to a custom semantic model/report. It does not refer to the Microsoft Agent 365 product. This is a Power BI integration pattern, not a product-specific Agent 365 integration.

The same architecture can target other compatible semantic models. The example's table names, metrics, relationships, and DAX are not universal; adaptation and validation are required.

See [capabilities and limits](capabilities-and-limits.md) for how schema discovery differs from query execution, what model-authored guidance can provide, and the proposed model-catalog architecture. That multi-model architecture is **not implemented** in the current agent.

## The reusable pattern

1. An authenticated user asks a business question.
2. The standard Copilot Studio orchestrator interprets it using the model contract.
3. The agent either selects a supported analytics action or explains model-specific DAX.
4. An execution action constructs or supplies DAX for the configured model.
5. The Power BI connector runs the query with the requesting user's connection.
6. The agent explains the returned result, its metric, time scope, and limitations.

The supported analytics surface must be defined by the actual tool inputs and query construction, not simply by a broad instruction such as "answer any question."

## What is actually deployed

- Three preserved connector tools: smoke test, governance counts, and top-100 ranking.
- `ModelAnalytics`: a generatively selected topic with structured inputs, executable Power Fx validation/query construction, and an Invoker Power BI connector action.
- `ModelDaxAdvice`: a separate topic using the same query-construction logic without a connector action.
- `ModelQuestionClarification`: handles unsupported or ambiguous model questions.

The Python compiler in `agent/analytics.py` is **local authoring and verification tooling**, not a hosted Python service in the runtime architecture. It emits the Power Fx topic definitions and compiles matching DAX for offline/direct checks. The live runtime uses Copilot Studio and its connector.

Date/filter/alternative-limit rankings select ModelAnalytics rather than the fixed all-history tool.
The runtime resolves `last30Days` from a captured UTC calendar clock before query construction,
and returns requested bounds separately from observed event bounds. See [date filtering](date-filtering.md).

Metrics and model identifiers are selected through fixed mappings. The analytics interface does not accept arbitrary DAX, arbitrary workspace/model IDs, or user impersonation parameters. This allows varied questions within a finite approved schema rather than pretending to expose an unrestricted SQL-like console.

The editable diagram is [architecture.excalidraw](assets/architecture.excalidraw). The [walkthrough](index.html#architecture) contains a rendered version.

## Three things that must stay separate

| Responsibility | What it means |
|---|---|
| Grounding | Actual model tables, columns, measures, relationships, date semantics, and business definitions. |
| Execution | An authenticated, scoped Power BI query call. |
| Explanation | Interpreting returned results, or teaching DAX without pretending a suggestion was executed. |

The Power BI connector accepts DAX query text. It does not automatically discover the model or supply reliable natural-language-to-DAX generation. The Execute Queries API is not a general schema-discovery endpoint; its documented limitations exclude INFO and DMV queries.

## Authentication and authorization

The agent uses **Invoker/end-user credentials**, not a maker-owned connection as a fallback. There are separate configuration steps:

- Create or select a connected Power BI connection.
- Bind the agent's connection reference.
- Approve the agent's use of that connection when prompted.

An existing environment connection does not by itself prove that the agent's runtime connection is approved.

Power BI is responsible for access enforcement. Read/Build permissions and row-level security apply to the executing identity. Workspace Admin, Member, and Contributor roles do not have the same RLS behavior as Viewer. A model that allows a user to read sensitive data cannot be made secure merely by telling the agent not to mention it.

## Boundaries and failure handling

- Keep the target workspace and semantic model in controlled deployment configuration.
- Do not expose arbitrary model IDs or impersonated-user inputs to the agent.
- Prefer approved measures and bounded structured inputs for repeatable analysis.
- Treat generated DAX as unverified until it has executed successfully.
- Enforce constraints in the query-building/execution layer wherever possible; prose is not enforcement.
- Check both transport errors and errors embedded in the response.
- Report unsupported questions, empty results, date coverage, and truncation explicitly.
- Distinguish an approved-tool restriction from full-model absence or an actual permission failure.
- Do not return owner identities, transcripts, or individual interaction records in this demonstration.

An approved fixed top-100 query can remain alongside reusable analytics. Tools should be organized by capability, not multiplied for each natural-language wording.

The reusable query produces one Summary row and at most 100 aggregate Data rows. It excludes zero/blank groups and uses a stable group key for sorting. Agent grouping excludes missing agent keys. All-surface totals can include base Copilot or unlinked audit events, so an all-surface total is not necessarily the sum of named-agent results. Distinct-user/session counts across groups are not additive.

Input/result limits do not prove low scan cost for every model; benchmark representative data volumes before production use.

## Why not Fabric data agents or MCP?

Fabric data agents are not necessary to execute DAX against an existing semantic model. The connector uses the Power BI API.

Hosted Power BI MCP can offer schema retrieval and query execution, but it is a separate integration with its own tenant settings, authentication, preview status, and tool entitlements. The available MCP connection was not validated for the model used during this PoC. It is not represented as a working dependency.

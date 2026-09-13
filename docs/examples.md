# General-question examples and evidence labels

These are prompts and expected answer contracts for the **generated-DAX design**, not predefined
metric mappings. No successful new-runtime conversation is fabricated. Names/numbers in the ranking
illustration are synthetic; direct test fixtures are not proof of cloud query generation.

`Agent365` is the custom example model/report, not Microsoft Agent 365.
The tests used a **Power BI semantic model containing agents**, with agent inventory,
creator/ownership and usage data. These are agent-focused examples because of that model's data,
not because the reusable connector is restricted to agents.

![User-provided Power BI Copilot interactions report for the tested agent-focused semantic model.](assets/powerbi-agents-report.png)

This is report context, not a Copilot Studio answer. The report uses a different displayed date
window from the conversation tests and does not independently verify their totals.
The report and semantic model are not included in the solution ZIP.

## Actual published M365 prompts

These three prompts completed in the published channel. See the
[real redacted screenshots and specific evidence boundaries](m365-testing.md):

> Review the Agents semantic model and provide me the top 20 used agents and their creators.

> For the same period, show only the top 5 agents in a table with Agent, Creator, and Interactions. Keep the same usage definition and state the exact date range.

> Based on this semantic model, write DAX to compare interactions by platform over the same date range. Explain the filter context and mark the DAX as unexecuted. Do not execute the proposed business query.

The first answer contained 20 descending, distinct usage values and creators. The second matched
the prior first five, but used a list instead of a table. The third explicitly labeled its DAX
unexecuted, but used prose rather than a code block. Values, DAX semantics and advice-path
nonexecution were not independently audited. These are observations, not reusable fixed queries.

## Metadata before querying

> What tables and measures are in this model? Retrieve the model metadata before answering.

Expected behavior: invoke metadata retrieval, complete its requesting-user visibility probe, and
answer from the prepared catalog. State snapshot freshness and avoid treating missing descriptions
or an access failure as proof that data does not exist.

**Observed result:** after the numeric output-type correction, the user's Studio answer listed the
model catalog, measures, snapshot freshness and relationships. Metadata retrieval now succeeds.
After the generic output correction, dated usage ranking and contextual creator/owner answers
also succeeded in the user's Studio session. Separate automated-client authorization boundaries
are not diagnoses of that user's connection.

## Multiple dimensions and filters

> Compare usage by platform and region, filtered to two specified environment types. Show the query you used.

The orchestrator should find the actual relevant columns/measures, generate the combined expression,
and explain the resulting metric and filters. The old one-group/one-filter limit no longer defines
the expression contract.

Do not invent categorical values. If the user has not supplied them and metadata does not establish
them, clarify or use an authorized bounded lookup.

## A derived calculation

> Calculate sessions per user by platform and explain what that ratio means.

The proposed formula should use verified measure names and handle division by zero. It must explain
the measure grain and avoid asserting that ratios or distinct counts are additive across groups.

Illustrative table expression using names from the example model, **not a captured cloud-generated
answer or an executed-as-shown result**:

```dax
SUMMARIZECOLUMNS(
    'Agent'[Platform],
    "SessionsPerUser", DIVIDE([Interaction Sessions], [Interaction Users])
)
```

The actual tool receives a table expression and projection/order metadata; it forms its own bounded
execution envelope. This example is not an arbitrary full DAX script to paste as a tool argument.

## Dates beyond one fixed period

> Give me the top agents and their usage over the last 30 days.

> Compare the last complete calendar month with the preceding month.

The model can generate paired scalar date expressions from the engine's `UTC_TODAY` context and
use `QUERY_START`/`QUERY_END` in the table expression. It must state the interpretation, retain the
requested interval, and distinguish observed records from completeness/refresh claims.

See [date semantics](date-filtering.md). Reference checks do not prove that arbitrary generated
filter logic is semantically correct; observe the actual query.

## Top-100 presentation

> Give me the top 100 agents by usage.

The ranking is now a regression goal for the generic expression path, not a fixed-query tool
dependency. Preserve ranking order and the requested available rows up to the 100-row limit.

![Synthetic ranking illustration, not a live Copilot Studio answer.](assets/illustrative-ranking-output.png)

Only three invented rows are shown in the illustration. The direct generic-contract regression
matched the original top-100 membership/order; that is not a successful new cloud-chat transcript.

## Explain DAX without executing it

> Write DAX for sessions by month and explain filter context. Do not execute the business query.

Expected behavior: retrieve authorized metadata and compile suggested DAX. The metadata visibility
probe may run, but the proposed business query must not. Label the code **UNEXECUTED** and do not
claim a measure was created or saved.

Exact measure expressions are not retained by the current metadata preparation path. The agent must
not pretend to know an existing measure's implementation merely because its name is in the catalog.

## Owner/creator questions and actual access

**User-observed successful follow-up:** after receiving a dated usage ranking, the user asked
"now get me their creator details". The answer retained the same date window and usage order,
then added creator/owner information. The identity-bearing screenshot and values are not published.
The earlier combined, single-turn two-scope request remains unresolved; this confirms the
contextual follow-up, not every possible combined request.

> Which fields describe an agent's creator, and can you count records with that information?

The old blanket owner-field exclusion has been removed from the generic contract. Use the actual
retrieved schema and requesting-user permissions; do not claim a field is absent because an earlier
PoC omitted it. Direct owner/creator aggregate-count checks did not print identities.

This repository still excludes personal/business values from examples and screenshots. Removing an
invented query-field ban is not permission to publish private results or bypass RLS/OLS.

## Unknown or ambiguous questions

> Rank agents by satisfaction.

Establish whether there is a relevant metric and what it means. Do not substitute interaction count
for satisfaction. Explain missing context or actual access failures without inventing schema or
results. A new expression is not automatically a correct business answer.

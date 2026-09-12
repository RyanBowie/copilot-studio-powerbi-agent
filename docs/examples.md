# Prompts and output contracts

**All named agents and numeric outputs below are synthetic publication fixtures.** They illustrate expected presentation; they are not screenshots or transcripts of customer data. Actual verification status is recorded separately.

The `Agent365` example is a custom semantic model/report, **not Microsoft Agent 365**. These governance prompts are examples of the broader pattern. Other models can support their own sales, operations, finance, or service questions after the model-specific configuration and grounding are adapted.

## Top 100 agents

**Prompt**

> Give me the top 100 agents by usage.

**Illustrative output**

> Ranked by audited Interactions for the selected period. The full result contains up to 100 agents, ordered highest first. Only three synthetic rows are shown in this documentation excerpt.

| Rank | Agent | Interactions |
|---|---|---|
| 1 | Service Desk Demo | 1,284 |
| 2 | Policy Finder Demo | 976 |
| 3 | Onboarding Demo | 811 |

The live top-100 experience should return all available requested rows up to its limit, not silently reduce the answer to ten. The documentation excerpt is intentionally shorter and is not a complete result.

![Synthetic documentation rendering of the ranking output, not an actual Copilot Studio result.](assets/illustrative-ranking-output.png)

## Reusable analytics

The deployed reusable topic supports five metrics, one grouping, one exact categorical filter, optional paired inclusive audit dates up to 366 days, sorting, and 1-100 groups. It returns an additional Summary row. These prompts remain evaluation scenarios, not captured successful agent transcripts.

| Prompt | What a good answer establishes |
|---|---|
| How many agents and environments are visible to me? | The actual count definition; no unsupported claim that row counts are distinct entities. |
| Show usage by environment for the last complete month in the data. | Usage measure, date boundaries, grouping, and model freshness. |
| Which ten agents have the highest interaction count in that period? | The same metric and period; ordering and limit are explicit. |
| Compare usage across supported agent types. | Uses a real supported grouping, or clearly states that the field is unavailable. |
| What changed compared with the preceding period? | Uses comparable windows if supported; otherwise states the current capability boundary. |

"Compare periods" is not a dedicated compiler operation. It would require separately executed comparable queries and interpretation; do not present it as a built-in, verified single-call feature.

"Last month" should not be silently interpreted as a calendar month that lies beyond the data's refresh range. The agent should explain which time range it used.

### Concrete structured request

> Show interactions by platform for August 2026.

```json
{
  "metric": "interactions",
  "groupBy": "platform",
  "filterBy": "none",
  "filterValue": "",
  "relativePeriod": "none",
  "startDate": "2026-08-01",
  "endDate": "2026-08-31",
  "topN": 20,
  "sortBy": "value",
  "mode": "execute"
}
```

The answer should use the Summary row to state the actual audit window and whether more groups exist, rather than inferring completeness from the displayed row count.

### Last-30-days ranking

> Give me the top agents and their usage over the last 30 days.

Use the reusable analytics route, not the fixed all-history ranking. Resolve the 30 inclusive UTC
calendar dates from the invocation clock, and display the requested period separately from observed
event bounds. On the test date of 12 September 2026, the requested window is 14 August through
12 September inclusive. This is a test fixture, not a fixed production interval.

No complete successful chat transcript is claimed for this scenario; see [date filtering and verification](date-filtering.md).

## Model-grounded DAX help

**Prompt**

> Explain how to write DAX to rank agents by Interactions. Use the actual model names and explain the filter context. Do not run the query yet.

**Expected answer contract**

- Names only tables, columns, and measures found in the model contract.
- States whether it is writing a query, a measure, or a calculated column.
- Explains aggregation grain, filters, ties, ordering, and date assumptions.
- Prefers existing measures where their definitions match the question.
- Labels the DAX **suggested, not executed** when execution was not requested.
- Does not claim that new measures were saved to the model. This integration is read-only.

### Model-grounded DAX illustration

**Suggested DAX, not executed as shown and not captured from a live agent answer:**

```dax
EVALUATE
SUMMARIZECOLUMNS(
    'Date'[YearMonth],
    "Sessions", [Interaction Sessions]
)
ORDER BY 'Date'[YearMonth]
```

This uses a verified column and measure name from the custom example's contract. It is a query, not a new measure definition. It groups the existing sessions measure by month; without a date filter it covers available dates in context. Distinct sessions across months are not necessarily additive.

The deployed advice topic returns the compiler's bounded query, including its Summary row, rather than promising to generate unrestricted arbitrary DAX. Further natural-language explanation must stay grounded in the declared model contract.

## Unsupported analysis

**Prompt**

> Rank agents by customer satisfaction and include their owners' email addresses.

**Expected behavior**

Explain whether the model contains an approved satisfaction metric; do not substitute Interactions as if it meant satisfaction. Do not expose owner email addresses through this demonstration. Offer a supported aggregate alternative.

Do not claim the underlying model lacks owner/creator fields merely because the approved contract excludes them. Say that these fields are **not exposed by the current PoC tools**, and that full-model presence/absence has not been established.

# Date semantics in generated DAX

**Current design:** generated scalar date expressions, not the retired finite
`relativePeriod=last30Days` compiler. The original date-routing incident is useful historical
evidence, but its old input schema is no longer the runtime contract.

## Trusted anchor, generated periods

The execution envelope captures `UTCNOW()` and defines `UTC_TODAY`. The orchestrator generates
paired scalar date expressions for the requested interval, then uses `QUERY_START` and `QUERY_END`
in the proposed table expression.

Examples of language primitives, **not captured successful cloud outputs**:

| Interpretation | Example scalar expressions |
|---|---|
| 30 calendar dates including the current UTC date | `UTC_TODAY - 29` through `UTC_TODAY` |
| 90 calendar dates including the current UTC date | `UTC_TODAY - 89` through `UTC_TODAY` |
| Last complete calendar month | `EOMONTH(UTC_TODAY,-2)+1` through `EOMONTH(UTC_TODAY,-1)` |
| Calendar year to date | `DATE(YEAR(UTC_TODAY),1,1)` through `UTC_TODAY` |

For a test anchor of 12 September 2026, 30 inclusive calendar dates are 14 August through
12 September. Production must not hardcode that example or silently anchor to the latest recorded
event instead.

UTC is the declared engine anchor. It does not establish the source-event timezone. A local-time
or rolling-hour interpretation must be explained and implemented correctly, or clarified.

## What is enforced versus what needs reasoning

Date-bearing requests must supply the paired expressions and reference the trusted date variables.
Common unresolved-date prompts are rejected rather than intentionally routed to all history.

These are **reference and intent guards**, not a semantic proof of arbitrary DAX. A generated
expression might reference a date variable without filtering as intended. Inspect the actual DAX
and test known answers; do not treat a lexer or a prompt instruction as proof of date correctness.

The output Summary records the evaluated requested dates and UTC anchor. If observed first/last
event bounds are included, they are not refresh timestamps, continuous-coverage guarantees, or
proof that no activity occurred outside the returned data.

No matching rows means no matching returned rows in that scope. Do not widen the interval.

## Advice

The advice capability uses the same expression contract without executing the proposed business
query. Its output must be marked unexecuted. The separate metadata authorization probe may still
run.

## Historical incident and regression

An earlier agent chose or described an all-history ranking when the user asked for the last 30 days.
The screenshot did not establish the exact selected tool. That fixed/bounded architecture was
subsequently replaced; its specialist top-100 query is no longer a runtime dependency.

Direct generic-expression checks include explicit-date rankings and complete-month comparisons.
These checks do not establish successful cloud generation, topic selection, or final chat wording.
See [verification](verification.md) for the unresolved test routes.

[Copilot Studio date and time handling](https://learn.microsoft.com/en-us/microsoft-copilot-studio/manage-date-and-time)

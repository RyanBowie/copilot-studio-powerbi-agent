# Filtered rankings and relative dates

**The fixed all-history ranking is not an acceptable substitute for a requested date range.**

The date correction was published on 12 September 2026. It addresses conflicting ranking routes and the absence of deterministic relative-date resolution. It does not add another model or broaden data access.

## Which capability should run?

| Request | Route |
|---|---|
| Original unfiltered, all-history top 100 agents by usage | Preserved fixed top-100 tool |
| Top agents over the last 30 days | Reusable ModelAnalytics, interactions by agent, descending value; default 20 groups if unspecified |
| Top 100 agents over the last 30 days | Reusable ModelAnalytics with a 100-group limit |
| Ranking with explicit dates, a categorical filter, another metric, or another limit | Reusable ModelAnalytics |
| Explain the DAX for a supported date-scoped request without running it | Connector-free advice route using the same compiler |

The fixed tool's description was narrowed; its DAX bytes were preserved. The agent must not describe implemented date-scoped analytics as a future feature or redirect to report filtering instead of using the supported route.

## What "last 30 days" means here

The implementation uses **30 inclusive UTC calendar dates, including the invocation date**:

- Capture the trusted runtime clock once.
- End date is the current UTC calendar date.
- Start date is that date minus 29 days.
- Compare against the model's `Date.Date` values as stored.

For the **test fixture** of 12 September 2026, the requested interval is **14 August through 12 September 2026 inclusive**. Production does not hardcode these dates or anchor to the latest recorded event.

This is a calendar-date window, not exactly the preceding 720 hours. The source-event timezone is **not established** by the approved schema. UTC is the declared anchor convention, not a claim that all source events were recorded in UTC.

Requests for a different local-time convention, latest-available-event anchoring, or an unsupported unresolved period should clarify the interval rather than silently reinterpret it.

## Structured input

```json
{
  "metric": "interactions",
  "groupBy": "agent",
  "filterBy": "none",
  "filterValue": "",
  "relativePeriod": "last30Days",
  "startDate": "",
  "endDate": "",
  "topN": 20,
  "sortBy": "value",
  "mode": "execute"
}
```

Use `relativePeriod=none` for explicit paired dates or genuinely unfiltered requests. Unknown/unresolved relative values stop for clarification. Do not combine an explicit interval and a relative period.

The runtime resolves dates before validation and DAX construction; it does not rely solely on an LLM supplying an invented current date. Advice uses the same date interpretation without executing the query.

## Requested interval versus observed data

The Summary row separates:

| Field | Meaning |
|---|---|
| `RequestedStartDate` / `RequestedEndDate` | The actual requested, resolved interval |
| `RelativePeriod` / `DateConvention` | How that interval was interpreted |
| `WindowStart` / `WindowEnd` | First/last observed matching events, where the measures support them |
| `TotalGroups` / `ReturnedGroups` / `HasMore` | Result completeness relative to the group limit |

Observed event bounds are **not refresh timestamps**, proof of continuous coverage, or evidence that nothing happened outside them. If recent records are missing, preserve the requested interval and disclose the observed bounds. If no recorded events match, say so; do not widen to all history or assert that there was no activity.

The ranked answer should preserve the requested number of available rows, ordering, and readable ranking format. This documentation does not publish actual agent names or usage figures from the user's screenshot.

## Verification and remaining uncertainty

- The local and sanitized source suites passed **25 tests**, covering routing declarations, clock/date handling, month/year/leap boundaries, UTC-midnight behavior, conflicting inputs, no all-history fallback, and generated-topic parity.
- Three fixed, seven reusable, and five date-specific direct-query cases passed.
- The original fixed DAX, Invoker binding, and user's cloud reasoning-model selection were preserved.
- The date-capable topic was published and read back.

**Full agent chat remains unverified.** The screenshot did not prove which tool or arguments produced the faulty answer. Subsequent chat probes did not reveal a completed invocation: the shared authenticated browser was unavailable, one advice probe returned no activities, and an existing-conversation read returned 404.

These are not proof of a new authentication problem or a successful date-filtered conversation. A fresh approved Studio test must still confirm the actual selected capability, resolved arguments, query result, and final explanation.

The Agent365 custom-model-versus-product clarification is documentation-only, as requested. Runtime instructions retain the actual schema, business definitions, and scope safeguards.

## Reference

[Copilot Studio date and time handling](https://learn.microsoft.com/en-us/microsoft-copilot-studio/manage-date-and-time)

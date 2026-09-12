# Model-grounded Copilot Studio / Power BI reference

Source-only reference implementation for a standard Copilot Studio agent, not a Fabric data agent.
This publication copy contains placeholder configuration, no live solution export, no authentication
state, no customer output tables, and no screenshots.

**Naming clarification:** `Agent365` is a custom demonstration semantic model/report, not the
Microsoft Agent 365 product or an official product schema. The architecture is reusable with other
compatible models after adapting the model contract, mappings, DAX, configuration and permissions.

## How it works

1. Generative orchestration chooses a preserved specialized tool or a reusable analytics topic.
2. Structured metric/group/filter/date/limit inputs pass executable Power Fx validation.
3. Fixed switches select approved model identifiers; filter literals are escaped.
4. The standard Power BI ExecuteDatasetQuery connector executes against one configured semantic
   model using Invoker/end-user credentials.
5. One Summary row and bounded aggregate rows expose the actual audit window and any result limit.
6. A separate DAX-advice topic uses the same compiler without a connector action; advice is marked
   NOT EXECUTED. It is not evidence of a successful live query.

The three specialized tools cover a constant smoke test, inventory counts, and top-100 agent usage.
They coexist with reusable analytics rather than one tool per business question.

## Model contract and boundaries

The example expects Agent, Interaction and Date tables and the measure names documented in
model-context.json. This is a sample approved schema subset, not automatic support for any model.
Validate and adapt the contract before connecting another semantic model.

Five metrics: interaction turns, distinct sessions, distinct-user counts, inventory agents and
inventory environments. One grouping, one exact categorical filter, optional paired inclusive audit
dates (maximum 366 days), and 1-100 returned aggregate groups are supported. The query includes an
additional Summary row with TotalGroups, ReturnedGroups, HasMore and time-window bounds.

`relativePeriod=last30Days` resolves 30 inclusive UTC calendar dates from the runtime clock,
including today; do not combine it with explicit dates. RequestedStartDate/RequestedEndDate are
separate from observed WindowStart/WindowEnd. The source event timezone is unverified; UTC is
the declared date-anchor convention. Unknown or unresolved periods stop for clarification rather
than widening to all history. See `..\docs\date-filtering.md`.

Any date/filter/alternative-limit ranking uses ModelAnalytics. The fixed top-100 tool is reserved
for the unfiltered all-history scenario; its original DAX is unchanged. The Agent365 product-naming
clarification remains in this README and public documentation, not in runtime instructions.

No arbitrary DAX execution, mutable model IDs, owner/user identities, transcripts, raw session IDs,
anonymous endpoint, or maker-credential fallback is exposed. Inventory counts are current snapshots,
not historical inventory. Distinct counts across groups are not necessarily additive.

## Example prompts

- Show interactions by platform for a selected month.
- How many agents are in each current risk band?
- Show distinct sessions by month in chronological order.
- Show the top three client hosts by distinct-user count.
- Write DAX for sessions by month; do not execute it.
- Give me the top 100 agents by usage.

See examples.json for precisely labelled evidence versus illustrations. No successful user-facing
analytics screenshot is included. Do not render illustrative output as if it were captured evidence.

## Configure your own existing agent

1. Install Python dependencies from requirements.txt and Node dependencies with npm ci.
2. Copy resources.example.json to resources.json (gitignored), and enter your own resource IDs.
   Never place connection credentials or tokens in that file.
3. Run python configure.py, then npm test.
4. Review the model mappings and generated YAML, then use python deploy.py only against your own
   existing standard agent and dedicated solution. It does not create the initial agent.
5. Create/choose your own authorized Power BI connection and bind your connection reference in
   the target environment. Retain Invoker/end-user credentials.
6. Publish with PAC using explicit environment/agent IDs. Wait for publishing and synchronization.
7. Test in your approved Studio session. Test-channel connection approval is separate from merely
   creating an environment connection.

Do not change global account/profile selections to run these scripts. Deployment gets tokens through
the user's existing Azure CLI authentication and keeps them in memory. Inspect live changes before
deployment; protected specialized tools are not silently overwritten.

## Validation status and limitations

The sanitized source passes **25 offline tests**, including scope and date regressions. Three fixed,
seven reusable, and five date-specific queries passed directly in the development model. These are not full runtime
conversation tests.

The implementation's unit tests and direct compiled-query cases passed in its original environment.
The original top-100 source was preserved. These statements do not establish that your deployment
will work without configuration, model validation and consent.

Automated chat-to-query-to-answer and live DAX-advice output were not fully verified. The evaluation
channel requested per-agent connection approval; a separate published invocation route lacked its
required first-party preauthorization. No permission bypass or maker fallback was used.

For the latest date correction, the shared authenticated browser was unavailable, a connector-free
advice probe returned no activities, and an existing-conversation read returned 404. Those observations
do not prove an authentication failure, tool invocation, or a full chat pass.

The latest scope correction distinguishes approved-tool restrictions, unknown full-model metadata,
verified absence, and actual access errors. Owner/creator requests receive a scope explanation,
not a claim that the underlying model lacks those fields. This did not expand identity access,
change queries, or replace the user's selected cloud reasoning model.

Run npm test for offline checks, python verify-model.py and python verify-analytics.py for explicitly
authorized direct queries, and npm run test:agent -- --maker-test for a separate actual chat probe.
The direct query scripts are not chat E2E tests. Review runtime output privately; do not commit logs.

## Before public release

Keep the repository private and Pages disabled until owner review. Check every source file and image
for actual IDs, account names, URLs, business statistics, connection state and credentials. Never add
raw solution ZIPs, .mcs state, local configuration, chat transcripts or unredacted screenshots.
No GitHub repository or Pages setting is changed by this source bundle.

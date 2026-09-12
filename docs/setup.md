# Preparing and testing the generated-DAX design

**Experimental: the deployed generic runtime has not passed a complete cloud conversation.**
Do not mistake successful local/direct tests for a ready production agent.

The custom `Agent365` example is not Microsoft Agent 365. Reuse requires metadata preparation,
appropriate identity access, deployment review, and realistic testing on the intended model.

## Prerequisites

- An existing standard Copilot Studio agent and dedicated development solution.
- Copilot Studio/Power BI licensing and permitted connector use.
- Runtime users with appropriate Power BI Read/Build rights.
- The tenant Execute Queries setting and applicable model/RLS/OLS permissions.
- An already-authorized owner for Fabric definition preparation, which requires read/write rights.

Do not grant model-write rights to all runtime users for convenience. No credentials belong in
source or the local resource configuration.

## Owner preparation and deployment

Work in a private deployment copy:

```powershell
Set-Location agent
python -m pip install -r requirements.txt
npm ci
Copy-Item resources.example.json resources.json
# Fill the ignored resources.json with your own existing resources.
python deploy.py --capture
python prepare-model.py
python general_runtime.py
npm test
```

Inspect the generated private source, retained metadata, active capability changes, and cloud
configuration before applying:

```powershell
python deploy.py --apply --publish
```

The workflow refuses concurrent cloud edits and preserves current AI/authentication settings
rather than deploying an old `settings.mcs.yml`. It checks native parsed model settings and topic
contracts before and after publication, rather than trusting raw YAML. A persisted model-name
string alone is not proof of the picker selection or effective model.
Inspect warnings, reopen the model picker, and compare the post-publication representation.

The snapshot is a governed preparation artifact. Refresh and republish after model changes.
It is not an automatically refreshed remote catalog, and only alias `primary` is onboarded.

## Verify in layers

1. **Offline contract/client tests:** `npm test`.
2. **Authorized direct model checks:** `python verify-generated.py`.
3. **Metadata-only chat:** ask "What tables and measures are in this model? Retrieve the metadata first."
4. **Generated-query chat:** observe a model-authored expression, actual tool inputs, execution, and Summary.
5. **Realistic analytics:** multiple dimensions/filters, a derived calculation, dates, and a top-100 regression.
6. **Advice-only:** verify no proposed business query executes; metadata authorization may still probe.
7. **Negative cases:** unavailable fields, denied visibility, stale metadata, oversized output, and ambiguity.

The unit fixtures are not cloud-generated queries. Inspect the activity plan and actual arguments
before claiming that the orchestrator retrieved metadata or authored the executed expression.

## Test routes are not interchangeable

```powershell
node test-agent.cjs --prompt "What tables and measures are in this model?" --save-evidence
```

This uses the published SDK route. `--maker-test` explicitly selects the separate evaluation route.
Both must forward the requested prompt; a retired fixed-tool prompt is not a valid generic-runtime test.

The corrected SDK attempt returned 403 before conversation creation because its token had
`CopilotStudio.Copilots.Test`, not `CopilotStudio.Copilots.Invoke`. Do not diagnose that as a
Power BI connector login problem. Use an appropriately authorized supported client; this repository
does not request or bypass missing permissions.

Separately, the evaluation route selects metadata after serialization repair. Attempts have returned
HTTP 504 and, after the later alias repair, the previous local validation error/output contract.
A normal Studio session must still be tested; neither
topic selection nor an HTTP error establishes that the complete published UI flow works.

`test-studio.cjs` uses an independent project-local browser profile and never the shared MCP browser.
It does not enter credentials or fabricate interaction evidence.

## Keep private artifacts private

Do not commit `.generated-private`, real metadata snapshots, resource IDs, browser profiles, raw
definitions, solution exports, runtime probes, transcripts, or business rows. The source bundle has
synthetic metadata for offline tests, not the live model snapshot.

Before enabling Pages or changing repository visibility, complete the [release checklist](public-release.md).

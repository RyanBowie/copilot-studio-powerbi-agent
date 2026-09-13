# Preparing and testing the generated-DAX design

**Experimental: scoped Studio and published M365 conversations have succeeded.**
This is not production certification or proof of correctness for every model/question.
See the [actual M365 tests and limitations](m365-testing.md).

The custom `Agent365` example is not Microsoft Agent 365. Reuse requires metadata preparation,
appropriate identity access, deployment review, and realistic testing on the intended model.

## Prerequisites

- An existing standard Copilot Studio agent and dedicated development solution, or the
  [importable unmanaged starter ZIP](solution-import.md).
- Copilot Studio/Power BI licensing and permitted connector use.
- Runtime users with appropriate Power BI Read/Build rights.
- The tenant Execute Queries setting and applicable model/RLS/OLS permissions.
- An already-authorized owner for Fabric definition preparation, which requires read/write rights.

Do not grant model-write rights to all runtime users for convenience. No credentials belong in
source or the local resource configuration.

## Owner preparation and deployment

Create a standard agent in Copilot Studio if you do not already have one. Use a dedicated
development solution; identify its environment URL, agent ID and schema name. In that environment,
create a Power BI connection using an authorized account and a solution connection reference.
Configure requesting-user/Invoker execution rather than silently using the maker's identity.
The deployment script updates an existing agent; it does not provision all of these resources.

Install Python and Node.js for the source tools, and authenticate the Azure CLI to the intended
tenant using your organization's supported process. Review `agent/resources.example.json` and
`agent/README.md` for the complete configuration and tool prerequisites. Resolve workspace/model
identifiers from your own authorized Power BI resources. Do not copy this demonstration's identifiers.

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

## Publish and test in M365 Copilot

1. Open the agent's Overview and inspect its instructions and model picker. Preserve the intended
   model selection; preview models carry separate suitability warnings.
2. Inspect Topics: **Get model metadata**, **Run generated DAX**, **Compile DAX advice** and
   **Generated query error** are the active generic capabilities. Connector actions are inside these
   topics; an empty standalone Tools tab is intentional, not a missing Power BI integration.
3. Inspect the conversation starters. They are example prompts, not fixed-query tools or a list
   of all supported questions.
4. Publish in Studio and enable the Microsoft 365 Copilot channel using the tenant's permitted
   availability/sharing process. Follow any administrator approval requirements. Copy your own
   published agent link; this repository deliberately contains no tenant-bound deep link.
5. Open a new M365 conversation as the intended user. If prompted, approve use of their existing
   Power BI connection. Consent does not grant Read/Build, bypass RLS/OLS, or authorize maker fallback.
6. Run the [three generic prompts](m365-testing.md), then expand to representative questions and
   identities. Inspect actual activity inputs and compare important values with independent model
   queries. UI completion alone does not establish correct DAX filter context.

The demonstration currently shows two warnings: preview-model suitability and no formal Studio
evaluation. Its browser tests do not satisfy the formal evaluation feature. Evaluate correctness,
permissions and expected question coverage before treating your own deployment as production-ready.

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
Those historical failures did not establish whether the complete UI flow worked. Subsequent
Studio and M365 observations are successful through their own authenticated sessions; neither
topic selection nor an HTTP error alone establishes UI completion.

The automated evaluation's connection-manager card is separate from the connected Studio user.
Metadata now succeeds, and actual caller queries returned successful envelopes before local
projection erased their fields. After the dynamic-output correction, the user confirmed a dated
ranking and contextual creator/owner follow-up. Preserve that working deployment. The original
combined request remains unresolved, but no further user retry or permission change is requested.
For your own deployment, follow the layered evaluation matrix rather than assuming those results
transfer to another model or identity.

`test-studio.cjs` uses an independent project-local browser profile and never the shared MCP browser.
It does not enter credentials or fabricate interaction evidence.

## Keep private artifacts private

Do not commit `.generated-private`, real metadata snapshots, resource IDs, browser profiles, raw
definitions, tenant-bound solution exports, runtime probes, transcripts, or business rows. Only the
separately generated and inspected unconfigured starter ZIP is approved for this repository. The source bundle has
synthetic metadata for offline tests, not the live model snapshot.

Before enabling Pages or changing repository visibility, complete the [release checklist](public-release.md).

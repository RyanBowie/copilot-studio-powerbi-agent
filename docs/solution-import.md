# Import and configure the Power BI Query Runtime

**[Download PowerBIQueryRuntime_unmanaged.zip](https://ryanbowie.github.io/copilot-studio-powerbi-agent/downloads/PowerBIQueryRuntime_unmanaged.zip)**
and its [checksum/configuration manifest](downloads/package-manifest.json).
The ZIP itself is the unmanaged Power Platform solution: select it directly in the import wizard.
Do not unzip it, import a repository/source archive, or look for another ZIP inside it.

This package contains the demonstrated **native implementation**, adapted to read trusted model
configuration after import. It is not the old onboarding-only starter. Its metadata authorization
probe, DAX compiler/executor, advice and error handling are present. Configuration is disabled by
default; setting reviewed configuration values enables the retained paths without rebuilding,
replacing or pasting topic YAML. Python is an owner preparation/setup tool, not a hosted runtime.

**Evidence is artifact-specific:** read [import-verification.json](https://github.com/RyanBowie/copilot-studio-powerbi-agent/blob/main/solution/import-verification.json)
for the exact ZIP hash and operations actually verified. The [historical starter observation](https://github.com/RyanBowie/copilot-studio-powerbi-agent/blob/main/solution/starter-import-verification.json)
does not validate this package. Native import and structural checks do not establish configured
query-to-answer correctness, licensing, cross-tenant behavior or every user's permissions.
This exact runtime ZIP passed an authorized sandbox import and full component/configuration
readback on **21 September 2026**. It remained unpublished, unbound and `NOT_CONFIGURED`;
configured conversations and live configuration-apply transactions were not tested.

## What travels in the solution

| Component | Contents |
|---|---|
| Solution and agent | `poc_PowerBIQueryRuntime`, version `1.0.0.0`; display name **Power BI Query Runtime** |
| Four native topics | Model metadata, generated DAX execution, unexecuted advice, and actual-error reporting |
| GPT configuration | Real generic instructions, neutral starters; no forced preview-model selection |
| Fifteen native variables | Hidden conversation/provenance state; no external initialization or external output |
| Power BI connection reference | `poc_PowerBIQueryRuntime_PowerBI`; connector identity only, no bound connection |
| 129 Text environment definitions | `poc_PowerBIQueryRuntime_Config_Manifest` and `..._Chunk001` through `..._Chunk128`, all default `NOT_CONFIGURED` |
| 387 associations | Each of metadata/query/advice linked to its 129 configuration definitions |
| Public source and build | [Unpacked source](https://github.com/RyanBowie/copilot-studio-powerbi-agent/tree/main/solution/src), [builder](https://github.com/RyanBowie/copilot-studio-powerbi-agent/blob/main/scripts/build_solution.py), and checksum manifest |

There is no cloud flow, custom connector, MCP server or Fabric data agent dependency. The standard
Power BI connector is required. The package excludes the original report/model, private metadata,
results, workspace/dataset/tenant IDs, credentials, current environment-variable values, connection
bindings and channel registrations. It does not auto-publish.

`Agent365` is a **custom demonstration report/model**, not the Microsoft Agent 365 product or an
official product schema. Supply the contract for your own model; the demo's business meanings do
not automatically apply.

## Prerequisites

- A dedicated development/sandbox environment that permits unmanaged solutions and has Copilot
  Studio provisioned; appropriate authoring/runtime licensing and import privileges, normally
  System Customizer or Administrator.
- An approved Power BI semantic model/workspace and licensing for its use; tenant **Dataset Execute
  Queries REST API** setting enabled and Power Platform data policies permitting `shared_powerbi`.
- Intended runtime users with suitable **Read and Build** access, plus applicable RLS/OLS access
  and their own Power BI connection/consent. Build is more powerful than report viewing.
- An already-authorized model owner for Fabric definition preparation, which requires existing
  model read/write rights. Do not grant model-write rights to every agent user.
- Python **3.12+**, the agent's declared Python dependencies, and an existing approved Azure CLI
  sign-in for owner preparation/configuration. PAC is optional for import and required only to
  reproduce the public ZIP. Node is not a runtime or configuration-helper requirement.

The current setup helper supports commercial Dataverse URLs and bare, lowercase GUID environment
IDs. It deliberately rejects `Default-...` environment IDs and sovereign-cloud destinations.
Do not work around that check by changing identifiers; those destinations need an explicitly
supported configuration contract.

## 1. Import first, without activation

1. Choose a fresh, approved sandbox explicitly. Check that `poc_PowerBIQueryRuntime` and its
   component names do not already exist. Unmanaged reimport can overwrite customizations:
   stop on a collision, back up and review an upgrade separately.
2. In **Power Apps or Copilot Studio > Solutions > Import solution**, select the downloaded
   `PowerBIQueryRuntime_unmanaged.zip`. Review dependencies. A missing-component warning is
   not an acceptable successful import.
3. Leave **Enable Plugin steps and flows included in the solution** unchecked. This solution
   has no workflows, but do not use a broadly activating import setting. Unchecking it would
   not deactivate flows already running in a target environment.
4. For import-only inspection, leave the Power BI reference unbound if the target permits it.
   If connection mapping is mandatory, stop and obtain approval for the intended destination
   connection; never substitute the source maker's credentials.
5. Keep all environment definitions at their supplied **NOT_CONFIGURED** defaults. The wizard
   may expose a long definition list. **There are not 129 manual setup steps**: the helper below
   encodes, writes and verifies every slot in one configuration operation after import.
6. Open **Power BI Query Runtime**. Confirm it is unpublished, has no channels, and contains
   all four topics, the hidden variables and configuration definitions/links. Importing is not
   publishing or sharing.

Optional explicit-target CLI alternative:

```powershell
pac solution import --environment "<TARGET_ENVIRONMENT_ID>" `
  --path ".\PowerBIQueryRuntime_unmanaged.zip" `
  --activate-plugins false --publish-changes false
```

The [package-specific observation](https://github.com/RyanBowie/copilot-studio-powerbi-agent/blob/main/solution/import-verification.json) records actual verification;
the command shown here is not a claim that it has run against your environment.

## 2. Configure connection, authentication and model

Bind the existing `poc_PowerBIQueryRuntime_PowerBI` reference to an approved destination Power BI
connection. Inside both connector actions, retain **Invoker / end-user credentials** and blank
impersonation. Do not change them to maker credentials to make a failed call succeed.
Connection mapping does not grant the chatting user missing Power BI permissions.

Review authentication after import. The package requests **Integrated authentication (2)**,
**Always (1)** and **Group membership access policy (2)**, with no source group IDs. Verify
these values rather than assuming the importer retained them. Configure your approved audience
and groups through your normal approval process before sharing; this download grants no audience
access. Select an available, appropriate reasoning model in Studio and review its warnings.
The demo's preview-model choice is not forced.

The configuration helper requires these auth/privacy values, the exact imported schema, the
bound connection, all native topic/variable bodies and the complete environment associations.
It refuses missing or ambiguous state rather than silently fixing settings or deploying topics.

## 3. Prepare and review your model metadata

Work in a **private deployment copy**, not a public publication worktree. Install the declared
dependencies and create private resource/target configuration from the examples:

```powershell
python -m pip install -r agent\requirements.txt
Copy-Item agent\resources.example.json agent\resources.json
Copy-Item agent\portable-target.example.json C:\PrivateAnalytics\portable-target.json
```

Create the private output directory first. Replace placeholders with your actual tenant,
destination environment URL/ID, imported agent ID, workspace and dataset. Use these fixed package
values wherever the examples request them:

| Key | Package value |
|---|---|
| `schemaName` / `solutionName` | `poc_PowerBIQueryRuntime` |
| `connectionReference` | `poc_PowerBIQueryRuntime_PowerBI` |
| `environmentPrefix` | `poc_PowerBIQueryRuntime_Config` |
| `connectorId` | `/providers/Microsoft.PowerApps/apis/shared_powerbi` |

See the full [private target example](https://github.com/RyanBowie/copilot-studio-powerbi-agent/blob/main/agent/portable-target.example.json) and
[owner preparation instructions](https://github.com/RyanBowie/copilot-studio-powerbi-agent/blob/main/agent/PORTABLE.md#adopter-setup-commands-shown-not-executed-here).
The legacy resource file also asks for a report ID; execution uses the semantic model, not
report visuals. Do not run `general_runtime.py` or `deploy.py` over this imported implementation.

Using the already-authorized owner identity, prepare the governed snapshot:

```powershell
python agent\prepare-model.py
```

Review `agent\model-schema.private.json`. Preparation records source tenant/workspace/dataset
binding; do not invent that binding on an old snapshot. Reprepare it instead. The snapshot
excludes raw definitions, partitions, connections, roles and exact measure expressions.

Review important business definitions separately: metric meaning/grain, duplicate records,
creator/owner fields, blanks, date relationships, source time zone, fiscal/calendar conventions,
default filters and how report-page filters should translate into DAX. A measure name alone
does not establish its calculation. Supply approved guidance rather than guess missing semantics.
Changing only a dataset ID is not model onboarding.

## 4. Load configuration, not topic code

The helper assembles and validates the private document, generates a revision and splits it into
bounded slots. It rejects unsupported shapes, source/target mismatches and excess size without
truncating metadata:

```powershell
python agent\configure_portable.py prepare `
  --snapshot agent\model-schema.private.json `
  --target-config C:\PrivateAnalytics\portable-target.json `
  --out C:\PrivateAnalytics\configuration-v1.private.json
```

`prepare` is offline, prints sizes rather than metadata, and refuses to overwrite an existing file.
Review the private file, then perform the explicit, read-only destination check:

```powershell
python agent\configure_portable.py check `
  --configuration C:\PrivateAnalytics\configuration-v1.private.json `
  --tenant-id "<TENANT_ID>" --environment-id "<TARGET_ENVIRONMENT_ID>" `
  --dataverse-url "https://<TARGET_ORG>.crm.dynamics.com" --agent-id "<IMPORTED_AGENT_ID>"
```

After approval for this separate configuration write, use the same arguments with **`apply`**
instead of `check`. It checks the destination again, changes **only current environment-variable
values in one transactional changeset**, and verifies readback. Existing values use ETags.
All unused slots are explicitly reset to `NOT_CONFIGURED`, so a smaller replacement snapshot
cannot accidentally retain the tail of an older one. Quiesce concurrent configuration/import
operations; duplicate values or conflicting edits block verification.

This tool never changes shared auth defaults, agent permissions, connections, topic/GPT code,
definition defaults or publication state. Never publish after a failed/partial/conflicting check.
Exact commands and implementation boundaries are in [PORTABLE.md](https://github.com/RyanBowie/copilot-studio-powerbi-agent/blob/main/agent/PORTABLE.md).

**Why the chunk count:** Power Platform values are limited to 2,000 characters. Each of the
128 data slots holds up to 1,900 ASCII-encoded JSON payload characters plus a 45-character
revision/index/count header. The document limit is **243,200 characters**, including escaped
text and binding overhead. One manifest makes incomplete or mixed revisions fail closed.
The helper performs the bookkeeping; an adopter supplies meaningful model/target inputs, not
chunk strings. Models beyond the bound need a separately reviewed design, not silent trimming.
Offline boundary tests exercise the exact 128-slot limit, one-character overflow rejection,
Unicode/JSON-escape round-trips, and a large-to-small update resetting every stale slot.
Stored values are escaped ASCII JSON, so character count equals UTF-16 code-unit count; the length
of the unescaped model descriptions is not the platform-value length. These are offline transport
checks, not proof of a complete maximum-size conversation in Copilot Studio.

## 5. Verify, publish and share separately

Environment values are captured in the published agent. **Changing values alone does not update
an already published runtime.** After successful configuration review, explicitly publish in Studio,
start a new conversation, and perform authorized smoke checks before sharing more broadly:

| Check | Expected observation |
|---|---|
| Unconfigured state, before setup | Explicit `NOT_CONFIGURED`, no Power BI call, no schema/results |
| Metadata | Full-reference zero-row probe as the caller; catalog/table output only after verified access |
| Query | New metadata-grounded table expression, bounded execution and Summary; independently verified values |
| Advice | Clearly labelled unexecuted proposed DAX; no business-query action in the advice topic |
| Limits and transport | Up to 100 rows, 16 aliases and 256 text characters; dynamic numeric precision; null omission distinguished from empty text |
| Negative identities/configuration | Denied visibility, stale/mixed configuration, wrong user/turn, unsupported field and malformed output fail explicitly |
| Refresh | Reprepare and review metadata, prepare a new private configuration file, check/apply, republish, new conversation |

These checks are a setup checklist, **not a claim of completed tests on this distributed artifact**.
Configured publication/execution requires separate authorization from import-only verification.
The [M365 demo observations](m365-testing.md) concern the original configured implementation.

Configure and share the Microsoft 365 Copilot channel through the destination tenant's approval
process. Authentication, connection consent, audience and channel registration do not arrive as
a working M365 deployment in the ZIP. See [channel setup](setup.md#publish-and-test-in-m365-copilot).

## Limits and package evidence

Only alias **primary** is configured. Prepared metadata is not live schema discovery or complete
business semantics. The all-column visibility probe may reject narrower OLS users; use a properly
reviewed role-appropriate snapshot, never maker fallback. Structural DAX checks are not a complete
parser, proof of business accuracy or query-cost estimator. Metadata responses retain a 64,000-character
budget even if configuration is larger. Configuration values are not secret storage.

The generic core was compared with the existing original project and a fresh read-only native
export. Native topics matched its private generated source. The baseline generic-runtime commit
and current source hashes are recorded in the package manifest. The builder uses the reviewed
generic source and portable configuration boundary, **never the raw export or private snapshot**.
New schema names avoid replacing the live demo or the historical starter.

Reproduce locally with Python requirements and PAC installed:

```powershell
python scripts\build_solution.py
python scripts\build_site.py
python -m unittest discover -s scripts -p "test_*.py"
python scripts\validate_publication.py
```

PAC creates the unmanaged ZIP; only ZIP headers are normalized, preserving every payload byte.
Entity fragments and native relationship shapes follow authentic/Microsoft-native examples.
The source and downloadable ZIP are checked byte-for-byte, including an actual local HTTP download.
Every decompressed entry is checked against the manifest and reviewed source; unexpected or nested
archives, private current values and bound connections are rejected.

Before a native import observation exists, use `validate_publication.py --allow-unverified-import`
for **local structural/privacy inspection only**. Publication CI never uses this bypass.
A changed ZIP cannot inherit the previous import success; preserve the old observation and perform
a new approved import/readback for the new hash. A clean PAC pack is not native import validation.

Microsoft references: [agent solution import/export](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-solutions-import-export),
[environment values and republication](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-variables-about#environment-variables),
[Power BI Execute Queries](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries).

# Import the Power BI Query Starter solution

**[Download the unmanaged solution ZIP](../solution/PowerBIQueryStarter_unmanaged.zip).**
This is an importable, deliberately **unconfigured starter**, not a preauthenticated copy of the
demonstration. Import was successfully verified in a development environment on 13 September 2026.
The imported agent remained unpublished, had no channels, and its Power BI connection reference
was unbound. Native authoring readback retained the topic contracts and stop-before-query guards.

The package uses its own solution and agent schema, `poc_PowerBIQueryStarter`. It does not replace
the original demonstration agent. Import into a development environment first. Importing again into
an environment already containing this same starter solution can update its unmanaged components;
back up your customizations before reimporting.

## What is included

| Included | Purpose |
|---|---|
| Standard Copilot Studio agent | Generic instructions, generative orchestration and neutral starters |
| Get model metadata topic | Explicit onboarding message in place of a model-specific snapshot/probe |
| Run generated DAX topic | Generic expression/envelope machinery, stopped before execution until configured |
| Compile DAX advice topic | Generic advice machinery, stopped until configured |
| Generated query error topic | Local error handling |
| Power BI connection reference | Connector identity only; no connection, credentials or user binding |
| [Unpacked source](../solution/src) and [build script](../scripts/build_solution.py) | Reviewable, reproducible package source |

The starter does **not** contain the demonstration's semantic model, report, metadata snapshot,
workspace/dataset IDs, real connections, identities, result rows, channel registration, or preview-model
selection. It contains no Fabric data agent, custom MCP server, cloud flow or custom connector.
The standard Power BI connector must be permitted in the destination environment.

**Do not remove the configuration stops and merely replace two IDs.** The metadata topic's
model-specific authorization probe and governed catalog must be generated for the actual target
model. Until then, all callable topics explicitly explain that configuration is required and stop;
they do not return synthetic data or attempt a query against a placeholder model.

## Import and configure

1. Select the intended development environment in Power Apps or Copilot Studio. You need appropriate
   import privileges (typically System Customizer or Administrator), required licensing, and permission
   to import unmanaged customizations.
2. Open **Solutions > Import solution**, select `PowerBIQueryStarter_unmanaged.zip`, and complete the
   import. If asked for the Power BI connection, select/create an authorized destination connection.
   An import can also leave the reference unbound; resolve it before deployment.
3. Open **Power BI Query Starter** in the imported solution. Review authentication and access settings.
   The package requests authenticated access and does not publish or enable channels on import.
   Reconfigure user authentication as required by the destination tenant.
4. Bind `poc_PowerBIQueryStarter_PowerBI` to the destination Power BI connection. Retain
   **Invoker/end-user** execution in connector nodes, never substitute a privileged maker to make
   requests succeed. Users still need appropriate Read/Build and RLS/OLS access, tenant Execute
   Queries availability, licensing and normal per-user connection consent.
5. Use a private working copy of this repository's `agent` directory. Install its dependencies and
   create the ignored resource configuration:

```powershell
Set-Location agent
python -m pip install -r requirements.txt
npm ci
Copy-Item resources.example.json resources.json
```

Populate all required placeholders with **your own** resources. For this imported starter:

| Configuration key | Value |
|---|---|
| `solutionName` | `poc_PowerBIQueryStarter` |
| `schemaName` | `poc_PowerBIQueryStarter` |
| `connectionReference` | `poc_PowerBIQueryStarter_PowerBI` |
| `agentId` | ID of the newly imported agent, not the original demonstration |
| `tenantId`, `environmentId`, `dataverseUrl` | Destination environment |
| `workspaceId`, `datasetId`, `reportId` | Your target Power BI resources |
| `connectorId` | `/providers/Microsoft.PowerApps/apis/shared_powerbi` |

6. Authenticate the Azure CLI through your approved tenant process. Use an already-authorized model
   owner to prepare and review metadata. Definition preparation currently requires existing read/write
   model access; do not grant that access to every runtime user.

```powershell
python configure.py
python prepare-model.py
python general_runtime.py
npm test
```

7. Review generated private topics, schema, connection binding, current cloud settings and the
   model-specific customization checklist below. The deployment replaces the onboarding stub/stops
   with the actual metadata gate and generic query/advice definitions. It also replaces the
   unconfigured instruction notice. Do not upload the generated files to this public-ready repository.
8. Choose an available, appropriate model in Studio and review any warnings. The package intentionally
   does not force the demonstration's preview model. The deployment preserves the target agent's
   current model/authentication settings.

```powershell
python deploy.py --capture
```

Review that captured baseline against the intended settings before applying; do not change Studio
settings between capture and apply. Concurrent changes cause deployment to stop rather than overwrite them.

```powershell
python deploy.py --apply --publish
```

9. Verify metadata retrieval and independently checked analytics as representative users. Adapt any
   direct-query regression fixtures to your own schema; the demonstration's named-field test cases
   are not universal tests for another model.
10. Configure and share the M365 Copilot channel using the destination tenant's approval process.
    Test your own published link and connection consent. Channel setup and availability do not transfer
    as a working M365 registration in this ZIP.

The CLI alternative to the import wizard is:

```powershell
pac solution import --environment "<TARGET_ENVIRONMENT_ID>" `
  --path ".\solution\PowerBIQueryStarter_unmanaged.zip" --publish-changes false
```

Use the wizard or destination-specific deployment settings when connection mapping is needed.

## Required report/model customization

**The example report's business instructions are not a universal semantic contract.** No
report-specific knowledge is bundled as if it applied to your model.

Prepare the actual tables, columns, measure names/descriptions and relationships. Establish the
meaning and grain of important metrics, creator/owner fields, grouping keys, duplicate records,
blank identities, date relationships, source time zone, fiscal/calendar periods and default filters.
Clarify which measure means "usage"; its name alone is not proof of its calculation.

Use model descriptions and reviewed guidance where possible. Add concise, model-appropriate
instructions and starter prompts in your private `agent.mcs.yml` when necessary; respect the
instruction budget. The generic source's example starters mentioning risk, tools or interactions
may not apply to your model. Do not treat report visual/page filters as automatically present in
an Execute Queries request: encode intended filters in the generated DAX.

The prepared snapshot deliberately excludes exact measure expressions, partitions, connection
material, roles and raw definitions. Where those omissions prevent reliable interpretation,
obtain an approved business definition rather than guessing. RLS/OLS and workspace roles must
be validated with the actual execution identities. Refresh metadata and republish after schema
changes. Only one configured model alias, `primary`, is supported by this starter.

## Build, inspect and evidence

From the repository root, with the agent Python requirements and Power Platform CLI installed:

```powershell
python scripts\build_solution.py
python -m unittest discover -s scripts -p "test_solution_package.py"
python scripts\validate_publication.py
```

The builder reads generic source only, never the live deployment configuration or a tenant export.
It packages source with the Power Platform SolutionPackager and records the ZIP and entry hashes in
[`package-manifest.json`](../solution/package-manifest.json). Publication validation inspects every
decompressed entry and rejects other ZIP files. ZIP headers are normalized without changing
SolutionPackager payloads so unchanged source/toolchain builds reproduce the archive. Source changes
require a new import check and an updated observation for the exact distributed ZIP; do not simply
copy an older successful verification claim onto a different package.

See the [public-safe import observation](../solution/import-verification.json). Successful import and
native parsed-contract checks are **not** a configured end-to-end query test in every target tenant.
The separate [M365 tests](m365-testing.md) apply to the configured demonstration, not this deliberately
unconfigured starter. No production readiness, universal semantic correctness or cross-tenant
entitlement guarantee is implied.

Microsoft guidance: [Export and import agents using solutions](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-export-import-bots).

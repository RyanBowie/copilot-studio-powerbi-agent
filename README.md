# Copilot Studio + Power BI

**Ask questions of a Power BI semantic model and get model-grounded DAX guidance from a standard Copilot Studio agent. No Fabric data agent is required.**

This repository packages a proof of concept, its reusable agent source, and a publication-ready documentation site. It is intentionally private while the implementation and documentation are reviewed. GitHub Pages is not enabled.

> **About the example model:** `Agent365` is the name of a **custom Power BI semantic model/report** used in this demonstration. It is **not the Microsoft Agent 365 product**, an official Agent 365 schema, or an Agent 365 product integration. The architecture is reusable with other compatible Power BI semantic models; adapt the model contract, queries, configuration, permissions, and tests to your model.

## Start here

- [Visual walkthrough](docs/index.html) — architecture, example conversations, screenshots, and caveats. Open this file locally; it has no build step.
- [Architecture and execution identity](docs/architecture.md)
- [Setup and adaptation](docs/setup.md)
- [Example prompts and output contracts](docs/examples.md)
- [Evidence and known limitations](docs/verification.md)
- [Capabilities, model discovery, and scaling limits](docs/capabilities-and-limits.md)
- [Second-report scalability experiment](docs/scalability-experiment.md)
- [Public-release checklist](docs/public-release.md)

## What this demonstrates

The agent connects to an existing Power BI semantic model using the **Power BI connector**, rather than a Fabric data agent. A curated model contract grounds its interpretation of metrics, dimensions, dates, and DAX.

**Current scope: one configured model, not automatic whole-model or multi-model discovery.** Unavailable through the approved tools does not mean absent from the underlying model. The [capability and limits guide](docs/capabilities-and-limits.md) explains model onboarding, metadata/instruction retrieval, safe response wording, and what a scalability evaluation must measure.

**Second-model evidence:** a separate authorized report resolved to a distinct model. Generic constant DAX passed, and a documented Fabric API retrieved its structural definition automatically. This proves a metadata-acquisition path, **not** automatic agent onboarding or business understanding. It used existing read/write model permissions; read-only-user parity and authored-instruction discovery remain unproven. See the [experiment and measured timings](docs/scalability-experiment.md).

The implementation preserves the smoke-test, governance-count, and top-100-agent tools and adds a **reusable analytics topic**, a **connector-free DAX-advice topic**, and a clarification topic. The source and verification guide describe the actual supported scope; this is not a promise of arbitrary natural-language access to every model.

**Execution and advice are different.** The connector executes DAX; it does not itself generate or validate the business meaning of DAX. Advice-only answers must label unexecuted DAX as a suggestion.

### Current reusable capability

| Input | Supported scope |
|---|---|
| Metric | Audited interaction turns, distinct sessions, distinct-user counts, inventory agent rows, distinct inventory environments |
| Grouping | One of total, platform, environment, environment type, region, risk, activity, agent, month, day, or client host |
| Filter | One exact categorical filter using an approved field; filter text is escaped |
| Dates | Paired inclusive dates up to 366 days, or `last30Days` resolved from the runtime UTC calendar date; unresolved date requests never fall back to all history |
| Results | 1-100 aggregate groups plus a Summary row with counts, truncation, requested dates, and separate observed-event bounds |
| DAX advice | The same model-specific compiler returns suggested DAX without calling Power BI |

Inventory metrics are current snapshots, not historical inventory. Inventory does not support audit-date or client-host slicing. Zero/blank metric groups are excluded. Multiple simultaneous categorical filters, arbitrary calculations, and automatic schema discovery are not implemented.

**Verification:** the sanitized source passes 25 offline tests, including scope explanations and relative-date boundaries. Three fixed, seven reusable, and five date-specific queries passed directly in the development model. Full chat-to-answer and live DAX-advice responses remain unverified; the latest probes did not expose an execution trace. The user's successful unfiltered top-100 observation is recorded separately.

Filtered rankings use the reusable analytics topic. The fixed top-100 tool is reserved for the original unfiltered all-history request. See [date-filter behavior and evidence](docs/date-filtering.md) for the last-30-days convention and its limits.

## Repository layout

```text
agent/                  Sanitized, environment-independent agent source
examples/               Synthetic public-safe conversations and outputs
scripts/                Packaging and documentation validation
docs/
  index.html            Self-contained, GitHub Pages-ready walkthrough
  assets/               Sanitized screenshots and editable architecture
.github/workflows/      Manual-only, public-repository-gated Pages deployment
```

Tenant-bound solution exports, credentials, connection IDs, sync caches, live transcripts, and raw customer data are deliberately excluded. This is an adaptation kit, not a preauthenticated one-click deployment.

## Architecture at a glance

![Copilot Studio interprets a question with model context, constructs a supported query, and invokes Power BI as the user. DAX guidance can return without execution.](docs/assets/architecture.svg)

## Screenshots and examples

![Actual initial Copilot Studio tool registration: governance counts, smoke test, and top 100 agents by usage.](docs/assets/tools-initial-poc.png)

This actual UI crop shows the **initial three-tool PoC**, not the later enhancement or proof of query success. See [screenshot provenance and previews](docs/screenshots.md).

<img src="docs/assets/illustrative-ranking-output.png" width="480" alt="Clearly labeled synthetic illustration of a ranked answer, with three invented demo agents and values.">

The answer illustration is **synthetic**, not a customer result or a product screenshot. It preserves the intended ranked-table presentation without publishing business data.

## Prerequisites

- Copilot Studio authoring/runtime licensing and an appropriate Power Platform environment.
- Power BI licensing appropriate to the model and workspace.
- An authenticated user with **Read and Build** access to the model.
- The tenant's **Dataset Execute Queries REST API** setting enabled.
- Power Platform data policies that permit the required connector.
- An approved model contract and a Power BI connection configured for **end-user / Invoker** execution.

Build permission is more powerful than report-viewing permission. Review the model's data access before granting it. Row-level security follows the effective execution identity and Power BI workspace role; agent instructions are not an authorization boundary.

## Local preview

Open `docs/index.html` directly, or run:

```powershell
python -m http.server 8080 --bind 127.0.0.1 --directory docs
```

Then visit `http://127.0.0.1:8080`. The site loads no external fonts, analytics, or JavaScript libraries.

Validate the publication bundle:

```powershell
python scripts\validate_publication.py
```

To rebuild the site and editable diagram after changing their source:

```powershell
python scripts\build_architecture.py
python scripts\build_site.py
```

Both builds use only the Python standard library. `scripts\preview_site.py` is an optional screenshot/interaction check that requires Python Playwright and an installed Microsoft Edge browser; it launches its own headless browser and does not use a signed-in profile.

## Publication status

**Private repository; no public site.** The Pages workflow is manual-only and refuses to deploy from a private repository. Before changing visibility, follow the release checklist, choose a license, and review all source, history, and imagery. A private repository does not guarantee that a subsequently enabled Pages site will be private.

## Microsoft references

- [Power BI connector: Run a query against a dataset](https://learn.microsoft.com/en-us/connectors/powerbi/#run-a-query-against-a-dataset)
- [Power BI Execute Queries API](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries)
- [Copilot Studio agent flows](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-flow-create)
- [Power BI remote MCP server](https://learn.microsoft.com/en-us/power-bi/developer/mcp/remote-mcp-server-get-started)

The hosted Power BI MCP server is an optional, separate route. It is not used by this connector-based implementation. Its `Generate Query` tool has Power BI Copilot entitlement/capacity requirements; these must not be confused with a requirement for a Fabric data agent.

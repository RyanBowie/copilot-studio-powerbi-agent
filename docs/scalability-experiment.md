# Second-report scalability experiment

**Completed 12 September 2026: a distinct second model accepted DAX, and its structural definition was retrieved automatically through a documented API.** This is useful portability evidence, not proof of an automatically scalable multi-model agent.

The user authorized a second report in the same workspace. It resolved to a **different semantic model** from the original custom example. Public labels below are **Model A** and **Model B**; live identifiers and report names are deliberately omitted.

No model was added to the live agent. The experiment did not change permissions, connections, cloud settings, or deployments, and did not retrieve business rows or owner identities.

## Observed results

| Test | Result | What it establishes |
|---|---|---|
| Resolve approved Report B | HTTP 200; distinct dataset identity | This is genuinely another semantic model, not another report on Model A |
| Execute a constant-only DAX query | Three HTTP 200 responses, value `1`, no response errors | The same authenticated execution transport works against Model B |
| Remote MCP model schema | Error `-32600`, artifact not found or access unavailable | This MCP connection did not retrieve metadata; does not establish model absence |
| Remote MCP report schema | Same artifact/access error | Report visual/page/filter context was not obtained |
| Fabric semantic-model `getDefinition` | HTTP 202, operation succeeded, result HTTP 200 | Automatic structural metadata retrieval is possible for this model and identity |

### DAX execution and timings

```dax
EVALUATE ROW("SmokeTest", 1)
```

| Sequential sample | HTTP status | Returned constant | Client request time |
|---|---|---|---|
| 1 | 200 | 1 | 823 ms |
| 2 | 200 | 1 | 461 ms |
| 3 | 200 | 1 | 538 ms |

A stopwatch surrounded each synchronous HTTP request through response download, excluding Azure CLI token acquisition and local JSON validation. Both HTTP status and response error fields were checked.

**These three constant-only requests are not a benchmark.** They do not measure business-query performance, load, throughput, concurrency, capacity requirements, or complete agent response time. No cold/warm-cache claim is made.

### Automatically retrieved structure

The documented operation was:

`POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels/{semanticModelId}/getDefinition?format=TMSL`

Although this uses POST, it **retrieves** a definition; it does not update the semantic model. The returned `model.bim` was parsed in memory.

| Structural object | Count |
|---|---|
| Tables | 78 |
| Columns | 694 |
| Measures | 17 |
| Relationships | 79 |

These are counts of all returned objects, including hidden or automatically generated objects. They are not counts of distinct business concepts or a claim that all those objects should enter an LLM prompt.

No manually authored schema contract was needed to retrieve and count this structure. **However, it was not integrated into the live agent or its query compiler.**

### Metadata retrieval timings

Submission took approximately **920 ms**, the status request **361 ms**, and result download **3,073 ms**. The initial response supplied `Retry-After: 20`; the test waited 20 seconds before a single status poll.

These are **separate request durations**, not total client end-to-end retrieval latency. They exclude orchestration and the polling wait. The result suggests metadata retrieval belongs in an explicitly managed acquisition/refresh path, not an assumed zero-cost step in every chat turn.

### Business descriptions and instructions

No nonempty descriptions were found on the returned model, tables, columns, measures, or relationships. Linguistic metadata was present.

A heuristic name check of annotations/extended properties did not identify explicit instruction or verified-answer fields. **This does not prove model-authored Copilot instructions or verified answers are absent.** Specialized MCP retrieval failed, and the definition format's coverage of that product-level guidance was not established.

Structural metadata is useful grounding, but it is not a substitute for missing business definitions.

## The important permission boundary

The Fabric definition API is a read operation, but its documented prerequisites include **read and write permissions on the semantic model**, plus a delegated **`SemanticModel.ReadWrite.All` or `Item.ReadWrite.All`** scope.

The test used existing authorized credentials; no permission was added. It does **not** establish that a read-only analyst or every end user can retrieve this definition. The API also documents restrictions for encrypted sensitivity labels, and the returned definition does not include the sensitivity label.

**Do not grant model-write access to every agent user just to reproduce metadata discovery.** A possible design is approved metadata preparation by an already authorized model owner, with versioned, access-controlled contracts for the runtime. That design still needs implementation and permission-specific validation; it was not tested here.

Using a Fabric API endpoint does **not** mean a Fabric data agent was created or required.

## What this proves and what it does not

**Proven for these tested resources and identities:**

- Report-to-model resolution distinguishes models.
- The query transport can execute unchanged constant DAX against a second model.
- An official API can retrieve structural metadata without hand-writing its schema first.

**Still not proven or implemented:**

- Automatic model routing or runtime onboarding.
- Portability of Model A's metric/dimension mappings to Model B.
- Discovery of all model-authored guidance.
- Correct interpretation of Model B's business measures, relationships, and filters.
- Realistic question-to-query-to-answer behavior on Model B.
- Equivalent schema access under read-only users, other tenants, or restricted models.
- Automatic schema refresh, drift handling, load capacity, or a supported model-count ceiling.

The practical conclusion is **reusable execution plus a viable structural-metadata acquisition route**, with model interpretation, governance, and runtime integration still separate responsibilities.

## Publication and evidence

The [public-safe evidence summary](../examples/second-model-evidence.json) contains only anonymized results, counts, timing methodology, and limitations. Raw definitions, field names, expressions, source/partition queries, credentials, report links, and business records are excluded.

See [capabilities and limits](capabilities-and-limits.md) for the distinction between platform limits, this PoC's deliberate scope, and unverified scaling claims.

## Microsoft references

- [Get semantic model definition: permissions, format, and limitations](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/get-semantic-model-definition)
- [Fabric long-running operations](https://learn.microsoft.com/en-us/rest/api/fabric/articles/long-running-operation)
- [Power BI Execute Queries](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries)

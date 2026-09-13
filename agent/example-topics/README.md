# Complete synthetic native topics

These files show the complete current topic definitions, not abbreviated snippets.
They are **synthetic reference artifacts**, not an export of a deployed agent.
Only the invented `Entity` and `Event` schema and placeholder resource identifiers are used.
No live metadata, identities, business rows, connection state or credentials are included.

| File | Capability | Trigger |
|---|---|---|
| `ModelMetadata.mcs.yml` | Get model metadata | Generative selection |
| `GeneratedDaxQuery.mcs.yml` | Run generated DAX | Generative selection |
| `GeneratedDaxAdvice.mcs.yml` | Compile DAX advice | Generative selection |
| `GeneratedQueryError.mcs.yml` | Generated query error | OnError |

`index.json` lists the inputs, outputs, trigger, connector operations and related source.
The three callable capabilities are native topics, not the deleted fixed connector-tool cards.
The error handler is automatic rather than an independently selected query tool.

## Inspect the complete design

- `..\agent.mcs.yml`: full agent instructions, capabilities, starters and model configuration.
- `..\general_runtime.py`: topic generation and native Power Fx guards.
- `..\generated_dax.py`: unrestricted expression boundary and bounded DAX envelope.
- `..\query_transport.py`: dynamic result typing and envelope validation.
- `..\metadata.example.json`: the same synthetic model used here.

Metadata accepts the fixed `primary` alias, a catalog/tables view and selected table names.
Query and advice accept generated table expressions, arbitrary declared output aliases, sorting,
row limit and optional paired date expressions. Their full input/output schemas are in the YAML.
Query execution uses fixed placeholder workspace/model/connection mappings and Invoker mode.
Advice does not execute the proposed business query. Error handling stops local decoder failures.

## Regenerate safely

From the example repository root, with its Python requirements installed:

```powershell
python example_topics.py
```

The script always uses built-in synthetic metadata and placeholder configuration. It does not
read `resources.json` or `model-schema.private.json`, and makes no network or deployment calls.
The files are deterministically generated from the same builders as the real implementation.

## Configure a real deployment separately

Do not import or publish these reference files unchanged. Follow the owner workflow in
`..\README.md`: configure your own private resources, prepare and review your authorized model
metadata, generate private topics, validate, then deploy deliberately. A new model requires
its own schema preparation and permission-aware validation; these examples do not grant access.

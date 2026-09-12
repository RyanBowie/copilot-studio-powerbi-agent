# Setup and adaptation

This publication bundle contains sanitized source, not a tenant-bound solution export. Do not import it and assume it is already connected to a model.

## 1. Prepare the environment

Use a nonproduction Power Platform environment with Copilot Studio access. Confirm Power BI connector availability under the environment's data policies and verify the Power BI account's licensing.

The model must permit the intended users to execute queries: Read and Build access, the tenant Execute Queries setting, and appropriate workspace/model access are required.

## 2. Establish the model contract

Document the real schema using approved metadata:

- Tables and column data types.
- Existing measures and their business definitions.
- Relationships and relevant filter directions.
- Date columns, time zones, aggregation grain, and freshness.
- Allowed metrics and dimensions.
- Sensitive fields that should not be part of the analytics interface.

The included example is a custom governance/agent-usage model named `Agent365`, not the Microsoft Agent 365 product. Do not assume its names or usage definitions exist in another model or tenant. Update query construction and grounding together. The integration pattern is reusable; the example schema is not a required product schema.

## 3. Create or clone the target agent

Create a standard Copilot Studio agent in the intended environment, or clone an existing empty one using your supported authoring workflow. Use a dedicated unmanaged solution for development.

Power Platform CLI also supports `pac copilot create` from an extracted template. An arbitrary folder of YAML is not automatically a provisioned cloud agent.

## 4. Adapt the source

The `agent` directory is a sanitized template. Replace deployment placeholders only in an ignored working copy. Preserve your cloned agent's identity and connection metadata rather than copying another deployment's IDs.

Update the model contract before enabling tools. Review each tool's declared inputs and output bindings. Do not change structured-input tools into unconstrained DAX execution without a separate validation and data-access review.

The packaged source has its own configuration workflow:

```powershell
Set-Location agent
python -m pip install -r requirements.txt
npm ci
Copy-Item resources.example.json resources.json
# Edit the ignored resources.json with your own existing-agent resource IDs.
python configure.py
npm test
```

`configure.py` only renders local source; it does not provision an agent or call the tenant. It rejects unresolved configuration placeholders. Run this in a private deployment working copy, not in the public publication source: rendering replaces placeholders in tracked templates' outputs.

Inspect the current cloud draft and preserve any user edits before running `python deploy.py`. That script targets an **existing** standard agent, obtains tokens from the configured Azure CLI account, and does not replace protected specialized tools silently. Use explicit target IDs when publishing with PAC. Do not run live deployment or verification commands merely to preview the documentation.

## 5. Connect Power BI

Create or select the user's Power BI connection and bind the relevant connection reference. Configure actions for **end-user/Invoker** execution. Do not change to maker credentials merely to eliminate an authorization prompt.

In a new test conversation, select **Allow** if the agent requests permission to use the connection. This is distinct from signing into Power BI in the environment.

## 6. Verify before publishing

Use a dedicated test user and record:

1. Smoke test returns the expected constant.
2. A known measure matches a directly checked result.
3. Top-100 ranking preserves sorting, metric meaning, and requested row count.
4. Multiple independent analytics questions reuse the generic capability.
5. Filters and date boundaries produce the expected changes.
6. DAX advice uses real schema and marks unexecuted examples clearly.
7. Unsupported fields, invalid inputs, and connector errors produce explicit responses.
8. RLS is tested with representative restricted users, not only the model owner.

Direct REST success alone is not an end-to-end agent test. Verify **question -> tool invocation -> successful result -> final answer**.

## 7. Publish and hand over

Publish only the intended agent/solution. Test again in the target channel because connection behavior can differ from the authoring test pane. Record the deployed version and known limitations without committing live transcripts or credentials.

# Screenshots and provenance

## Current published M365 and Studio captures

See the [M365 test walkthrough](m365-testing.md) for exact prompts, results and limitations.
These captures come from actual browser tests, not the synthetic illustration below.

The walkthrough opens with two real screenshot crops, not a recreated chat mockup.
`m365-prompt-intro.png` is the prompt crop `(32, 68, 622, 174)` from the reviewed
740 x 1273 `m365-ranking-redacted.png` composite. `m365-output-intro.png` is the response crop
`(0, 204, 740, 566)`, showing the first eight of twenty rows. Coordinates are left/top/right/bottom.
The crops preserve the original pixels and existing name masks; the output excerpt is explicitly
labeled and links to the complete capture. No result was regenerated or retyped for the opening.

| Asset | What it records |
|---|---|
| `m365-connection-consent.png` | Generic prompt and normal Power BI Allow/Cancel card |
| `m365-ranking-redacted.png` | Genuine top-20 composite; people's names masked, agent names/usage/dates unchanged |
| `m365-followup-redacted.png` | Genuine top-five composite; people's names masked, agent names/usage/dates unchanged |
| `m365-dax-advice.png` | Genuine advice prompt/response composite; DAX explicitly labeled unexecuted |
| `studio-current-topics.png` | Four active and three inactive topics; editor identity masked |
| `studio-query-details.png` | Actual Run generated DAX details, model description and enabled status |
| `studio-query-input.png` | Actual dynamically filled tableExpression input, including Studio's display-name warning |
| `studio-powerbi-action.png` | Actual code-editor crop: generated DAX binding, Invoker mode, dynamic output and timeout; resource IDs masked |
| `studio-model-selection.png` | Actual GPT-5 Reasoning (Preview) picker |
| `studio-current-warnings.png` | Current preview-model and formal-evaluation warnings |
| `studio-updated-starter.png` | Actual saved Analyze agent usage title/prompt in Studio; not M365 propagation evidence |

Opaque pixels remove people's names in result captures; the owner approved keeping agent names,
usage figures and dates visible. Configuration captures also redact private resource IDs and
personal identity. No replacement business values are invented.
Prompt/response composites are labeled as such; browser scrolling and a taller
viewport made the actual content visible without changing its text. Originals remain private.

## User-provided report context

`powerbi-agents-report.png` is the report screenshot the owner supplied and explicitly approved
for publication on 13 September 2026. It shows the **Copilot interactions** page of the custom
Power BI report connected to the agent-focused semantic model used for testing.

The image contains aggregate usage values, chart labels and report filters, with no visible
personal names or tenant/resource identifiers. No redaction was needed. It was re-encoded to
remove embedded image metadata; the RGB pixels were preserved unchanged.
This is not an assistant-captured test response, a synthetic illustration or proof that the
report's totals reconcile with conversation answers. Its displayed date window differs.
The report and semantic model are not included in the solution ZIP.

## User-provided Studio metadata example

`studio-metadata-example.png` was supplied and approved for use as an example by the owner on
13 September 2026. It retains the exact prompt, **Give me some details of the semantic model**,
the completed Get model metadata topic, its catalog input and the partially visible model overview.
It is a Studio test-pane capture, not a M365 channel screenshot or an independently rerun test.

The visible model table names, counts and snapshot timestamp are included with the owner's
approval. No personal names, connection secrets or tenant/resource identifiers are visible.
No redaction was needed; embedded image metadata was removed without changing RGB pixels.
This approval covers the supplied image, not publication of the complete private model snapshot.

## Actual configuration, not a historical tool inventory

![Actual Power BI connector configuration in the Studio code editor, with resource IDs masked.](assets/studio-powerbi-action.png)

The old fixed top-100 tool and empty standalone Tools screenshots have been removed from the
current walkthrough and asset set. Historical states remain in Git history, not the current gallery.
The working capabilities are native topics with embedded connector actions.

See the [visible topic contracts and genuine input/details captures](topic-and-tool-reference.md).
The input screenshot retains Studio's display-name warning. Capturing it did not change or save
runtime configuration. The model-facing description, dynamic filling, query binding and Invoker
mode are actual configuration, not a reconstructed mockup.

## Simple architecture

![Message through Copilot Studio capabilities to an answer, with Power BI execution as the user.](assets/architecture-simple.svg)

[Editable simple diagram](assets/architecture-simple.excalidraw).
This is an authored architecture illustration, not a product screenshot.

## Synthetic output illustration

![Synthetic ranking output using invented demo agent names and values](assets/illustrative-ranking-output.png)

Rendered from this repository's walkthrough. **Not a screenshot of Copilot Studio, a live answer, or execution evidence.** Every agent name and number is invented and explicitly labeled. Only three example rows appear; the live top-100 scenario should preserve its requested limit.

## Documentation-site previews

These are local renders of the documentation source, not signed-in product screenshots:

- [Light desktop preview](assets/walkthrough-light.png)
- [Dark desktop preview](assets/walkthrough-dark.png)
- [Mobile preview](assets/walkthrough-mobile.png)

## Public-release review

Later user-supplied screenshots confirmed a dated usage ranking and a contextual creator/owner
follow-up. They contain business values and, in the follow-up, real names, emails and identifiers.
They are deliberately not copied into this repository or embedded in the site. The successful
scenarios are documented in [verification](verification.md) without those values. The synthetic
ranking illustration remains labeled synthetic; it is not substituted as photographic proof.

The owner approved public release after the current and historical imagery was reviewed, then
requested names-only result redaction. The reviewed M365 captures now retain actual agent names,
usage figures and dates, with no substitute values. Earlier user-supplied screenshots described
above remain private. Continue reviewing
new images at full resolution before publication. Microsoft product UI and trademarks remain their
owners' property; no additional intellectual-property license is implied by public visibility.

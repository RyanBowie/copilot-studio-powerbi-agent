# Public release review

The owner authorized public repository and GitHub Pages publication on **13 September 2026**,
subject to anonymizing screenshots and reviewing the solution. The website documents the agent;
it does not host a connected agent or provide access to the demonstration's Power BI data.

## Initial release review performed

| Area | Scope and result |
|---|---|
| Existing Git history | All 12 reachable commits through `63e7cf9`; 284 unique text objects/archive entries scanned |
| Historical images | 48 unique images, including images embedded in HTML; 238 tiles processed with local Windows OCR, not an external service |
| Initial-release screenshots | Visual review of real captures and redactions; at that release, names, creators, business values and editor identity were covered by opaque pixels |
| Text scan findings | Two email-pattern matches were `parentbotid@odata.bind`, an OData property name, not personal email addresses |
| Image scan findings | No identity/tenant pattern hits; no flagged comment, description, XMP or EXIF payloads |
| Unknown binary artifacts | None found in the history inventory |
| Solution ZIP | Every decompressed entry inspected and matched against its manifest/source; no tenant IDs, live connection binding, customer schema or credentials |
| Download integrity | Unchanged import-verified ZIP; SHA-256 recorded in the package manifest and import observation |

At the initial release, the real ranking and follow-up images contained **redacted result cells**,
not invented replacement values. Other numeric rows/names were labeled synthetic illustrations.
Generic prompts, declared date ranges and response-shape counts remain visible to explain the tests.
The public GitHub owner name and normal public commit attribution are intentionally retained.
Original captures, private audit/OCR output, deployment configuration and transcripts are not published.

The history scan found no private-content removal requiring a history rewrite. Pattern matching and
OCR support, but do not replace, human review; this is not a guarantee that every possible sensitive
fact can be detected automatically.

## Owner-approved screenshot update - 13 September 2026

The owner subsequently requested **only people's names** be masked in result screenshots.
The ranking and follow-up derivatives now retain actual agent names, usage figures and dates.
Opaque masks cover 17 and five personal-name occurrences respectively; every response pixel
outside the masks was compared against the private original and found unchanged. System labels
and blank entries are retained. No substitute values or reconstructed answers are used.

The historical fixed-tool and empty standalone Tools images were removed from the current asset
set and visible documentation. New genuine Studio crops show the topic details, dynamically
filled DAX input and embedded Power BI action. Private workspace/model IDs are masked in the
action; no live runtime settings were edited or saved. The input's display-name warning remains
visible rather than being cosmetically removed. An authored simple architecture diagram and
visible topic contracts complement the captures; diagrams are not execution evidence.

This update does not expand the initial history-scan counts above. Unredacted originals, private
OCR output and mask specifications remain excluded. The solution ZIP is unchanged.

The owner also explicitly supplied and approved `powerbi-agents-report.png` as report context
for the tested semantic model containing agents. Its visible aggregate figures and filters are
retained. No personal names or tenant/resource identifiers are visible; image metadata was removed
without changing RGB pixels. This supplied report image is separate from the browser-observed
conversation evidence and does not reconcile totals across different date windows.

## Solution review boundary

The ZIP contains a separate **unconfigured unmanaged starter**, not the working tenant export.
Its import was already verified in an authorized development environment. It remains unpublished,
with no configured channels or bound connection. Metadata explains required setup rather than
probing an example model; query and advice paths stop before a connector can execute.
Package invariants and native parsed-contract checks are documented in the
[import guide](solution-import.md) and [import observation](../solution/import-verification.json).

Runtime query generation still requires model-specific metadata, business definitions, destination
permissions and correctness testing. This release review is **not** a production security
certification, formal Studio evaluation, cross-tenant query test or resolution of the deferred
ranking-accuracy concern. No model rights, working runtime settings or channel permissions were
changed to publish this website.

## Future release checklist

- [ ] Confirm ownership and permission to publish all code, documentation, and images.
- [ ] Choose and add a license if granting reuse rights. No open-source license has been selected;
      public visibility alone does not grant additional reuse rights.
- [ ] Review every tracked file and Git history, not just the latest working tree.
- [ ] Remove credentials, token-bearing links, connection bindings, `.mcs` state, tenant exports, live transcripts, and raw model data.
- [ ] Confirm every environment, model, workspace, report, connection, user, and agent identifier is a placeholder or harmless documented schema name.
- [ ] Review screenshots at full resolution for account names, tenant URLs, organization details, identifiers, and business data.
- [ ] Keep sample names and numeric results clearly labeled synthetic.
- [ ] Confirm architecture descriptions match the deployed implementation and distinguish enforced controls from instructions.
- [ ] Recheck implementation status, direct-query versus chat evidence, limitations, and Microsoft preview/licensing documentation.
- [ ] Run `python scripts\validate_publication.py` and inspect the rendered site in light and dark themes.
- [ ] Inspect every decompressed starter ZIP entry against its unpacked source and checksum manifest;
      retain its unconfigured stop-before-query behavior and exclude all tenant-bound exports.
- [ ] Test adaptation with a clean nonproduction environment and synthetic model.
- [ ] Test restricted-user permissions and RLS separately from maker testing.
- [ ] Review dependencies and GitHub Actions versions.
- [ ] Review the included unmanaged starter ZIP and import/customization caveats before public distribution;
      development import success does not establish configured cross-tenant query behavior.
- [ ] Treat publication as disclosure; obtain approval for any newly included private material.
- [ ] Configure **Settings -> Pages -> Source: GitHub Actions**, then manually run the Pages workflow.

If sensitive material ever entered history, simply deleting it from the latest commit is insufficient. Remediate the exposure before publication.

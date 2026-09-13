# Before making this repository public

The repository starts private. Its Pages workflow is deliberately manual-only and gated to public repositories. **No public deployment should happen during preparation.**

- [ ] Confirm ownership and permission to publish all code, documentation, and images.
- [ ] Choose and add a license. No open-source license is assumed by this private draft.
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
- [ ] Change repository visibility only after review and explicit owner approval.
- [ ] Configure **Settings -> Pages -> Source: GitHub Actions**, then manually run the Pages workflow.

If sensitive material ever entered history, simply deleting it from the latest commit is insufficient. Remediate the exposure before publication.

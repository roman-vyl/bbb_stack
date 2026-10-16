## Decisions

### D1. Separate mount path in Research

The catalog is mounted at `/runtime-specs`, not under `/data`, so that the Research
data root and the Runtime catalog stay separate directories with separate mount modes.
The export lock file stays in Research's own `/data/analysis`, not in the catalog.

### D2. Runtime stays read-only

The `strategy-runtime` mount is not touched. Read-only for Runtime is the permission
boundary that makes it a pure consumer of the catalog.

### D3. Mount and variable ship before the image

`RESEARCH_RUNTIME_SPECS_PATH` is ignored by the currently pinned Research image
(`extra="ignore"`), so this change can merge before the image with the export route is
pinned. The route becomes usable only after a separate pin-bump PR.

### D4. Protection is verified, not assumed

Each check in `tasks.md` section 2 is run on the Mac and its output is recorded in
`docs/verification-research-runtime-export-v1.md` before the export is used. A failed
check blocks use of the feature and is reported; it is not worked around in this change.

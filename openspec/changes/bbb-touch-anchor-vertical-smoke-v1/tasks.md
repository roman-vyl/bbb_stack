## 1. Baseline and fixture discovery

- [x] Confirm `bbb-live-stack-v1` is merged into `main` and update local `main`.
- [x] Create branch `bbb-touch-anchor-vertical-smoke-v1`.
- [x] Record exact main SHAs for `bbb_stack`, MDS, Strategy Engine, Strategy Runtime, and ABI.
- [x] Find and reuse the existing Strategy Engine EMA Pullback touch-anchor fixture.
- [x] Confirm Runtime deployment JSON format and committed-bar webhook behavior.
- [x] Confirm MDS has no deterministic production HTTP seam for injecting one realtime committed bar.
- [x] Confirm ABI dry-run entry-package semantics before running the stack.

## 2. Smoke artifact

- [x] Add a system-only smoke script in `bbb_stack`.
- [x] Prepare an isolated `BBB_DATA_ROOT`.
- [x] Seed MDS deterministic data through existing MDS application/storage ingestion.
- [x] Trigger Runtime through the closed-bar webhook as a clearly labeled one-boundary injection.
- [x] Capture Runtime journal, Engine desired-entry result, ABI mode, ABI correlation, and logs.

## 3. Verification

- [x] Run `docker compose config`.
- [x] Build and run all four services.
- [x] Confirm all services are healthy/ready.
- [ ] Verify MDS data window through MDS HTTP. Blocked: production MDS startup
  reconciliation marked the finite fixture stream non-ready/failed before the
  Engine boundary.
- [ ] Verify Engine produces the singular touch-anchor desired entry.
- [ ] Verify Runtime dispatches to Engine and ABI.
- [ ] Verify ABI safe-mode acknowledgement/error and correlation behavior.
- [ ] Verify no service repo modifications.
- [ ] Run `git diff --check`.
- [ ] Validate OpenSpec if CLI is available.

## 4. Closeout

- [x] Update `docs/verification-touch-anchor-vertical-v1.md` with real results.
- [ ] Archive the OpenSpec change if the system verification reaches its accepted safe-mode boundary.
- [ ] Commit and push `bbb_stack`.

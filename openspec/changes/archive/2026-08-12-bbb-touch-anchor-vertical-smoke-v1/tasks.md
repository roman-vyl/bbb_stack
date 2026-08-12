## 1. Baseline and fixture discovery

- [x] Confirm `bbb-live-stack-v1` is merged into `main` and update local `main`.
- [x] Create branch `bbb-touch-anchor-vertical-smoke-v1`.
- [x] Record exact main SHAs for `bbb_stack`, MDS, Strategy Engine, Strategy Runtime, and ABI.
- [x] Find and reuse the existing Strategy Engine EMA Pullback touch-anchor fixture.
- [x] Confirm Runtime deployment JSON format and committed-bar webhook behavior.
- [x] Confirm MDS can be pointed at deterministic REST/WS upstreams through
  `MDS_REST_BASE_URL` and `MDS_WEBSOCKET_URL`.
- [x] Confirm ABI dry-run entry-package semantics before running the stack.

## 2. Smoke artifact

- [x] Add a system-only smoke script in `bbb_stack`.
- [x] Add a smoke-only Bybit-compatible REST/WS fixture.
- [x] Add a smoke-only Compose override without changing base `docker-compose.yml`.
- [x] Prepare an isolated `BBB_DATA_ROOT`.
- [x] Drive MDS lower-bound discovery, historical reconciliation, and readiness
  through fixture REST.
- [x] Trigger Runtime through genuine MDS committed-bar notifier from fixture WS.
- [x] Capture Runtime journal, Engine desired-entry result, ABI mode, ABI correlation, and logs.

## 3. Verification

- [x] Run `docker compose config`.
- [x] Build and run all four real BBB services plus the smoke-only fixture.
- [x] Confirm all services are healthy/ready.
- [x] Verify MDS data window through MDS HTTP.
- [x] Verify Engine produces the singular touch-anchor desired entry.
- [x] Verify Runtime dispatches to Engine and ABI.
- [x] Verify ABI safe-mode acknowledgement/error and correlation behavior.
- [x] Verify no service repo modifications.
- [x] Run `git diff --check`.
- [x] Validate OpenSpec if CLI is available.

## 4. Closeout

- [x] Update `docs/verification-touch-anchor-vertical-v1.md` with real results.
- [x] Archive the OpenSpec change now that the system verification reached its accepted safe-mode boundary.
- [x] Commit and push `bbb_stack`.

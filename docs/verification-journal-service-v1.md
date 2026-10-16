# Verification: Journal Service wiring (bbb-journal-service-wiring-v1)

Checks of `openspec/changes/bbb-journal-service-wiring-v1/tasks.md` section 2, recorded on
the owner's Mac on 2026-10-16 (~17:27 UTC).

Setup:

- bbb_stack branch `claude/project-thread-kyrwe7` at `a215676` (worktree), `docker-compose.yml` only.
- Image built locally from `journal_service` main `42c51e2` (`bbb-stack/journal-service:local`);
  nothing pulled from GHCR.
- `BBB_DATA_ROOT=/Users/mcroma/BBB_data`, compose project `bbb_stack`.
- Command: `docker compose -p bbb_stack -f docker-compose.yml up -d --no-deps journal-service`.
- Only `journal-service` was started; Runtime, ABI and all strategies were left off. The already
  running Market Data Service, Strategy Engine and Research Service were not touched.

Source: `strategy-runtime/journal/runtime.jsonl`, 83,586,207 bytes, 195,584 lines, last written
2026-10-04. Event types in it: `strategy_cycle_dispatch_succeeded` 151,174,
`committed_bar_orchestration_started` 14,999, `committed_bar_orchestration_completed` 14,990,
`strategy_cycle_dispatch_failed` 14,421. It contains no `live_entry_evaluated` events, so the
expected ingest result is 0 stored and every line skipped.

| Check | Result | Evidence |
| --- | --- | --- |
| 2.1 Starts and becomes healthy (`--no-deps`) | pass | Container `Up (healthy)` within 15 s; `/health` returns `status: ok`. |
| 2.2 Existing `runtime.jsonl` scanned, cursor at EOF, DB created | pass | First run: stored 0, skipped 195,584 (= line count), malformed 0; `cursor_offset` 83,586,207 = file size. `journal.sqlite3` created in `/Users/mcroma/BBB_data/journal/`. |
| 2.3 Source mount read-only, `/data` writable | pass | `touch /sources/runtime/x` gives `Read-only file system`; `/data` accepts a write; root fs also read-only (`ReadonlyRootfs=true`). Mounts: source `RW=false`, `/data` `RW=true`. |
| 2.4 Restart resumes, no duplicates, SQLite WAL works on the bind mount | pass (no rows to duplicate) | `PRAGMA journal_mode` = `wal`; `-wal`/`-shm` files appear on the Docker Desktop bind mount and the WAL is checkpointed on stop. After `docker restart`: `integrity_check` ok, cursor unchanged (dev 43, ino 213105, offset 83,586,207), counters since start 0/0/0, so the file was not re-read. `events` = 0 before and after. Duplicate protection on real rows is not exercised because the source has no `live_entry_evaluated` events. |
| 2.5 Stopping it leaves other services untouched | pass | `docker stop` of journal-service: Market Data Service (8080), Strategy Engine (8090), Research Service (8095) stayed `Up (healthy)`, `/health` 200 each. Restarted afterwards; resumes at EOF. |
| 2.6 Published on `127.0.0.1:8097` only | pass | `PortBindings` `127.0.0.1:8097`; host listener only on `127.0.0.1:8097`. |

Not covered: ingest and dedup of actual `live_entry_evaluated` events (needs Runtime to produce
them), and a replaced `runtime.jsonl` (new inode).

## Smoke with one real strategy (2026-10-16, 17:35–17:50 UTC)

Passed. ABI `3d46c76` in dry-run (`dryRun: true`, `liveTradingEnabled: false`, testnet, no API
key); Runtime built locally from strategy_runtime `15e7fed`; only `journal-smoke-eth-ema500`
enabled (ETHUSDT.P 5m, EMA 200/500/1000), the 32 `loadtest-*` specs disabled. Three real bars
(open 17:35, 17:40, 17:45) arrived from MDS without manual webhooks; each produced one
`live_entry_evaluated` (`desired_entry: null`). The Central Journal stored 3, skipped 15,
malformed 0, cursor at end of file, 3 distinct `event_id`. ABI and Runtime were stopped afterwards.

Found on the way, not part of this change: `runtime_state.jsonl` still holds 28 old
loadtest/acceptance instances with open trade cycles; Runtime keeps retrying their recovery
against ABI (422 on recovery-state, 500 on close). To be cleaned up before demo or live.

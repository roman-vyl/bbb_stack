# Touch Anchor Vertical Smoke V1 Verification

Status: blocked at MDS finite-fixture readiness boundary.

This report belongs to `bbb-touch-anchor-vertical-smoke-v1` and records the
first safe-mode business vertical smoke through the ratified four-service stack.

## Baselines

- bbb_stack: `2304ef19f79c988c7f34dada37146b04b88c8057`
- market_data_service: `0389837df03e48d0ccc17b4255e1f97a33cd5277`
- strategy_engine: `4136d298531ae05c926df7aec04649c9e047c0d9`
- strategy_runtime: `d1872be4531b5a2916d439fa00af9c08d9466220`
- abi_executor_bot: `5420c289590337d8d0e011b900bc2b2c177cff8f`

## Fixture

- Strategy: `ema_pullback`
- Existing fixture source: Strategy Engine `tests/test_live_entry_projection.py`
- Ticker/timeframe: `BTCUSDT.P` / `5m`
- Trigger bar: `open_time_ms=3300000`
- Intended trigger mode: one-boundary Runtime webhook injection. The run did
  not reach trigger because MDS rejected the deterministic window as non-ready.

## Results

Command:

```text
/Users/mcroma/.local/bin/python3.12 scripts/smoke_touch_anchor_vertical.py
```

Isolated data root:

```text
/private/tmp/bbb-touch-anchor-smoke-mk846byb
```

Observed:

- `docker compose config` completed.
- `docker compose up -d --build` completed.
- The four-service stack reached the script's running/healthy gate.
- MDS `/health`, Engine `/health`, Runtime `/health/live`,
  Runtime `/health/ready`, ABI `/health`, and ABI `/execution/mode` were
  reachable before the MDS window assertion.
- ABI safe mode was confirmed:
  `dryRun=true`, `liveTradingEnabled=false`, `bybitEnvironment=testnet`,
  `canExecuteLive=false`, no API key/secret configured.
- The script seeded `BTCUSDT.P/5m` candles through MDS
  `IngestObservedCandle` and `SqliteUnitOfWork`, not direct SQL inserts.
- MDS `/v1/candles?ticker=BTCUSDT.P&timeframe=5m&from_ms=0&to_ms=3600000`
  returned:

```json
{"detail":"BTCUSDT.P:5m is failed","error":"stream_not_ready"}
```

Post-run MDS SQLite state for the target stream:

```text
BTCUSDT.P|5m|failed|0|3300000|runtime_failed|HistoricalLowerBoundUnavailable
```

Structured smoke output from the rerun:

```json
{
  "boundary": "MDS_STREAM_NOT_READY_FOR_FINITE_FIXTURE",
  "mds_window": {
    "body": {
      "detail": "BTCUSDT.P:5m is failed",
      "error": "stream_not_ready"
    },
    "status": 409
  },
  "ticker": "BTCUSDT.P",
  "timeframe": "5m",
  "trigger_mode": "one-boundary Runtime webhook injection",
  "trigger_open_time_ms": 3300000
}
```

MDS also registered the full configured catalog and began full-history
reconciliation for other configured streams during startup. The target finite
fixture used timestamp `0`, which is valid for the existing Engine unit fixture
but invalid for MDS production historical lower-bound reconciliation against
Bybit. Even with a shifted finite fixture, current MDS startup semantics degrade
persisted ready state and require full configured-history reconciliation before
consumer `/v1/candles` reads become ready.

## Boundary

First failing boundary:

```text
MDS_STREAM_NOT_READY_FOR_FINITE_FIXTURE
```

The run did not reach Runtime closed-bar trigger, Engine live-entry dispatch, or
ABI entry-package. No service code was changed.

## Required Follow-Up

A separate MDS/service-level or approved testability change is needed before a
clean deterministic four-service business vertical smoke can run without direct
DB lifecycle overrides. Candidate boundary to specify there:

- a supported deterministic fixture/import mode that can make a bounded
  isolated historical window consumer-ready for system tests; or
- an approved MDS test seam for realtime committed-bar notification that does
  not require full Bybit history reconciliation.

## Verdict

`MDS_STREAM_NOT_READY_FOR_FINITE_FIXTURE`

# Touch Anchor Vertical Smoke V1 Verification

Status: passed to the maximum safe ABI boundary.

This report belongs to `bbb-touch-anchor-vertical-smoke-v1` and records the
first MDS-originated business vertical smoke through the ratified four-service
stack plus a smoke-only Bybit-compatible upstream fixture.

## Baselines

- bbb_stack branch base: `1d8ea1155428a43e8e23c8335122e6476bd4f3f0`
- market_data_service: `0389837df03e48d0ccc17b4255e1f97a33cd5277`
- strategy_engine: `4136d298531ae05c926df7aec04649c9e047c0d9`
- strategy_runtime: `d1872be4531b5a2916d439fa00af9c08d9466220`
- abi_executor_bot: `5420c289590337d8d0e011b900bc2b2c177cff8f`

No service repo source, Dockerfile, API contract, or canonical spec was
modified.

## Fixture

- Strategy: `ema_pullback`
- Existing fixture source: Strategy Engine `tests/test_live_entry_projection.py`
- Smoke upstream: `bybit-fixture`, added only by
  `docker-compose.touch-anchor-smoke.yml`
- MDS external config:
  `MDS_REST_BASE_URL=http://bybit-fixture:8088`,
  `MDS_WEBSOCKET_URL=ws://bybit-fixture:8089/v5/public/linear`
- Ticker/timeframe: `BTCUSDT.P` / `5m`
- REST subset served: `/v5/market/instruments-info`,
  `/v5/market/kline`
- WebSocket subset served: subscribe ack and confirmed
  `kline.5.BTCUSDT`

## Run

Command:

```text
/Users/mcroma/.local/bin/python3.12 scripts/smoke_touch_anchor_vertical.py
```

Isolated data root:

```text
/private/tmp/bbb-touch-anchor-smoke-_fzq1eif
```

Fixture timing:

```text
launch_time_ms=1786506600000
max_rest_open_served=1786509900000
trigger_open_time_ms=1786510200000
```

Trigger mode:

```text
MDS-originated via fixture WebSocket -> MDS notifier
```

## Health

- MDS `/health`: healthy
- MDS `/readiness`: ready, stream `BTCUSDT.P:5m`, durable `ready`,
  realtime `live`, `data_ready=true`
- Engine `/health`: ok
- Runtime `/health/live`: live
- Runtime `/health/ready`: ready
- ABI `/health`: ok
- ABI `/execution/mode`: `dryRun=true`, `liveTradingEnabled=false`,
  `bybitEnvironment=testnet`, `canExecuteLive=false`, no API key/secret

## MDS Window

MDS served the Engine-read path for the exact smoke range:

```text
from_ms=1786506600000
to_ms=1786510500000
candle_count=13
market_data_hash=6dd8612ad525dbdd666e8e4b51e5119d7e87ee0d34f12658c8c5d653ecba1b2f
```

MDS reached this through production lower-bound discovery, historical
reconciliation, continuity readiness, realtime admission, and a genuine
confirmed WebSocket commit from the fixture.

## Engine Desired Entry

Runtime reached Engine live-entry; an additional direct observation call to the
same Engine endpoint returned:

```json
{
  "side": "long",
  "source_plan_bar_open_time_ms": 1786510200000,
  "planned_entry_price": "12.000244140625",
  "initial_stop_price": "11.750244140625",
  "initial_take_price": "12.500244140625",
  "locked_exit_profile": "neutral"
}
```

## Runtime Journal

Runtime journal for the trigger bar:

```text
committed_bar_orchestration_started
strategy_cycle_dispatch_failed error="ABI entry-package public error: internal_error"
committed_bar_orchestration_completed selected=1 attempted=1 succeeded=0 failed=1
```

Strategy instance:

```text
ema_pullback:bab740a8e7e711731f9b08d0
```

Trade cycle:

```text
a02e0d77-ff23-4ae4-bebf-e4d0ae409684
```

## ABI Boundary

ABI production entry-package path was reached in safe mode. Correlation record:

```text
strategy_instance_id=ema_pullback:bab740a8e7e711731f9b08d0
trade_cycle_id=a02e0d77-ff23-4ae4-bebf-e4d0ae409684
status=pending_create
pending_action=create
order_link_id=abi-ep-aad881511bf0a805bde0
exchange_order_id=null
```

ABI did not return `entry_package_applied` because the base stack correctly
blocks live execution in dry-run/no-credential mode. Runtime therefore did not
save `AppliedEntryPackage`. No fill/open-position continuation was attempted or
fabricated.

## Second Bar

Not run. The next lifecycle gate requires an exchange-confirmed create/fill or
a later demo/live execution path. Safe ABI mode stops at the entry-package
application boundary.

## Verification

- `docker compose config`: passed through the smoke script
- `docker compose up -d --build`: passed through the smoke script
- Full stack healthy/ready: passed
- MDS-originated trigger: passed
- Runtime -> Engine -> ABI chain: passed to safe ABI boundary
- Service repos modified: no
- Forced shutdown: no; script executed normal `docker compose down`

## Verdict

`TOUCH_ANCHOR_VERTICAL_SMOKE_PASS`

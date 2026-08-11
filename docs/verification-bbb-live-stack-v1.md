# bbb-live-stack-v1 Verification

Date: 2026-08-11

## Service Baselines

- `roman-vyl/market_data_service` `origin/main`: `0389837df03e48d0ccc17b4255e1f97a33cd5277`
- `roman-vyl/strategy_engine` `origin/main`: `4136d298531ae05c926df7aec04649c9e047c0d9`
- `roman-vyl/strategy_runtime` `origin/main`: `d1872be4531b5a2916d439fa00af9c08d9466220`
- `roman-vyl/abi_executor_bot` `origin/main`: `5420c289590337d8d0e011b900bc2b2c177cff8f`

These match the requested expected baseline after refreshing remote refs.

The existing sibling service worktrees were not modified. Verification used clean
temporary clones in `/private/tmp/bbb-stack-src` checked out at the baseline SHAs.

## Environment Blocker Removed

The required host ports were occupied by old BBB standalone containers:

- `market-data-service`
  - Image: `market_data_service-market-data-service`
  - Compose project: `market_data_service`
  - Compose working dir: `/Users/mcroma/BBB_project/market_data_service`
  - Port: `127.0.0.1:8080->8080/tcp`
  - Mounts: MDS `markets.toml` read-only and `/Users/mcroma/BBB_data/market-data` to `/data`
- `strategy-runtime`
  - Image: `strategy-runtime:local`
  - Compose labels: none
  - Ports: `0.0.0.0:8093->8093/tcp`, `[::]:8093->8093/tcp`
  - Mounts: `/Users/mcroma/BBB_project/strategy_runtime/var/specs` to `/runtime/specs` read-only and `/Users/mcroma/BBB_project/strategy_runtime/var/journal` to `/runtime/journal`

Only these two confirmed old BBB standalone containers were stopped with
`docker stop market-data-service strategy-runtime`. No volumes or data roots were
removed.

## Smoke Data Root

Smoke root: `/private/tmp/bbb-live-stack-v1-smoke`

Created host directories:

- `/private/tmp/bbb-live-stack-v1-smoke/market-data`
- `/private/tmp/bbb-live-stack-v1-smoke/strategy-runtime/specs`
- `/private/tmp/bbb-live-stack-v1-smoke/strategy-runtime/journal`
- `/private/tmp/bbb-live-stack-v1-smoke/abi`

No `chmod 777` was used.

## Compose and Build

`docker compose config` with `BBB_DATA_ROOT` passed.

`docker compose config` without `BBB_DATA_ROOT` failed non-zero with
`BBB_DATA_ROOT must be set`.

`docker compose up -d --build` built and started all four images:

- `bbb-stack/market-data-service:local`
- `bbb-stack/strategy-engine:local`
- `bbb-stack/strategy-runtime:local`
- `bbb-stack/abi:local`

The first Runtime start exposed a missing required Runtime timeout configuration.
The stack Compose was updated to preserve the existing Runtime standalone defaults:

- `RUNTIME_STRATEGY_ENGINE_TIMEOUT_SECONDS=5`
- `RUNTIME_ABI_OPEN_POSITION_TIMEOUT_SECONDS=5`
- `RUNTIME_ABI_ENTRY_PACKAGE_TIMEOUT_SECONDS=5`
- `RUNTIME_ABI_POSITION_MANAGEMENT_TIMEOUT_SECONDS=5`
- `RUNTIME_COMMITTED_BAR_QUEUE_CAPACITY=256`

No ports, DNS names, dependency graph, mounts, or application repositories were changed.

## Health Matrix

All four containers ran simultaneously and reached healthy state.

- MDS `GET http://127.0.0.1:8080/health`: `{"fatal_error": null, "status": "healthy"}`
- Engine `GET http://127.0.0.1:8090/health`: `{"status":"ok","service":"strategy_engine"}`
- Runtime `GET http://127.0.0.1:8093/health/live`: `{"status":"live"}`
- Runtime `GET http://127.0.0.1:8093/health/ready`: `{"status":"ready"}`
- ABI `GET http://127.0.0.1:8787/health`: `ok=true`, `dryRun=true`, `liveTradingEnabled=false`, `bybitEnvironment=testnet`, `bybitApiKeyConfigured=false`
- ABI `GET http://127.0.0.1:8787/execution/mode`: `dryRun=true`, `liveTradingEnabled=false`, `bybitEnvironment=testnet`, `canExecuteLive=false`

ABI live execution was unavailable with blocked reasons:

- `ABI_DRY_RUN must be false`
- `ABI_LIVE_TRADING_ENABLED must be true`
- `BYBIT_API_KEY is required`
- `BYBIT_API_SECRET is required`

## Wiring Matrix

Container env inspection confirmed:

- Engine: `STRATEGY_ENGINE_MDS_BASE_URL=http://market-data-service:8080`
- Runtime: `RUNTIME_STRATEGY_ENGINE_BASE_URL=http://strategy-engine:8090`
- Runtime: `RUNTIME_ABI_BASE_URL=http://abi:8787`
- MDS: `MDS_RUNTIME_WEBHOOK_ENABLED=true`
- MDS: `MDS_STRATEGY_RUNTIME_BASE_URL=http://strategy-runtime:8093`

No `host.docker.internal` was present in the rendered Compose or inspected stack env.

## Filesystem and Network Contract

- MDS
  - Root filesystem: read-only
  - User: `10001:10001`
  - Port: `127.0.0.1:8080->8080/tcp`
  - Mounts:
    - `/private/tmp/bbb-stack-src/market_data_service/config/markets.toml` -> `/app/config/markets.toml`, read-only
    - `/private/tmp/bbb-live-stack-v1-smoke/market-data` -> `/data`, writable
  - Writable probe in `/data`: passed
- Strategy Engine
  - Root filesystem: read-only
  - User: `10001:10001`
  - Port: `127.0.0.1:8090->8090/tcp`
  - Mounts: none
- Strategy Runtime
  - Root filesystem: read-only
  - User: `strategy-runtime`
  - Port: `127.0.0.1:8093->8093/tcp`
  - Mounts:
    - `/private/tmp/bbb-live-stack-v1-smoke/strategy-runtime/specs` -> `/runtime/specs`, read-only
    - `/private/tmp/bbb-live-stack-v1-smoke/strategy-runtime/journal` -> `/runtime/journal`, writable
  - Writable probe in `/runtime/journal`: passed
  - Write probe in `/runtime/specs`: failed with `Read-only file system`, as expected
- ABI
  - Root filesystem: not read-only, preserving ABI service contract
  - User: `node`
  - Port: `127.0.0.1:8787->8787/tcp`
  - Mounts:
    - `/private/tmp/bbb-live-stack-v1-smoke/abi` -> `/app/var`, writable
  - Writable probe in `/app/var`: passed

No service published host-side ports on `0.0.0.0`.

## Startup Order Evidence

Compose output and inspect timestamps confirmed:

- ABI started at `2026-08-11T19:09:22.569135013Z`
- Engine started at `2026-08-11T19:09:22.564687138Z`
- Runtime started at `2026-08-11T19:09:28.165804209Z`
- MDS started at `2026-08-11T19:09:33.766989295Z`

Compose events showed Runtime had
`com.docker.compose.depends_on=abi:service_healthy:false,strategy-engine:service_healthy:false`
and MDS had `com.docker.compose.depends_on=strategy-runtime:service_healthy:false`.

Observable requirement passed: MDS was not started until after Runtime reached the
Compose healthy gate.

## Restart and Persistence

After a normal `docker compose down`, the same `BBB_DATA_ROOT` was reused with
`docker compose up -d`.

The stack reached healthy state again:

- MDS healthy
- Engine healthy
- Runtime healthy
- ABI healthy

Persistent host contents survived recreate:

- MDS generated `/private/tmp/bbb-live-stack-v1-smoke/market-data/market.sqlite3`
  and it remained after restart.
- Runtime generated
  `/private/tmp/bbb-live-stack-v1-smoke/strategy-runtime/journal/runtime.jsonl`
  and it remained after restart.
- ABI mounted `/private/tmp/bbb-live-stack-v1-smoke/abi` remained present and
  writable. No ABI correlation file was generated during this topology-only
  smoke, and no business operation was invented to create one.

Runtime StrategyInstanceRuntimeState persistence was intentionally not tested.

## Shutdown

Final `docker compose down` completed normally:

- Containers showed `Stopping`, then `Stopped`, then `Removing`.
- No forced kill appeared in the output.
- The Compose network was removed.
- Persistent host data under `/private/tmp/bbb-live-stack-v1-smoke` remained.

## OpenSpec Status

`bbb-live-stack-v1` verification passed and the change was archived into the
canonical `bbb-live-stack` spec.

Active OpenSpec changes after archive: `0`.

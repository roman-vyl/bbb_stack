# BBB Stack

System-level deployment and integration repository for the BBB live stack.

This repository owns Docker Compose wiring, system configuration, lifecycle ordering,
system smoke checks, and system-level OpenSpec only. It does not vendor service source,
service Dockerfiles, or application contracts.

## Deployed image versions

[`deploy/images.env`](deploy/images.env) is the source of truth for which
six immutable GHCR images (tagged by full Git commit SHA) make up the
current BBB deployment. Update it via a normal PR after a service's
CI has published a new image on its `main`.

## Usage (local source build, for development)

Set shared/config and trading roots, plus the trusted account UID, before rendering or starting the stack:

```sh
export BBB_DATA_ROOT=/tmp/bbb-live-stack
export BBB_TRADING_DATA_ROOT=/tmp/bbb-live-stack
export ABI_EXPECTED_BYBIT_UID=<trusted-demo-uid>
docker compose config
docker compose up --build
```

The base composition is safe by default: ABI runs dry-run, live trading is
disabled, and no exchange credential file is loaded.

For Demo deployment, use the existing late authorization path: configure a trusted
`ABI_EXPECTED_BYBIT_UID` and select `BYBIT_ENV=demo` in the common Compose. ABI starts LOCKED;
keys are delivered separately through age/stdin/Unix socket by
`scripts/authorize_abi.py`, without restart. Do not create plaintext key env files or
set API keys in Compose/runner environment.

The service build contexts default to sibling repositories:

- `MDS_REPO_PATH=../market_data_service`
- `STRATEGY_ENGINE_REPO_PATH=../strategy_engine`
- `STRATEGY_RUNTIME_REPO_PATH=../strategy_runtime`
- `ABI_REPO_PATH=../abi_executor_bot`
- `RESEARCH_REPO_PATH=../research_service`
- `JOURNAL_SERVICE_REPO_PATH=../journal_service`

`research-service` is now a full deployment-parity member alongside the
other four: `docker-compose.deploy.yml` pins it to `${RESEARCH_IMAGE}`
(`platform: linux/amd64`, same as the others), `deploy/images.env` carries
its immutable GHCR SHA tag, and the `Deploy BBB` workflow pulls it,
waits for it to become healthy, and verifies its running image ref
alongside the other four services.

## Market data instrument list

`market-data-service` reads its instrument list from `${BBB_DATA_ROOT}/mds/markets.toml`
(the directory is mounted read-only at `/app/config`, in source-build and in deploy mode).
Create the file before the first start, for example from `config/markets.toml` of
market_data_service. To enable or disable an instrument change its `enabled` value and
restart only that container (`docker compose restart market-data-service`); no image,
pin or PR is needed. MDS reads the file at start, so a missing or invalid file stops it
with the loader's error instead of falling back to a baked-in list. Stored history of a
disabled instrument is kept.

## Strategy Engine settings

`strategy-engine` mounts `${BBB_DATA_ROOT}/strategy-engine` read-only at `/app/config` and
receives `STRATEGY_ENGINE_CONFIG_PATH=/app/config/engine.toml` (source-build and deploy mode).
The directory must exist before the first start; the file itself is optional. Without the
file, or without a key, the Engine uses its defaults (`live_entry_mode = "ema_anchor"`).
The Engine reads the file once at start: to switch, edit it and restart only that container
(`docker compose restart strategy-engine`); no image, pin or PR is needed. An unknown key or
value, or a file that does not parse, stops the Engine with an error. Example:

```toml
live_entry_mode = "ema_anchor"   # or "touch_trigger"
```

Do not set `touch_trigger` on a live stack before ABI places the touch-close entry as a
limit order: today ABI sends a conditional Market entry that would fill at once as taker.

## Strategy Runtime settings

`strategy-runtime` mounts `${BBB_DATA_ROOT}/strategy-runtime/config` read-only at `/runtime/config` and
receives `RUNTIME_CONFIG_PATH=/runtime/config/runtime.toml`, the same way as the Engine settings above.
The directory must exist before the first start; the file is optional (missing = `live_entry_mode =
"ema_anchor"`). Runtime reads it once at start: edit it and restart only that container
(`docker compose restart strategy-runtime`). An unknown key or value, or a broken file, stops Runtime.
No Runtime behaviour depends on the mode yet.

## ABI settings

`abi` mounts `${BBB_DATA_ROOT}/abi/config` read-only at `/app/config` and receives
`ABI_CONFIG_PATH=/app/config/abi.json`. The directory must exist before the first start; the file is
optional (missing = `live_entry_mode` `ema_anchor`, the conditional Market entry). ABI reads it once at
start: edit it and restart only that container. Invalid JSON, an unknown key or value stops ABI.

```json
{ "live_entry_mode": "touch_trigger", "touch_trigger_entry_order_type": "limit" }
```

Set `touch_trigger` in ABI only together with the Engine and Runtime settings above, after the joint
check: in `touch_trigger` ABI sends a plain Market or a GTC Limit entry with no exchange trigger.

## Research export to the Runtime catalog

`research-service` mounts `${BBB_DATA_ROOT}/strategy-runtime/specs` read-write at
`/runtime-specs` and receives `RESEARCH_RUNTIME_SPECS_PATH=/runtime-specs`. Research only
creates new deployment files there, always with `enabled: false`
(`research-candidate-runtime-export-v1`); Strategy Runtime mounts the same directory
writable at `/runtime/specs` and uses it only to change `enabled` of an existing file
(`runtime-strategy-enabled-control-v1`). The Research API has no authentication of its own and is
published on `127.0.0.1:8095` only. Mac checks are recorded in
[`docs/verification-research-runtime-export-v1.md`](docs/verification-research-runtime-export-v1.md).
The export route needs a Research image that contains it (pin bump in `deploy/images.env`
is a separate change).

## Central Journal

`journal-service` (repository `journal_service`) is a read-only observer. It mounts
`${BBB_DATA_ROOT}/strategy-runtime/journal` read-only at `/sources/runtime`, reads
`runtime.jsonl` from there, and keeps its own SQLite database in
`${BBB_DATA_ROOT}/journal` (mounted read-write at `/data`, file `journal.sqlite3`). No
other service mounts that database directory. To assemble closed trades it reads ABI's
per-cycle exchange journal over HTTP (`JOURNAL_ABI_BASE_URL=http://abi:8787`, GET only);
when ABI is down the trade rows stay incomplete and are retried. Its health endpoint is published on
`127.0.0.1:8097` only. No trading service depends on it (`depends_on`) and it depends on
none, so stopping it never affects Runtime, ABI, Engine, MDS or Research. Mac checks are
recorded in [`docs/verification-journal-service-v1.md`](docs/verification-journal-service-v1.md).
The deploy override requires `JOURNAL_IMAGE`; its pin in `deploy/images.env` is a separate
change after the journal_service image is published.

## Deployment (GHCR images, no local build)

The `Deploy BBB` GitHub Actions workflow (manual `workflow_dispatch`,
self-hosted Mac runner) pulls the exact images pinned in
[`deploy/images.env`](deploy/images.env) and updates the necessary containers without
building from source:

```sh
docker compose -f docker-compose.yml -f docker-compose.deploy.yml \
  --env-file deploy/images.env up -d --no-build --remove-orphans
```

It requires `BBB_DATA_ROOT` and trusted Demo `ABI_EXPECTED_BYBIT_UID` already set in the
runner's own environment and never runs `down -v` —
durable state (MDS data, Runtime journal/state, ABI var, Research
runs/configs) survives recreate. The workflow does not send bars,
place/cancel Bybit orders, or change strategy specs; ABI stays in Demo
mode (`BYBIT_ENV=demo`,
the Deploy workflow explicitly sets dry-run off and live trading on).

## Switching Demo / Mainnet

[Switching runbook](docs/mainnet-cutover.md): one parameterized Compose, one
`deploy/images.env` manifest and the existing **Deploy BBB** workflow with an explicit
`demo`/`mainnet` choice. Shared history/config stays at `BBB_DATA_ROOT`; trading memory
uses that root for Demo and `BBB_DATA_ROOT/mainnet` for Mainnet. Stop the current stack
only before switching environments. Same-environment Deploy uses ordinary Compose up;
unchanged ABI keeps its authorization. A recreated ABI starts LOCKED and is authorized
separately through age, without restart.

Mainnet requires the published ABI image from PR #58 pinned in the same common manifest;
the current pins are preserved until that release. No separate Mainnet image set exists.

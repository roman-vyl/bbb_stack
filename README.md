# BBB Stack

System-level deployment and integration repository for the BBB live stack.

This repository owns Docker Compose wiring, system configuration, lifecycle ordering,
system smoke checks, and system-level OpenSpec only. It does not vendor service source,
service Dockerfiles, or application contracts.

## Deployed image versions

[`deploy/images.env`](deploy/images.env) is the source of truth for which
four immutable GHCR images (tagged by full Git commit SHA) make up the
current BBB Demo deployment. Update it via a normal PR after a service's
CI has published a new image on its `main`.

## Usage (local source build, for development)

Set a data root before rendering or starting the stack:

```sh
export BBB_DATA_ROOT=/tmp/bbb-live-stack
docker compose config
docker compose up --build
```

The base composition is safe by default: ABI runs dry-run, live trading is
disabled, and no exchange credential file is loaded.

For a Bybit Demo execution smoke, keep data and secrets outside the repository:

```sh
export BBB_DATA_ROOT=/Users/mcroma/BBB_data
export BBB_SECRETS_ROOT=/Users/mcroma/BBB_secrets
mkdir -p "$BBB_DATA_ROOT"/{abi,market-data,strategy-runtime/journal,strategy-runtime/specs}
mkdir -p "$BBB_SECRETS_ROOT"/abi
$EDITOR "$BBB_SECRETS_ROOT"/abi/bybit-demo.env
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build
```

The Demo secret file is expected at
`$BBB_SECRETS_ROOT/abi/bybit-demo.env` and should contain:

```sh
BYBIT_API_KEY=...
BYBIT_API_SECRET=...
```

The four service build contexts default to sibling repositories:

- `MDS_REPO_PATH=../market_data_service`
- `STRATEGY_ENGINE_REPO_PATH=../strategy_engine`
- `STRATEGY_RUNTIME_REPO_PATH=../strategy_runtime`
- `ABI_REPO_PATH=../abi_executor_bot`

## Demo deployment (GHCR images, no local build)

The `Deploy Demo` GitHub Actions workflow (manual `workflow_dispatch`,
self-hosted Mac runner) pulls the exact images pinned in
[`deploy/images.env`](deploy/images.env) and recreates the stack without
building from source:

```sh
docker compose -f docker-compose.yml -f docker-compose.demo.yml -f docker-compose.deploy.yml \
  --env-file deploy/images.env up -d --no-build --remove-orphans
```

It requires `BBB_DATA_ROOT` and `BBB_SECRETS_ROOT` already set in the
runner's own environment (not GitHub secrets) and never runs `down -v` —
durable state (MDS data, Runtime journal/state, ABI var) survives
recreate. The workflow does not send bars, place/cancel Bybit orders, or
change strategy specs; ABI stays in Demo mode (`BYBIT_ENV=demo`,
dry-run disabled only via the existing `docker-compose.demo.yml`
override, same as manual Demo runs today).

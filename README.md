# BBB Stack

System-level deployment and integration repository for the BBB live stack.

This repository owns Docker Compose wiring, system configuration, lifecycle ordering,
system smoke checks, and system-level OpenSpec only. It does not vendor service source,
service Dockerfiles, or application contracts.

## Deployed image versions

[`deploy/images.env`](deploy/images.env) is the source of truth for which
five immutable GHCR images (tagged by full Git commit SHA) make up the
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
mkdir -p "$BBB_DATA_ROOT"/{abi,market-data,strategy-runtime/journal,strategy-runtime/specs,research/runs,research/configs,journal}
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

The MDS instrument list is host-owned: `${BBB_DATA_ROOT}/mds/markets.toml`
(see the README next to it). It is mounted read-only at `/app/config-host` in
base and deploy mode. Edit it by hand; MDS checks it every 10 s
(`MDS_CONFIG_WATCH_SECONDS`) and restarts itself on a valid change of the
enabled instruments. No image or pin change is needed.

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
its immutable GHCR SHA tag, and the `Deploy Demo` workflow pulls it,
waits for it to become healthy, and verifies its running image ref
alongside the other four services.

## Research export to the Runtime catalog

`research-service` mounts `${BBB_DATA_ROOT}/strategy-runtime/specs` read-write at
`/runtime-specs` and receives `RESEARCH_RUNTIME_SPECS_PATH=/runtime-specs`. Research only
creates new deployment files there, always with `enabled: false`
(`research-candidate-runtime-export-v1`); Strategy Runtime mounts the same directory
read-only at `/runtime/specs`. The Research API has no authentication of its own and is
published on `127.0.0.1:8095` only. Mac checks are recorded in
[`docs/verification-research-runtime-export-v1.md`](docs/verification-research-runtime-export-v1.md).
The export route needs a Research image that contains it (pin bump in `deploy/images.env`
is a separate change).

## Central Journal

`journal-service` (repository `journal_service`) is a read-only observer. It mounts
`${BBB_DATA_ROOT}/strategy-runtime/journal` read-only at `/sources/runtime`, reads
`runtime.jsonl` from there, and keeps its own SQLite database in
`${BBB_DATA_ROOT}/journal` (mounted read-write at `/data`, file `journal.sqlite3`). No
other service mounts that database directory. Its health endpoint is published on
`127.0.0.1:8097` only. No trading service depends on it (`depends_on`) and it depends on
none, so stopping it never affects Runtime, ABI, Engine, MDS or Research. Mac checks are
recorded in [`docs/verification-journal-service-v1.md`](docs/verification-journal-service-v1.md).
The deploy override requires `JOURNAL_IMAGE`; its pin in `deploy/images.env` is a separate
change after the journal_service image is published.

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
durable state (MDS data, Runtime journal/state, ABI var, Research
runs/configs) survives recreate. The workflow does not send bars,
place/cancel Bybit orders, or change strategy specs; ABI stays in Demo
mode (`BYBIT_ENV=demo`,
dry-run disabled only via the existing `docker-compose.demo.yml`
override, same as manual Demo runs today).

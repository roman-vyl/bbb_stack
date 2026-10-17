## Why

The MDS instrument list (`markets.toml`) is baked into the MDS image. In deploy mode
(`docker-compose.deploy.yml`) the base file's config bind mount is dropped, so changing
the list today takes four steps:
- a PR to market_data_service;
- an image build;
- a pin in `deploy/images.env`;
- recreating the container.

On 2026-10-17 that loop ran three times in one afternoon (enable 9 tickers, reconnect fix,
pause 9 tickers).

The owner wants the list to live under `BBB_DATA_ROOT`, next to the other durable host
data, so it can be edited by hand. MDS should pick up a change by itself, with no deploys
and no pins. Code changes still go through images.

## What Changes

- New host file `${BBB_DATA_ROOT}/mds/markets.toml`. It is seeded once with the config
  currently in the pinned image (`461558d`: BTC/ETH enabled, nine tickers with
  `enabled = false`). A short `README.md` sits next to it.
- `docker-compose.yml` and `docker-compose.deploy.yml`, service `market-data-service`:
  bind-mount `${BBB_DATA_ROOT}/mds` → `/app/config-host`, read-only, and set
  `MDS_MARKETS_CONFIG_PATH=/app/config-host/markets.toml`. The directory is mounted, not
  the single file, so an editor that saves by replacing the file is still seen inside the
  container. The deploy override keeps the market-data mount it already has and adds this
  one.
- `MDS_CONFIG_WATCH_SECONDS: "10"`, consumed by the MDS change
  `mds-config-file-watch-v1` (market_data_service). With it, MDS restarts itself on a
  valid edit. Until that MDS image is pinned the variable is ignored, and an edit takes
  effect on the next manual `docker restart` of MDS.
- The `bbb-live-stack` spec: the MDS config source moves from the repo checkout and the
  image to the host data root.

## Non-Goals

- No change to the MDS data mount or to the market database.
- No change to other services.
- No image pin bump in this change; the MDS image pin is a separate PR after
  `mds-config-file-watch-v1` is merged.
- No hot add or remove of streams without a process restart.
- No restart of MDS while the smoke test runs. Apply is scheduled by the owner.

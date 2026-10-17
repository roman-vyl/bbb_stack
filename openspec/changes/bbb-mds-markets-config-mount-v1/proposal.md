## Why

The list of Bybit instruments Market Data Service tracks (`config/markets.toml`) is baked
into the MDS image. In deploy mode `docker-compose.deploy.yml` drops the base file's config
bind mount, so any change of the list (enable or disable a coin) needs a market_data_service
PR, an image build, a `deploy/images.env` pin and a container re-creation.
On 2026-10-17 this took three such rounds in one day, and a pin to an image with the wrong
baked config (526a9c2, all eleven coins enabled) kept BTC/ETH out of `ready`.

Other services already take their data and settings from `${BBB_DATA_ROOT}`, outside the
repositories. The owner wants the MDS instrument list to live there too, edited by hand.

## What Changes

- `docker-compose.yml` and `docker-compose.deploy.yml`, service `market-data-service`:
  the config comes from the host directory `${BBB_DATA_ROOT}/mds`, bind-mounted
  read-only at `/app/config`. `MDS_MARKETS_CONFIG_PATH` stays `/app/config/markets.toml`.
  The `${MDS_REPO_PATH}/config/markets.toml` mount of the base file is removed.
- A directory is mounted, not the single file, so that an editor that replaces the file
  (new inode) is still seen after the container is restarted.
- README: the `mkdir` line gets `mds`, plus a paragraph on the file, its fields and how to
  enable or disable an instrument.
- A starter `${BBB_DATA_ROOT}/mds/markets.toml` is created on the owner's Mac from the
  currently deployed content (BTC and ETH enabled, nine instruments `enabled = false`).
- OpenSpec requirement added to `bbb-live-stack`.

## Non-Goals

No change to the market_data_service repository or image, no image pin bump, no change to
`deploy/images.env`. No watching of the file and no automatic restart: the owner restarts
the `market-data-service` container by hand after editing (MDS reads the file at start).
No hot add or remove of streams. No restart or deploy of any module is part of the
apply while the vertical smoke test is running.

## Findings that shape the change

1. **Restart, not redeploy.** MDS loads the file at startup, so an edit takes effect on
   `docker compose restart market-data-service`, with no image, pin or PR.
2. **Bad file.** A missing or invalid file stops MDS at startup with the loader's error;
   it does not fall back to the old baked list. Checked on the real stack in tasks 2.x.
3. **Edits are not validated before the restart.** Operator keeps a copy; the checked-in
   `config/markets.toml` of market_data_service remains the reference example.

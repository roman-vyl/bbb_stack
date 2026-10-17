## 1. Host file

- [ ] 1.1 Create `${BBB_DATA_ROOT}/mds/markets.toml`, byte-identical to the
  `config/markets.toml` baked into the currently pinned MDS image (copy it out with
  `docker run --rm --entrypoint cat <MDS_IMAGE> /app/config/markets.toml`).
- [ ] 1.2 `${BBB_DATA_ROOT}/mds/README.md` covers:
  - what the file controls;
  - how to enable or disable a ticker (`enabled`);
  - that disabling keeps stored history;
  - that MDS restarts itself on a valid edit (about a minute of `connecting`);
  - where to see errors (`docker logs bbb_stack-market-data-service-1`).

## 2. Compose

- [ ] 2.1 `docker-compose.yml`, `market-data-service`: replace the
  `${MDS_REPO_PATH}/config/markets.toml` mount with
  `${BBB_DATA_ROOT}/mds` → `/app/config-host`, read-only, and set
  `MDS_MARKETS_CONFIG_PATH: "/app/config-host/markets.toml"` and
  `MDS_CONFIG_WATCH_SECONDS: "10"`.
- [ ] 2.2 `docker-compose.deploy.yml`, `market-data-service`: the `volumes: !override` list
  keeps the market-data mount and adds the same `/app/config-host` mount.
- [ ] 2.3 `docker compose -f docker-compose.yml config --quiet` and the same with
  `-f docker-compose.deploy.yml --env-file deploy/images.env` succeed. The rendered MDS
  service shows both mounts, with `/app/config-host` read-only, and both environment
  variables.
- [ ] 2.4 README of bbb_stack: one paragraph on the host config file.

## 3. Apply on the Mac (only when the owner allows an MDS restart)

- [ ] 3.1 Recreate only `market-data-service`. `docker inspect` shows `/app/config-host`
  with `RW: false`, and the startup log shows the same enabled streams as before
  (BTCUSDT.P and ETHUSDT.P, 4 timeframes each).
- [ ] 3.2 BTC/ETH reach `ready` within 5 minutes, with no reconnect loop.
- [ ] 3.3 Manual pickup works without image change: append a comment line to the host
  file, `docker restart` MDS, and the streams return to `ready`. The comment line is
  removed afterwards.

## 4. Out of this change

- MDS self-restart on file change: market_data_service `mds-config-file-watch-v1`, then
  an MDS pin PR.
- Re-enabling the nine paused tickers: a separate owner decision after the WebSocket drop
  cause is fixed.

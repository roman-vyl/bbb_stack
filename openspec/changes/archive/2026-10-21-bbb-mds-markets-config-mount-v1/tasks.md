## 1. Compose and docs (apply)

- [x] 1.1 `docker-compose.yml`: `market-data-service` replaces the
  `${MDS_REPO_PATH}/config/markets.toml` bind mount with
  `${BBB_DATA_ROOT:?BBB_DATA_ROOT must be set}/mds` → `/app/config`, `read_only: true`.
- [x] 1.2 `docker-compose.deploy.yml`: the `volumes: !override` list for
  `market-data-service` contains the same config mount next to `/data`; the comment about
  the baked config is replaced.
- [x] 1.3 `docker compose config --quiet` succeeds for the base file and for
  `-f docker-compose.demo.yml -f docker-compose.deploy.yml --env-file deploy/images.env`;
  the rendered config shows the new mount only on `market-data-service`.
  Checked 2026-10-21: exit 0 for the base file and for base + demo + deploy (the demo file is
  an overlay and needs the base file; `BBB_SECRETS_ROOT` pointed at empty placeholder files).
  Only `market-data-service` has `${BBB_DATA_ROOT}/mds` -> `/app/config`, read-only.
- [x] 1.4 README: add `mds` to the `mkdir` line, a short section on the file and on
  restarting only `market-data-service`.

## 2. On the Mac (owner's device; no restart while the smoke test runs)

- [x] 2.1 Create `${BBB_DATA_ROOT}/mds/markets.toml` from the content of image 461558d.
  Present on the Mac since 2026-10-19 20:32Z; 10 instruments enabled.
- [x] 2.2 After the smoke test, on the owner's word: re-create `market-data-service` once with the new
  mount; `/health` is healthy; BTC/ETH 5m/1h/4h/1d reach `ready`.
  Live container mounts `/Users/mcroma/BBB_data/mds` -> `/app/config` read-only; `/health` is
  `healthy`; MDS logs `service readiness ready=True ready_streams=40 total_streams=40`
  (10 instruments x 5m/1h/4h/1d, BTC and ETH included) on 2026-10-21.
- [x] 2.3 Edit-to-effect: change one `enabled`, restart only `market-data-service`, the
  stream list in `/health` follows the file, without any image or pin change.
  Confirmed by the owner: editing `enabled` and restarting MDS changes the stream list;
  checked many times on the Mac.
- [ ] 2.4 Bad file: with an invalid file MDS fails at startup with a readable error; the
  file is restored and MDS starts. Recorded in the verification note.
  Waived by the owner on 2026-10-21: not needed.

## 3. Out of this change

- [ ] 3.1 Return of the nine paused instruments is a file edit after the websocket
  drop cause is found; it is not part of this change.
- [ ] 3.2 File watching and automatic restart, if wanted later, is a separate
  market_data_service OpenSpec.

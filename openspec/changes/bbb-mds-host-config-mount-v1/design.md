## Decisions

1. **Directory mount, read-only.** Mounting `${BBB_DATA_ROOT}/mds` at `/app/config-host`
   avoids the stale-inode problem of single-file bind mounts. Many editors write a new
   file and rename it over the old one; a single-file mount keeps pointing at the old
   inode. Read-only, because MDS never writes its config.

2. **The path comes from the existing variable.** `MDS_MARKETS_CONFIG_PATH` already
   selects the config file (`RuntimeSettings`). Only its value changes. The baked
   `/app/config/markets.toml` stays in the image as the fallback for runs outside the
   stack.

3. **Seed, not sync.** The host file is created once from the pinned image's config. After
   that the host file is the source of truth for the live stack. The repository copy stays
   the default for tests and for runs without the stack.

4. **Missing file fails loudly.** If `${BBB_DATA_ROOT}/mds/markets.toml` is absent, MDS
   fails at startup with the existing "config not found" error. It does not fall back
   silently to the baked list. The apply checklist creates the file before the first
   recreate.

5. **Pickup.** Picking up an edit by itself is MDS behaviour (`mds-config-file-watch-v1`).
   This change only provides the file and the variable. Without that MDS image, an edit
   needs `docker restart bbb_stack-market-data-service-1`, with no image or pin change.

## Risks

- An invalid edit: MDS validates the file before it acts on it (see the MDS change). A bad
  file found at a cold start still makes MDS fail at startup, as any invalid config does
  today. The README says to check `docker logs` after an edit.
- Restart cost: every applied edit restarts MDS. Streams are `connecting` for about a
  minute (measured 2026-10-17: about 48 s from start to BTC 5m `ready`). Calculations
  started in that minute fail with `stream_not_ready`.

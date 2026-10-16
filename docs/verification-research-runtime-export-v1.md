# research-runtime-export-v1 Verification (bbb_stack side)

Change: `bbb-research-runtime-catalog-mount-v1`.

## 1. Compose rendering (done in the cloud session, 2026-10-16)

Rendered with `BBB_DATA_ROOT=/tmp/bbbdata` and an empty `BBB_SECRETS_ROOT/abi/bybit-demo.env`:

- `docker compose -f docker-compose.yml config --quiet`: exit 0.
- `docker compose -f docker-compose.yml -f docker-compose.demo.yml -f docker-compose.deploy.yml --env-file deploy/images.env config --quiet`: exit 0.
- Rendered base config:
  - `research-service`: `/data` (rw), `/runtime-specs` (rw, source `${BBB_DATA_ROOT}/strategy-runtime/specs`),
    `RESEARCH_RUNTIME_SPECS_PATH=/runtime-specs`, port `127.0.0.1:8095->8080`.
  - `strategy-runtime`: `/runtime/specs` **read-only**, `/runtime/journal` rw, `/runtime/state` rw, port `127.0.0.1:8093`.
  - Only `research-service` and `strategy-runtime` mount `strategy-runtime/specs`.
- `docker-compose.deploy.yml` is unchanged and overrides only images.

## 2. Checks on the owner's Mac (run 2026-10-16)

Run on 2026-10-16 with `BBB_DATA_ROOT=/Users/mcroma/BBB_data`, research-service on image `42df599`
(first pass), then `dd12d5b` and `e19a764`. Strategy Runtime and ABI were stopped; Runtime checks used a
one-off `docker run --rm --network none --read-only` of the pinned Runtime image (`5d62a6e`) with the
catalog mounted `:ro`. Test export files were removed afterwards.

| # | Check | Command | Expected | Result |
|---|-------|---------|----------|--------|
| 2.1 | Mount modes | `docker inspect bbb_stack-research-service-1 --format '{{json .Mounts}}'`; same for `bbb_stack-strategy-runtime-1`; `docker exec bbb_stack-strategy-runtime-1 sh -c 'touch /runtime/specs/.w 2>&1'` | research: `/runtime-specs` RW true; runtime: `/runtime/specs` RW false; the write fails || PASS: research `/runtime-specs` RW=true, `/data` RW=true; runtime `/runtime/specs` RW=false; `touch` in Runtime: "Read-only file system" |
| 2.2 | flock | in the research container, run a Python snippet: open `/data/analysis/.flock_probe`, `fcntl.flock(fd1, LOCK_EX)`, then `fcntl.flock(fd2, LOCK_EX\|LOCK_NB)` on a second open fd must raise `BlockingIOError`; remove the probe | second lock refused || FAIL on Docker Desktop (`fakeowner` mount): the second lock was granted. By the owner's decision Research export no longer uses `flock` (research_service #35, one Research process per catalog); not required any more |
| 2.3 | hard link | in the research container: create `/runtime-specs/.probe.tmp`, `os.link` it to `/runtime-specs/.probe.final` (ok), `os.link` again to the same name (`FileExistsError`), remove both | link works, second link refused, no files left || PASS: first link ok, second `FileExistsError`, no probe files left |
| 2.4 | readable by Runtime | `docker exec bbb_stack-strategy-runtime-1 cat /runtime/specs/<exported file>` | readable || PASS: Runtime reads the exported file |
| 2.5 | loopback only | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8095/health`; the same against the Mac LAN IP; `docker compose ps` | 200 on loopback; LAN connection refused; no `0.0.0.0` publishing for research-service || PASS: loopback 200, LAN 192.168.3.36:8095 connection refused, published only on `127.0.0.1:8095` |
| 2.6 | known V1 limitation | none | the local Research API has no authentication and no anti-CSRF header | recorded |
| 2.7 | Runtime accepts the exported deployment | after an export, in the runtime container run the catalog loader on `/runtime/specs` (read only): the exported file name is in `accepted_deployments`, `enabled` false, `strategy_instance_id` equals the export response; it is not in `invalid_files` or `duplicate_identities`; not selected for a bar | accepted || PASS (API export and again from the Candidates tab): scanned 33, accepted 33, invalid 0, duplicates 0; exported file accepted, `enabled` false, `strategy_instance_id` `ema_pullback:ad27e132dd1977c47733408f` = export response; not selected for BTCUSDT.P/5m |
| 2.8 | existing files | `ls /runtime/specs` | `loadtest-*` listed, unchanged (all `enabled: true`) || PASS: sha256 of all 32 `loadtest-*` unchanged, all `enabled: true` |

Result lines are filled in by whoever runs the checks, with the command output. A failed check is
reported to the owner and the export is not used until he decides.

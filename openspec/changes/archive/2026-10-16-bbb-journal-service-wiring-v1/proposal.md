## Why

The Central Journal (`journal_service`, change `runtime-live-entry-first-event-v1`) tails
Strategy Runtime's processing journal and stores events in its own SQLite. It needs a
container in the stack with a read-only view of the Runtime journal and a private
writable database directory, without any trading service depending on it.

## What Changes

- `docker-compose.yml`: new service `journal-service` (local build from
  `${JOURNAL_SERVICE_REPO_PATH:-../journal_service}`), `read_only: true`,
  `restart: unless-stopped`, published on `127.0.0.1:8097` only, with two bind mounts:
  `${BBB_DATA_ROOT}/strategy-runtime/journal` → `/sources/runtime` read-only and
  `${BBB_DATA_ROOT}/journal` → `/data` read-write. Environment:
  `JOURNAL_RUNTIME_SOURCE_PATH=/sources/runtime/runtime.jsonl`,
  `JOURNAL_DB_PATH=/data/journal.sqlite3`, `JOURNAL_HOST`, `JOURNAL_PORT=8097`.
- No `depends_on` on `journal-service` from any service, and none from it.
- `docker-compose.deploy.yml`: the image of `journal-service` is `${JOURNAL_IMAGE}`,
  required like the other images.
- `.github/workflows/deploy-demo.yml`: pull, health wait, image-ref check and summary
  line for `journal-service`.
- README section and a verification record `docs/verification-journal-service-v1.md`
  (filled in on the Mac, on the owner's word).
- OpenSpec requirements added to `bbb-live-stack`.

## Non-Goals

No change to `deploy/images.env` (the `JOURNAL_IMAGE` pin is a separate PR after the
journal_service image is published), no change to Runtime, ABI, Engine, MDS or Research
services or their mounts, no real strategy and no real bars in this change, no container
started by this change.

## Findings that shape the checks

1. **Deploy Demo needs the pin.** With `JOURNAL_IMAGE` required in the deploy override,
   `Deploy Demo` fails at config validation until the pin PR lands. The workflow is
   manual, so merging this change does not deploy anything; the pin PR must land before
   the next dispatch. The journal_service image needs its own CI and publish workflow
   first (not part of this change).
2. **Directory mount.** The source is mounted as a directory so that a replaced
   `runtime.jsonl` stays visible; the Central Journal already handles inode changes.
3. **SQLite on a Docker Desktop bind mount.** WAL needs working shared memory and locking
   on the mount. This is verified on the real mount (tasks 2.x) before relying on it.

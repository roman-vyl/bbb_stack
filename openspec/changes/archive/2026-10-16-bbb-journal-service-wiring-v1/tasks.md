## 1. Compose (apply)

- [x] 1.1 `docker-compose.yml`: add `journal-service` as designed; no `depends_on` anywhere for it.
- [x] 1.2 `docker-compose.deploy.yml`: `image: ${JOURNAL_IMAGE:?...}`.
- [x] 1.3 `.github/workflows/deploy-demo.yml`: pull, health wait, image check, summary for `journal-service`.
- [x] 1.4 README section; `journal` added to the data directory list.
- [x] 1.5 `docker compose config --quiet` succeeds for the base file and, with `JOURNAL_IMAGE` set, for base + demo + deploy; the rendered config shows the read-only source mount, the read-write database mount, the loopback port and no `depends_on` to or from `journal-service`.

## 2. Verification on the Mac (owner's device, recorded in `docs/verification-journal-service-v1.md`; only on the owner's word and when the Docker stack is stable)

- [x] 2.1 Build and start only `journal-service` (`--no-deps`) from the sibling checkout; it becomes healthy.
- [x] 2.2 The existing `runtime.jsonl` is scanned: `cursor_offset` reaches the file size, `/health` is green, and `/Users/mcroma/BBB_data/journal/journal.sqlite3` exists (WAL files beside it).
- [x] 2.3 `docker inspect` shows `/sources/runtime` with `RW: false` and `/data` writable; a write into `/sources/runtime` from the container fails.
- [x] 2.4 SQLite on the bind mount: after a restart of the container the cursor resumes and no row is duplicated.
- [x] 2.5 Stopping `journal-service` leaves Runtime, ABI, Engine, MDS and Research healthy and unchanged.
- [x] 2.6 `docker compose ps` shows `journal-service` published on `127.0.0.1:8097` only.

## 3. Out of this change

- [x] 3.1 journal_service CI and image publish workflows (journal_service `42c51e2`).
- [x] 3.2 Pin `JOURNAL_IMAGE` in `deploy/images.env` (`a215676`).
- [x] 3.3 Smoke with one real strategy and three real 5m bars (passed 2026-10-16, see `docs/verification-journal-service-v1.md`).

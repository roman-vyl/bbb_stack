## Context

Runtime already mounts `${BBB_DATA_ROOT}/strategy-runtime/journal` read-write at
`/runtime/journal`. The Central Journal is an observer: if it is stopped, trading
continues and it catches up later (journal_service foundation F3).

## Decisions

- **Two mounts, asymmetric.** Source read-only, database directory read-write. The
  database directory `${BBB_DATA_ROOT}/journal` is mounted by this service only.
- **No ordering.** No `depends_on` in either direction. At start the source file may not
  exist yet; the tailer waits for it.
- **Restart policy.** `unless-stopped`, like MDS: an observer that comes back by itself
  is harmless and keeps the index close to the journal.
- **Health.** The image's own `HEALTHCHECK` (`GET /health` on 8097) is used; the compose
  file does not redefine it.
- **Loopback only.** `127.0.0.1:8097:8097`, like every other published port.
- **Read-only root filesystem.** The service writes only to `/data`.

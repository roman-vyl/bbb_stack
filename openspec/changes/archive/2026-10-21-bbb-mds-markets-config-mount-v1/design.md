## Decisions

### D1. Mount the directory, not the file

`${BBB_DATA_ROOT}/mds` → `/app/config` read-only. A single-file bind mount follows one
inode; editors that save through a rename leave the container on the old content.

### D2. One layout in both compositions

The base and the deploy compositions both read `${BBB_DATA_ROOT}/mds`. Source builds and
deploy mode therefore see the same list, and the image's baked copy becomes only a
reference example.

### D3. No fallback to the baked list

If the file is absent the service must not start silently with a stale list; it fails
with the loader's error and the owner creates the file (README).

### D4. Manual restart

No watcher in MDS. Keeps the change in this repository only, with no new code in a service
that was unstable under load on 2026-10-17.

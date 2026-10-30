## Why

journal_service now assembles closed trades (change `journal-closed-trades-builder-v1`,
PR #15): for each closed Runtime trade cycle it reads ABI's per-cycle exchange journal
`GET /v1/strategy-instances/{sid}/trade-cycles/{cid}/exchange-journal`. The builder runs only
when `JOURNAL_ABI_BASE_URL` is set; the stack does not set it yet, so every trade row would stay
`incomplete` with `abi_not_configured`.

## What Changes

- `docker-compose.yml`, service `journal-service`: new environment value
  `JOURNAL_ABI_BASE_URL: "http://abi:8787"` (the same address Runtime uses for ABI).
- `journal-service` still has no `depends_on`: when ABI is down, rows stay `incomplete` and are
  retried; ingest of Runtime events goes on.
- `bbb-live-stack` requirements "Journal Service Mounts" and "Journal Service Is Not A
  Dependency" are modified to name the ABI address and the soft read.
- README: the Central Journal paragraph names the ABI read.

## Non-Goals

No new mount, port or network. ABI is not changed. No pin change: the `JOURNAL_IMAGE` pin that
contains the builder is a separate change after journal_service PR #15 is merged and its image is
published. No deploy without the owner's word.

## Impact

`docker-compose.yml`, `README.md`, `openspec/specs/bbb-live-stack` (on archive).

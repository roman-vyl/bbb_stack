# Tasks

- [x] Record service `origin/main` baseline SHAs.
- [x] Create standalone `bbb_stack` repository.
- [x] Add minimal four-service `docker-compose.yml`.
- [x] Add non-secret `.env.example` and ignore local `.env`.
- [x] Add system-level OpenSpec proposal and spec.
- [x] Verify `docker compose config` with `BBB_DATA_ROOT`.
- [x] Verify missing `BBB_DATA_ROOT` fails closed.
- [x] Build all four images.
- [x] Start the stack and confirm all services become healthy/ready.
- [x] Check host health endpoints and ABI execution mode.
- [x] Inspect service wiring environment.
- [x] Inspect bind mounts and access modes.
- [x] Confirm Strategy Engine has zero persistent mounts.
- [x] Confirm host ports bind only to `127.0.0.1`.
- [x] Stop the stack gracefully.
- [x] Restart with same `BBB_DATA_ROOT` and verify durable MDS, ABI, and Runtime files persist.
- [x] Archive the OpenSpec change after successful verification.

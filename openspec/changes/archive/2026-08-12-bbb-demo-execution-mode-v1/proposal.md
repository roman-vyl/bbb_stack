# bbb-demo-execution-mode-v1

## Why

The ABI repository now owns its Bybit Demo secret contract through
`BBB_SECRETS_ROOT`. The system stack needs a matching, opt-in Compose override
so the shared four-service stack can run a Bybit Demo smoke without placing
credentials in the repository or weakening the safe base composition.

## What Changes

- Add `docker-compose.demo.yml` that overrides only the `abi` service.
- Load ABI Demo credentials from
  `${BBB_SECRETS_ROOT}/abi/bybit-demo.env`.
- Switch ABI to Demo execution mode with dry-run disabled, live trading enabled,
  and `BYBIT_ENV=demo`.
- Document the expected local data and secret root layout.

## Non-Goals

- No service code changes.
- No changes to the base safe Compose execution mode.
- No real API keys committed or generated.
- No Bybit smoke execution in this change.

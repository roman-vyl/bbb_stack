# bbb-live-stack

## ADDED Requirements

### Requirement: Bybit Demo ABI Override

The live stack SHALL provide a separate Demo override that changes only the ABI
execution mode and credential source.

#### Scenario: ABI Demo execution mode

- **WHEN** the stack is rendered with `docker-compose.yml` and
  `docker-compose.demo.yml`
- **THEN** ABI SHALL load
  `${BBB_SECRETS_ROOT}/abi/bybit-demo.env` through `env_file`
- **AND** rendering SHALL fail non-zero unless `BBB_SECRETS_ROOT` is set
- **AND** ABI SHALL receive `ABI_DRY_RUN=false`
- **AND** ABI SHALL receive `ABI_LIVE_TRADING_ENABLED=true`
- **AND** ABI SHALL receive `BYBIT_ENV=demo`
- **AND** no service other than ABI SHALL be modified by the Demo override

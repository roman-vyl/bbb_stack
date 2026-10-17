## MODIFIED Requirements

### Requirement: Data Mount Layout

The live stack composition SHALL mount only the required system data paths from
`BBB_DATA_ROOT`.

#### Scenario: Durable and read-only paths

- **WHEN** the stack runs with `BBB_DATA_ROOT`
- **THEN** `${BBB_DATA_ROOT}/market-data` SHALL mount to MDS `/data` writable
- **AND** `${BBB_DATA_ROOT}/mds` SHALL mount to MDS `/app/config-host` read-only
- **AND** `${BBB_DATA_ROOT}/strategy-runtime/specs` SHALL mount to Runtime
  `/runtime/specs` read-only
- **AND** `${BBB_DATA_ROOT}/strategy-runtime/journal` SHALL mount to Runtime
  `/runtime/journal` writable
- **AND** `${BBB_DATA_ROOT}/abi` SHALL mount to ABI `/app/var` writable
- **AND** Strategy Engine SHALL have zero persistent mounts

## ADDED Requirements

### Requirement: Host-Owned MDS Market Configuration

The live stack SHALL take the MDS market configuration from the host file
`${BBB_DATA_ROOT}/mds/markets.toml` in every mode, including deploy mode, and SHALL NOT
depend on the repository checkout or the image for it.

#### Scenario: Config path in deploy mode

- **WHEN** the stack is rendered with `docker-compose.deploy.yml`
- **THEN** `market-data-service` SHALL receive
  `MDS_MARKETS_CONFIG_PATH=/app/config-host/markets.toml`
- **AND** SHALL mount `${BBB_DATA_ROOT}/mds` at `/app/config-host` read-only
- **AND** SHALL keep `${BBB_DATA_ROOT}/market-data` at `/data` writable.

#### Scenario: Editing the instrument list needs no image change

- **WHEN** the owner edits `${BBB_DATA_ROOT}/mds/markets.toml`
- **THEN** the change SHALL take effect after an MDS process restart
- **AND** SHALL NOT require a new image, a pin change or a compose change.

#### Scenario: Missing host config

- **WHEN** `${BBB_DATA_ROOT}/mds/markets.toml` does not exist
- **THEN** MDS SHALL fail at startup with its config-not-found error
- **AND** SHALL NOT silently use the list baked into the image.

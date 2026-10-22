## MODIFIED Requirements

### Requirement: Data Mount Layout

The live stack composition SHALL mount only the required system data paths from
`BBB_DATA_ROOT`.

#### Scenario: Durable, writable and read-only paths

- **WHEN** the stack runs with `BBB_DATA_ROOT`
- **THEN** `${BBB_DATA_ROOT}/market-data` SHALL mount to MDS `/data` writable
- **AND** `${MDS_REPO_PATH}/config/markets.toml` SHALL mount to MDS
  `/app/config/markets.toml` read-only
- **AND** `${BBB_DATA_ROOT}/strategy-runtime/specs` SHALL mount to Runtime
  `/runtime/specs` writable, so that Runtime can change `enabled` of an existing
  deployment file
- **AND** `${BBB_DATA_ROOT}/strategy-runtime/journal` SHALL mount to Runtime
  `/runtime/journal` writable
- **AND** `${BBB_DATA_ROOT}/abi` SHALL mount to ABI `/app/var` writable
- **AND** Strategy Engine SHALL have zero persistent mounts

### Requirement: Service Contract Preservation

The live stack composition SHALL preserve service-level container contracts and
SHALL NOT own application contracts.

#### Scenario: System-only change

- **WHEN** this change is implemented
- **THEN** the repository SHALL NOT modify the four service repositories
- **AND** the repository SHALL NOT copy canonical specs from those repositories
- **AND** MDS SHALL retain read-only root filesystem plus writable `/data`
- **AND** Strategy Engine SHALL retain read-only root filesystem and no volumes
- **AND** Strategy Runtime SHALL retain read-only root filesystem and writable journal,
  and its specs mount SHALL be writable only for the managed `enabled` change
- **AND** ABI SHALL retain writable `/app/var`
- **AND** the composition SHALL NOT introduce UID/GID changes, init containers,
  or chown containers

### Requirement: Research Runtime Catalog Mount

The live stack composition SHALL mount the Strategy Runtime deployment catalog into
`research-service` read-write at `/runtime-specs` and SHALL pass
`RESEARCH_RUNTIME_SPECS_PATH=/runtime-specs`, while Strategy Runtime mounts the same
directory writable at `/runtime/specs` for the managed `enabled` change only.

#### Scenario: Both mounts rendered

- **WHEN** the stack is rendered with `BBB_DATA_ROOT`
- **THEN** `${BBB_DATA_ROOT}/strategy-runtime/specs` SHALL mount to `research-service`
  `/runtime-specs` writable
- **AND** the same host directory SHALL mount to `strategy-runtime` `/runtime/specs`
  writable
- **AND** `research-service` SHALL receive `RESEARCH_RUNTIME_SPECS_PATH=/runtime-specs`
- **AND** no other service SHALL mount that directory.

#### Scenario: Deploy override unchanged

- **WHEN** the stack is rendered with `docker-compose.deploy.yml`
- **THEN** the override SHALL still change only service images.

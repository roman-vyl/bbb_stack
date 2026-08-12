# bbb-live-stack

## Purpose
Define the observable system contract for the local BBB four-service Docker
Compose stack.

## Requirements

### Requirement: Four-Service System Composition

The live stack composition SHALL define exactly four Compose services named
`market-data-service`, `strategy-engine`, `strategy-runtime`, and `abi`.

#### Scenario: Compose service ownership

- **WHEN** the system Compose file is rendered
- **THEN** it SHALL contain no services other than `market-data-service`,
  `strategy-engine`, `strategy-runtime`, and `abi`

### Requirement: Sibling Repository Build Contexts

The live stack composition SHALL build the four images from sibling repository
paths, overridable through `MDS_REPO_PATH`, `STRATEGY_ENGINE_REPO_PATH`,
`STRATEGY_RUNTIME_REPO_PATH`, and `ABI_REPO_PATH`.

#### Scenario: Default build contexts

- **WHEN** no repository path overrides are supplied
- **THEN** the MDS build context SHALL be `../market_data_service`
- **AND** the Strategy Engine build context SHALL be `../strategy_engine`
- **AND** the Strategy Runtime build context SHALL be `../strategy_runtime`
- **AND** the ABI build context SHALL be `../abi_executor_bot`
- **AND** the composition SHALL NOT use Git URL build contexts, vendored service
  source, or Git submodules

### Requirement: Internal Docker DNS Wiring

The live stack composition SHALL wire services through Compose DNS names and real
container ports.

#### Scenario: Runtime and producer URLs

- **WHEN** the stack runs
- **THEN** Strategy Engine SHALL receive
  `STRATEGY_ENGINE_MDS_BASE_URL=http://market-data-service:8080`
- **AND** Strategy Runtime SHALL receive
  `RUNTIME_STRATEGY_ENGINE_BASE_URL=http://strategy-engine:8090`
- **AND** Strategy Runtime SHALL receive `RUNTIME_ABI_BASE_URL=http://abi:8787`
- **AND** MDS SHALL receive `MDS_RUNTIME_WEBHOOK_ENABLED=true`
- **AND** MDS SHALL receive
  `MDS_STRATEGY_RUNTIME_BASE_URL=http://strategy-runtime:8093`

### Requirement: Mandatory Data Root

The live stack composition SHALL fail closed unless `BBB_DATA_ROOT` is set.

#### Scenario: Missing data root

- **WHEN** Compose is rendered without `BBB_DATA_ROOT`
- **THEN** rendering SHALL fail non-zero with `BBB_DATA_ROOT must be set`

### Requirement: Data Mount Layout

The live stack composition SHALL mount only the required system data paths from
`BBB_DATA_ROOT`.

#### Scenario: Durable and read-only paths

- **WHEN** the stack runs with `BBB_DATA_ROOT`
- **THEN** `${BBB_DATA_ROOT}/market-data` SHALL mount to MDS `/data` writable
- **AND** `${MDS_REPO_PATH}/config/markets.toml` SHALL mount to MDS
  `/app/config/markets.toml` read-only
- **AND** `${BBB_DATA_ROOT}/strategy-runtime/specs` SHALL mount to Runtime
  `/runtime/specs` read-only
- **AND** `${BBB_DATA_ROOT}/strategy-runtime/journal` SHALL mount to Runtime
  `/runtime/journal` writable
- **AND** `${BBB_DATA_ROOT}/abi` SHALL mount to ABI `/app/var` writable
- **AND** Strategy Engine SHALL have zero persistent mounts

### Requirement: Localhost-Only Host Publishing

The live stack composition SHALL publish local integration ports only on loopback.

#### Scenario: Host port bindings

- **WHEN** the stack runs
- **THEN** MDS SHALL publish `127.0.0.1:8080:8080`
- **AND** Strategy Engine SHALL publish `127.0.0.1:8090:8090`
- **AND** Strategy Runtime SHALL publish `127.0.0.1:8093:8093`
- **AND** ABI SHALL publish `127.0.0.1:8787:8787`
- **AND** no service SHALL publish host-side ports on `0.0.0.0`

### Requirement: Safe ABI Default

The base live stack composition SHALL not require exchange credentials and SHALL
start ABI in safe mode.

#### Scenario: ABI execution mode

- **WHEN** the stack runs
- **THEN** ABI SHALL receive `ABI_DRY_RUN=true`
- **AND** ABI SHALL receive `ABI_LIVE_TRADING_ENABLED=false`
- **AND** ABI SHALL receive `BYBIT_ENV=testnet`
- **AND** the base composition SHALL NOT require API keys

### Requirement: Startup Dependency Order

The live stack composition SHALL start ABI and Strategy Engine before Strategy
Runtime, and Strategy Runtime before MDS.

#### Scenario: Producer waits for consumer

- **WHEN** Compose starts the stack
- **THEN** Strategy Runtime SHALL depend on healthy `strategy-engine` and healthy
  `abi`
- **AND** MDS SHALL depend on healthy `strategy-runtime`
- **AND** Strategy Engine SHALL NOT depend on MDS

### Requirement: Service Contract Preservation

The live stack composition SHALL preserve service-level container contracts and
SHALL NOT own application contracts.

#### Scenario: System-only change

- **WHEN** this change is implemented
- **THEN** the repository SHALL NOT modify the four service repositories
- **AND** the repository SHALL NOT copy canonical specs from those repositories
- **AND** MDS SHALL retain read-only root filesystem plus writable `/data`
- **AND** Strategy Engine SHALL retain read-only root filesystem and no volumes
- **AND** Strategy Runtime SHALL retain read-only root filesystem, read-only
  specs, and writable journal
- **AND** ABI SHALL retain writable `/app/var`
- **AND** the composition SHALL NOT introduce UID/GID changes, init containers,
  or chown containers

# bbb-touch-anchor-vertical-smoke Specification

## ADDED Requirements

### Requirement: System smoke uses the ratified four-service stack

The smoke SHALL run against the existing `docker-compose.yml` services
`market-data-service`, `strategy-engine`, `strategy-runtime`, and `abi`.

#### Scenario: No service source or contract ownership

- **WHEN** the smoke artifacts are added
- **THEN** no source files in `market_data_service`, `strategy_engine`,
  `strategy_runtime`, or `abi_executor_bot` SHALL be modified
- **AND** no service Dockerfile or service API contract SHALL be modified
- **AND** no service source SHALL be copied into `bbb_stack`.

### Requirement: Touch-anchor fixture is reused

The smoke SHALL reuse an existing Strategy Engine EMA Pullback touch-anchor
fixture and SHALL NOT invent simplified strategy logic.

#### Scenario: Deterministic target bar

- **WHEN** the smoke prepares market data
- **THEN** it SHALL use ticker `BTCUSDT.P`
- **AND** timeframe `5m`
- **AND** trigger bar `open_time_ms=3300000`
- **AND** a market window sufficient for the existing Strategy Engine fixture.

### Requirement: MDS data path remains real

The smoke SHALL use MDS application/storage ingestion to prepare the isolated
market window and SHALL verify the window through MDS HTTP read APIs.

#### Scenario: MDS-originated event limitation is explicit

- **WHEN** production MDS exposes no deterministic HTTP/test seam for injecting
  one realtime committed websocket candle
- **THEN** the smoke MAY inject exactly one canonical closed-bar webhook at
  Runtime
- **AND** the report SHALL label this as one-boundary injection rather than a
  fully MDS-originated vertical.

### Requirement: Runtime routes through Engine and ABI

The smoke SHALL prove Runtime accepts the closed-bar event, dispatches to the
Strategy Engine live-entry endpoint, receives a singular desired entry, and
attempts the ABI entry-package endpoint through production HTTP boundaries.

#### Scenario: Touch-anchor desired entry

- **WHEN** Strategy Engine evaluates the selected bar
- **THEN** the result SHALL contain one `desired_entry`
- **AND** its side SHALL be `long`
- **AND** it SHALL include planned entry, initial stop, initial take, locked
  exit profile, and source plan bar fields.

### Requirement: ABI safe mode boundary is preserved

The smoke SHALL keep base-stack ABI safety settings:
`ABI_DRY_RUN=true`, `ABI_LIVE_TRADING_ENABLED=false`, `BYBIT_ENV=testnet`, and
no credentials.

#### Scenario: Safe mode blocks live execution

- **WHEN** ABI dry-run mode does not return `entry_package_applied`
- **THEN** the smoke SHALL NOT enable live trading or fabricate exchange fill
- **AND** it SHALL report the exact first boundary reached through ABI response,
  correlation record, Runtime journal, and logs.

### Requirement: Observable evidence is persisted

The smoke SHALL produce a compact verification report containing baseline SHAs,
chosen fixture, market window preparation, trigger mode, Runtime journal
outcome, Engine desired entry summary, ABI acknowledgement/error, correlation
record status, and final verdict.

#### Scenario: Verification fails closed

- **WHEN** an expected observable contract result is absent
- **THEN** the smoke script SHALL exit non-zero
- **AND** the report SHALL identify the first failing boundary.

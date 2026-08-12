# bbb-touch-anchor-vertical-smoke Specification

## Purpose
Define the observable system verification for the first MDS-originated
touch-anchor business vertical smoke through the ratified BBB four-service
stack.

## Requirements
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
- **AND** a timeframe-aligned trigger bar selected by the smoke fixture
- **AND** a market window sufficient for the existing Strategy Engine fixture.

### Requirement: MDS lifecycle remains real

The smoke SHALL drive MDS through production REST lower-bound discovery,
historical reconciliation, continuity readiness, WebSocket subscription,
realtime admission, and committed-bar notification.

#### Scenario: Smoke-only Bybit fixture

- **WHEN** the smoke stack is started
- **THEN** a smoke-only Bybit-compatible fixture MAY be added by Compose override
- **AND** MDS SHALL be pointed at it through `MDS_REST_BASE_URL` and
  `MDS_WEBSOCKET_URL`
- **AND** the fixture SHALL implement only the REST and WebSocket protocol
  subset consumed by the current production MDS adapters.

#### Scenario: MDS-originated trigger

- **WHEN** the fixture emits a confirmed WebSocket kline after MDS admission
- **THEN** MDS SHALL classify it through its production realtime ingestion path
- **AND** MDS SHALL notify Runtime through the real committed-bar notifier
- **AND** the smoke SHALL NOT directly POST the trigger event to Runtime.

### Requirement: Runtime routes through Engine and ABI

The smoke SHALL prove Runtime receives the MDS-originated closed-bar event,
dispatches to the Strategy Engine live-entry endpoint, receives a singular
desired entry, and attempts the ABI entry-package endpoint through production
HTTP boundaries.

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
- **AND** it SHALL report the exact safe boundary reached through ABI response,
  correlation record, Runtime journal, and logs.

### Requirement: Observable evidence is persisted

The smoke SHALL produce a compact verification report containing baseline SHAs,
chosen fixture, market window preparation, trigger mode, Runtime journal
outcome, Engine desired entry summary, ABI acknowledgement/error, correlation
record status, and final verdict.

#### Scenario: Verification fails closed before accepted safe boundary

- **WHEN** an expected observable contract result is absent
- **THEN** the smoke script SHALL exit non-zero
- **AND** the report SHALL identify the first failing boundary.

#### Scenario: Verification reaches safe ABI boundary

- **WHEN** Runtime reaches ABI entry-package and ABI blocks live execution due
  to safe dry-run configuration
- **THEN** the smoke script MAY exit zero
- **AND** the report SHALL use verdict `TOUCH_ANCHOR_VERTICAL_SMOKE_PASS`.

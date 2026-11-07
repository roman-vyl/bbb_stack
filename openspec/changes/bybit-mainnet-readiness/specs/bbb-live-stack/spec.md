## ADDED Requirements

### Requirement: Explicit Mainnet Deployment

The stack SHALL provide an explicit manual Mainnet deployment using immutable image pins, the existing services and startup ordering. It SHALL preserve the existing Demo deployment configuration and pins. Mainnet deployment SHALL fail before container mutation if its trusted UID, separate trading data root or preserved MDS/Research paths are absent or unsafe.

#### Scenario: Mainnet configuration
- **WHEN** Mainnet configuration is rendered
- **THEN** ABI SHALL use `BYBIT_ENV=mainnet`, `ABI_DRY_RUN=false`, `ABI_LIVE_TRADING_ENABLED=true`, `ABI_POSITION_SIZING_MODE=risk`, `ABI_BYBIT_LINEAR_POSITION_BINDING_MODE=hedge` and exchange facts enabled
- **AND** Runtime SHALL wait for healthy ABI and Engine, MDS SHALL wait for healthy Runtime, Research SHALL wait for Engine and MDS, and Journal SHALL have no dependency edges
- **AND** all published ports SHALL remain loopback-only

#### Scenario: Invalid environment isolation
- **WHEN** a Mainnet trading mount aliases a Demo trading mount, including through symlinks, or a required preserved history directory is missing
- **THEN** Mainnet deployment SHALL fail before `up` and SHALL NOT create an empty replacement for preserved history

### Requirement: Mainnet Late Authorization

Each Mainnet Deploy SHALL recreate ABI in LOCKED without credentials. Authorization SHALL use the existing age/stdin/Unix-socket mechanism without restart. Mainnet verification SHALL use the fixed Mainnet API host and retain the existing trusted UID and trading-rights checks, bounded response/deadline, failure classification and retries. Live execution SHALL retain authorization, dry-run, live-enabled and readiness gates while permitting Mainnet.

#### Scenario: Deployment completes without a key
- **WHEN** Mainnet Deploy completes, including a repeated Deploy with unchanged pins
- **THEN** ABI SHALL report LOCKED and `canExecuteLive=false`, and process liveness SHALL pass without waiting for trading readiness
- **AND** Deploy SHALL NOT decrypt credentials, authorize ABI or enable strategies

#### Scenario: Mainnet credentials are checked
- **WHEN** a candidate is delivered through the existing socket
- **THEN** verification SHALL use `https://api.bybit.com/v5/user/query-api`
- **AND** only the trusted UID, `readOnly=0` and required category rights SHALL allow authorization
- **AND** wrong UID, missing rights and rejected keys SHALL remain rejected; temporary failures SHALL remain fail-closed and retryable
- **AND** successful authorization SHALL NOT require container restart or bypass trading readiness

### Requirement: Environment Specific Trading Memory

Demo and Mainnet SHALL NOT share Runtime state/journal/catalog, ABI durable execution memory or Central Journal storage. A first Mainnet launch SHALL start with fresh trading memory and every strategy disabled. MDS and Research history SHALL be retained without two concurrent writers.

#### Scenario: First Mainnet launch
- **WHEN** the approved operational cutover prepares Mainnet
- **THEN** Demo trading files SHALL be preserved and consistently archived, Mainnet Runtime state/journal, ABI correlation/facts/diagnostics and Journal database SHALL start fresh
- **AND** any copied strategy deployment SHALL have `enabled: false` before Runtime starts
- **AND** copied strategy parameters and Engine/Runtime/ABI entry-mode configuration SHALL otherwise be preserved
- **AND** Mainnet Research exports SHALL target only the Mainnet strategy catalog

#### Scenario: Subsequent deploy
- **WHEN** Mainnet is redeployed after the first launch
- **THEN** its own durable memory SHALL survive, without automatic reset, archive restoration or strategy enablement

### Requirement: Account Preflight Before Strategy Enablement

The cutover runbook SHALL require separate authorization followed by read-only confirmation of the target Unified linear USDT account, cross margin (`REGULAR_MARGIN`), hedge slots for intended symbols, account positions/orders and configured strategy risks before any strategy is enabled. It SHALL NOT automatically change exchange modes or execute a trading smoke.

#### Scenario: Fresh memory does not prove account readiness
- **WHEN** ABI is authorized with no active local bindings
- **THEN** successful health/readiness SHALL NOT substitute for account and per-symbol preflight
- **AND** strategies SHALL remain disabled if margin, hedge geometry or account exposure is incompatible or unverified

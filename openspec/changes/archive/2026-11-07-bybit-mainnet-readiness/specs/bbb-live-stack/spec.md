## ADDED Requirements

### Requirement: One Deployment With Explicit Environment

The existing deployment SHALL select `demo` or `mainnet` for one BBB stack, using the same six services, Compose configuration, immutable image manifest, startup ordering and age authorization mechanism. It SHALL NOT introduce a separate Mainnet workflow or image manifest.

#### Scenario: Environment selected
- **WHEN** the operator selects Demo or Mainnet with manual stack stopping required only for environment changes
- **THEN** Deploy SHALL select the environment's trusted UID, `BYBIT_ENV` and trading data root
- **AND** the six images, service DNS, loopback ports and startup dependencies SHALL remain the same
- **AND** deployment SHALL fail before update only if the selected environment differs from that of the running stack

### Requirement: Isolated Trading Memory With Shared History

Demo and Mainnet SHALL use separate ABI var, Runtime state/journal/catalog and Journal database directories. MDS/Research history and service configuration SHALL be preserved.

#### Scenario: Switching environment
- **WHEN** the selected environment changes
- **THEN** trading data mounts SHALL change together, including Research export catalog and Journal Runtime source
- **AND** the operator SHALL prepare separate trading directories without aliases
- **AND** Deploy SHALL NOT reset, archive or copy data

### Requirement: Deploy Preserves Authorization Unless ABI Is Recreated

Same-environment Deploy SHALL use ordinary Compose up without stopping the stack or forcing recreation. A newly created ABI SHALL start LOCKED; an unchanged ABI SHALL retain its authorization. Separate age/socket authorization SHALL remain unchanged.

#### Scenario: Repeat deploy with unchanged ABI configuration
- **WHEN** the selected environment and ABI configuration/image are unchanged
- **THEN** Deploy SHALL NOT force ABI recreation, restart or authorization reset
- **AND** durable state and enabled/disabled SHALL be preserved

#### Scenario: ABI recreated by Compose
- **WHEN** ordinary Compose up recreates ABI because its image or configuration changed
- **THEN** ABI SHALL start LOCKED and require separate manual authorization without restart

### Requirement: First Mainnet Launch Has Disabled Strategies

The operator SHALL manually prepare fresh trading memory and disabled strategies for the first Mainnet launch. Backup and directory preparation SHALL remain separate manual operations; Deploy SHALL NOT infer first launch from file content, migrate/reset data or change enabled values.

#### Scenario: First Mainnet launch after manual preparation
- **WHEN** the operator stops Demo and selects Mainnet after preparing its directories and disabled specs
- **THEN** Deploy SHALL use the Mainnet UID and trading directories without modifying Demo data

#### Scenario: Returning to an environment
- **WHEN** the operator returns to an existing environment after stopping the current stack
- **THEN** Deploy SHALL use that environment's previous durable state and enabled/disabled values

### Requirement: Account Checks Before Strategy Enablement

The switching runbook SHALL require read-only confirmation of the trusted UID, Unified linear USDT account, cross margin (`REGULAR_MARGIN`), per-symbol hedge slots, orders/positions and strategy risks before strategy enablement. It SHALL NOT automate exchange mode changes or a trading smoke.

#### Scenario: Empty local bindings
- **WHEN** ABI is authorized and ready with no active local bindings
- **THEN** readiness SHALL NOT substitute for account/per-symbol checks
- **AND** strategies SHALL remain disabled until the owner enables them separately

## REMOVED Requirements

### Requirement: Bybit Demo ABI Override
**Reason**: One parameterized Compose serves both environments and late authorization replaces plaintext env_file.
**Migration**: Select `BYBIT_ENV`, trusted UID and trading root in the common Deploy; authorize separately through the existing age/socket client.

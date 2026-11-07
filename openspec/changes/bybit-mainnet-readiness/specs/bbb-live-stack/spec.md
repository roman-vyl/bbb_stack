## ADDED Requirements

### Requirement: One Deployment With Explicit Environment

The existing deployment SHALL select `demo` or `mainnet` for one BBB stack, using the same six services, Compose configuration, immutable image manifest, startup ordering and age authorization mechanism. It SHALL NOT introduce a separate Mainnet workflow or image manifest.

#### Scenario: Environment selected
+- **WHEN** the operator selects Demo or Mainnet after stopping the stack
+- **THEN** Deploy SHALL select the environment's trusted UID, `BYBIT_ENV` and trading data root
+- **AND** the six images, service DNS, loopback ports and startup dependencies SHALL remain the same
+- **AND** deployment SHALL fail before recreation if the current stack is still running
+
+### Requirement: Isolated Trading Memory With Shared History

Demo and Mainnet SHALL use separate ABI var, Runtime state/journal/catalog and Journal database directories. MDS/Research history and service configuration SHALL be preserved.

#### Scenario: Switching environment
+- **WHEN** the selected environment changes
+- **THEN** trading data mounts SHALL change together, including Research export catalog and Journal Runtime source
+- **AND** Deploy SHALL reject overlapping Demo/Mainnet trading paths and trading symlinks
+- **AND** Deploy SHALL NOT reset, archive or copy data
+
+### Requirement: Deploy Leaves ABI Locked

Every Deploy SHALL recreate ABI without credentials and verify LOCKED. Separate age/socket authorization SHALL work without restart. Existing authorization, dry-run, live-enabled, UID/rights and trading-readiness gates SHALL remain effective.

#### Scenario: Repeat deploy with unchanged pins
+- **WHEN** Deploy recreates the selected environment with the same pins
+- **THEN** ABI SHALL report LOCKED and `canExecuteLive=false`
+- **AND** Deploy SHALL NOT authorize ABI or enable strategies
+
+### Requirement: First Mainnet Launch Has Disabled Strategies

Mainnet SHALL start with fresh trading memory and every strategy disabled. Until Runtime has nonempty durable state, Deploy SHALL require all deployment JSON files to have `enabled: false`.

#### Scenario: Enabled first-launch deployment
+- **WHEN** the Mainnet catalog contains enabled, invalid JSON or unsupported entries before durable state exists
+- **THEN** Deploy SHALL fail before startup
+- **AND** strategies and files SHALL remain unchanged
+
+#### Scenario: Later deployment
+- **WHEN** Mainnet has its own durable state and is redeployed
+- **THEN** Deploy SHALL preserve its data and enabled values, while recreating ABI LOCKED
+
+### Requirement: Account Checks Before Strategy Enablement

The switching runbook SHALL require read-only confirmation of the trusted UID, Unified linear USDT account, cross margin (`REGULAR_MARGIN`), per-symbol hedge slots, orders/positions and strategy risks before strategy enablement. It SHALL NOT automate exchange mode changes or a trading smoke.
+
+#### Scenario: Empty local bindings
+- **WHEN** ABI is authorized and ready with no active local bindings
+- **THEN** readiness SHALL NOT substitute for account/per-symbol checks
+- **AND** strategies SHALL remain disabled until the owner enables them separately
+
+## REMOVED Requirements
+
+### Requirement: Bybit Demo ABI Override
+**Reason**: One parameterized Compose serves both environments and late authorization replaces plaintext env_file.
+**Migration**: Select `BYBIT_ENV`, trusted UID and trading root in the common Deploy; authorize separately through the existing age/socket client.

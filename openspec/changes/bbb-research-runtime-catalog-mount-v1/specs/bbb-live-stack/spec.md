## ADDED Requirements

### Requirement: Research Runtime Catalog Mount

The live stack composition SHALL mount the Strategy Runtime deployment catalog into
`research-service` read-write at `/runtime-specs` and SHALL pass
`RESEARCH_RUNTIME_SPECS_PATH=/runtime-specs`, while Strategy Runtime keeps the same
directory read-only.

#### Scenario: Both mounts rendered

- **WHEN** the stack is rendered with `BBB_DATA_ROOT`
- **THEN** `${BBB_DATA_ROOT}/strategy-runtime/specs` SHALL mount to `research-service`
  `/runtime-specs` writable
- **AND** the same host directory SHALL mount to `strategy-runtime` `/runtime/specs`
  read-only
- **AND** `research-service` SHALL receive `RESEARCH_RUNTIME_SPECS_PATH=/runtime-specs`
- **AND** no other service SHALL mount that directory.

#### Scenario: Deploy override unchanged

- **WHEN** the stack is rendered with `docker-compose.deploy.yml`
- **THEN** the override SHALL still change only service images.

### Requirement: Research API Stays Loopback-Only

The live stack composition SHALL keep the Research API published only on loopback, so
that the create-only runtime export route is not reachable from the network.

#### Scenario: Host port binding

- **WHEN** the stack runs
- **THEN** `research-service` SHALL publish `127.0.0.1:8095:8080`
- **AND** the Research API SHALL NOT answer on the host's non-loopback addresses.

### Requirement: Catalog Capability Is Verified On The Real Mount

Before the runtime export is used, the owner's Mac SHALL be checked for the mount modes of
both services, `flock` and hard-link support on the catalog mount, readability of exported
files by Strategy Runtime, and the cross-site behaviour of the export route, and the results
SHALL be recorded in `docs/verification-research-runtime-export-v1.md`.

#### Scenario: A check fails

- **WHEN** any check of the verification record fails
- **THEN** the failure is reported to the owner and the export is not used until he decides.

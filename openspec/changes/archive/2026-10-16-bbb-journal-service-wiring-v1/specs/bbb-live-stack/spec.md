## ADDED Requirements

### Requirement: Journal Service Mounts

The live stack composition SHALL run `journal-service` with the Strategy Runtime journal
directory mounted read-only and a database directory mounted read-write that no other
service mounts.

#### Scenario: Mounts rendered

- **WHEN** the stack is rendered with `BBB_DATA_ROOT`
- **THEN** `${BBB_DATA_ROOT}/strategy-runtime/journal` SHALL mount to `journal-service` `/sources/runtime` read-only
- **AND** `${BBB_DATA_ROOT}/journal` SHALL mount to `journal-service` `/data` writable
- **AND** no other service SHALL mount `${BBB_DATA_ROOT}/journal`
- **AND** `journal-service` SHALL receive `JOURNAL_RUNTIME_SOURCE_PATH=/sources/runtime/runtime.jsonl` and `JOURNAL_DB_PATH=/data/journal.sqlite3`.

### Requirement: Journal Service Is Not A Dependency

No service of the live stack SHALL depend on `journal-service`, and `journal-service` SHALL
depend on no other service.

#### Scenario: No ordering edges

- **WHEN** the stack is rendered
- **THEN** no service SHALL list `journal-service` in `depends_on`
- **AND** `journal-service` SHALL have no `depends_on`.

#### Scenario: Journal Service stopped

- **WHEN** `journal-service` is stopped
- **THEN** Strategy Runtime, ABI, Strategy Engine, MDS and Research SHALL keep running unchanged.

### Requirement: Journal Service Stays Loopback-Only

The live stack composition SHALL publish the `journal-service` health port only on loopback.

#### Scenario: Host port binding

- **WHEN** the stack runs
- **THEN** `journal-service` SHALL publish `127.0.0.1:8097:8097`
- **AND** no `0.0.0.0` host publishing SHALL exist for it.

### Requirement: Journal Service Image Is Pinned Separately

The deploy composition SHALL take the `journal-service` image from `JOURNAL_IMAGE`, and the
pin in `deploy/images.env` SHALL be changed only by a separate change after the image is
published.

#### Scenario: Deploy override

- **WHEN** the stack is rendered with `docker-compose.deploy.yml`
- **THEN** `journal-service` SHALL use `${JOURNAL_IMAGE}` and rendering SHALL fail if it is unset.

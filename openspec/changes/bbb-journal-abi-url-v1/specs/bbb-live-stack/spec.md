## MODIFIED Requirements

### Requirement: Journal Service Mounts

The live stack composition SHALL run `journal-service` with the Strategy Runtime journal
directory mounted read-only and a database directory mounted read-write that no other
service mounts, and SHALL give it the ABI address on the stack network for reading
closed-trade facts.

#### Scenario: Mounts rendered

- **WHEN** the stack is rendered with `BBB_DATA_ROOT`
- **THEN** `${BBB_DATA_ROOT}/strategy-runtime/journal` SHALL mount to `journal-service` `/sources/runtime` read-only
- **AND** `${BBB_DATA_ROOT}/journal` SHALL mount to `journal-service` `/data` writable
- **AND** no other service SHALL mount `${BBB_DATA_ROOT}/journal`
- **AND** `journal-service` SHALL receive `JOURNAL_RUNTIME_SOURCE_PATH=/sources/runtime/runtime.jsonl` and `JOURNAL_DB_PATH=/data/journal.sqlite3`
- **AND** `journal-service` SHALL receive `JOURNAL_ABI_BASE_URL=http://abi:8787`.

### Requirement: Journal Service Is Not A Dependency

No service of the live stack SHALL depend on `journal-service`, and `journal-service` SHALL
depend on no other service. Its reads of the ABI API are a soft link, not an ordering edge.

#### Scenario: No ordering edges

- **WHEN** the stack is rendered
- **THEN** no service SHALL list `journal-service` in `depends_on`
- **AND** `journal-service` SHALL have no `depends_on`, ABI included.

#### Scenario: Journal Service stopped

- **WHEN** `journal-service` is stopped
- **THEN** Strategy Runtime, ABI, Strategy Engine, MDS and Research SHALL keep running unchanged.

#### Scenario: ABI unavailable

- **WHEN** ABI is stopped or does not answer while `journal-service` runs
- **THEN** `journal-service` SHALL keep ingesting Runtime events
- **AND** closed-trade rows waiting for ABI facts SHALL stay `incomplete` and be retried.

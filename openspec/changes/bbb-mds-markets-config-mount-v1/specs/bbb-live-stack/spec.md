## ADDED Requirements

### Requirement: MDS Markets Config Is Mounted From The Data Root

The live stack composition SHALL mount `${BBB_DATA_ROOT}/mds` read-only into
`market-data-service` at `/app/config`, in the base composition and in the deploy
composition, and SHALL keep `MDS_MARKETS_CONFIG_PATH=/app/config/markets.toml`, so that
the instrument list is changed by editing `${BBB_DATA_ROOT}/mds/markets.toml` and
restarting that one container, without a new image or a pin change.

#### Scenario: Both compositions render the mount

- **WHEN** the stack is rendered with `BBB_DATA_ROOT`, with and without
  `docker-compose.deploy.yml`
- **THEN** `${BBB_DATA_ROOT}/mds` SHALL mount to `market-data-service` `/app/config`
  read-only
- **AND** no other service SHALL mount that directory
- **AND** the deploy composition SHALL still change images and the `market-data-service`
  volume list only.

#### Scenario: Missing or invalid file

- **WHEN** `${BBB_DATA_ROOT}/mds/markets.toml` is missing or invalid at container start
- **THEN** `market-data-service` SHALL fail at startup with the loader's error
- **AND** SHALL NOT start with an instrument list baked into the image.

#### Scenario: Edit takes effect on restart

- **WHEN** the owner changes `enabled` of an instrument and restarts only
  `market-data-service`
- **THEN** the enabled streams reported by the service SHALL follow the file
- **AND** no image build, pin bump or PR SHALL be needed.

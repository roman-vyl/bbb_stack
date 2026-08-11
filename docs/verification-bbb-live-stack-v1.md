# bbb-live-stack-v1 Verification

Date: 2026-08-11

## Service Baselines

- `roman-vyl/market_data_service` `origin/main`: `0389837df03e48d0ccc17b4255e1f97a33cd5277`
- `roman-vyl/strategy_engine` `origin/main`: `4136d298531ae05c926df7aec04649c9e047c0d9`
- `roman-vyl/strategy_runtime` `origin/main`: `d1872be4531b5a2916d439fa00af9c08d9466220`
- `roman-vyl/abi_executor_bot` `origin/main`: `5420c289590337d8d0e011b900bc2b2c177cff8f`

These match the requested expected baseline after refreshing remote refs.

## Local Worktree Note

The existing sibling service worktrees were not changed for this verification:

- MDS was on `feature/mds-container-production-readiness-v1`, HEAD `3691607f0c6b8a0931a06f25c6d1a54aff0a6f43`.
- Strategy Engine local `main` was behind `origin/main`.
- Strategy Runtime local `main` was behind `origin/main` and had untracked `var/journal/runtime.jsonl`.
- ABI local `main` was behind `origin/main`.

To avoid modifying those service repositories, image build verification used clean
temporary clones in `/private/tmp/bbb-stack-src` checked out at the baseline SHAs.

## Commands Verified

`docker compose config` with `BBB_DATA_ROOT=/private/tmp/bbb-live-stack-verify`:
passed.

`docker compose config` without `BBB_DATA_ROOT`:
failed non-zero with `BBB_DATA_ROOT must be set`.

`docker compose build` with baseline path overrides:
passed for all four images:

- `bbb-stack/market-data-service:local`
- `bbb-stack/strategy-engine:local`
- `bbb-stack/strategy-runtime:local`
- `bbb-stack/abi:local`

## Blocker

`docker compose up -d` was blocked by host port conflicts before full health,
mount, environment, and restart/persistence verification could complete.

Pre-existing containers were publishing required ports:

- `strategy-runtime`: `0.0.0.0:8093->8093/tcp`, `[::]:8093->8093/tcp`
- `market-data-service`: `127.0.0.1:8080->8080/tcp`

The attempted stack start reached healthy `abi` and healthy `strategy-engine`;
`strategy-runtime` failed to start because Docker could not bind host port `8093`.
The partial `bbb_stack` containers were removed with `docker compose down`.

The pre-existing conflicting containers were not stopped.

## OpenSpec Status

`bbb-live-stack-v1` remains active and is not archived because runtime
verification is incomplete.

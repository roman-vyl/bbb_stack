# BBB Stack

System-level deployment and integration repository for the BBB live stack.

This repository owns Docker Compose wiring, system configuration, lifecycle ordering,
system smoke checks, and system-level OpenSpec only. It does not vendor service source,
service Dockerfiles, or application contracts.

## Baseline

- `roman-vyl/market_data_service`: `0389837df03e48d0ccc17b4255e1f97a33cd5277`
- `roman-vyl/strategy_engine`: `4136d298531ae05c926df7aec04649c9e047c0d9`
- `roman-vyl/strategy_runtime`: `d1872be4531b5a2916d439fa00af9c08d9466220`
- `roman-vyl/abi_executor_bot`: `5420c289590337d8d0e011b900bc2b2c177cff8f`

## Usage

Set a data root before rendering or starting the stack:

```sh
export BBB_DATA_ROOT=/tmp/bbb-live-stack
docker compose config
docker compose up --build
```

The four service build contexts default to sibling repositories:

- `MDS_REPO_PATH=../market_data_service`
- `STRATEGY_ENGINE_REPO_PATH=../strategy_engine`
- `STRATEGY_RUNTIME_REPO_PATH=../strategy_runtime`
- `ABI_REPO_PATH=../abi_executor_bot`

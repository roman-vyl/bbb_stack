# bbb-live-stack-v1

## Summary

Create a system-level BBB deployment repository with one minimal Docker Compose
composition for the four existing live services:

- `roman-vyl/market_data_service`
- `roman-vyl/strategy_engine`
- `roman-vyl/strategy_runtime`
- `roman-vyl/abi_executor_bot`

## Goals

- Build all four services from sibling repository contexts.
- Wire service-to-service HTTP through Docker DNS and real container ports.
- Start consumers before the MDS committed-bar producer.
- Require an explicit `BBB_DATA_ROOT` for all durable system data.
- Keep ABI safe by default with dry-run enabled and live trading disabled.
- Publish host ports only on loopback for local integration.

## Non-Goals

- No application contract changes.
- No service Dockerfile changes.
- No source vendoring, Git URL build contexts, or submodules.
- No trading vertical smoke, live/demo trading, order creation, Kubernetes, TLS,
  monitoring, logging stack, CI/CD, image registry publishing, Research Service,
  Workbench, or old `_bbb_new_gen` integration.

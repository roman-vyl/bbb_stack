# bbb-touch-anchor-vertical-smoke-v1

## Why

The ratified four-service Docker stack needs its first business vertical smoke
through the real Runtime, Strategy Engine, MDS, and ABI HTTP/process
boundaries. This change adds system-owned verification only; it does not alter
service APIs, service Dockerfiles, or application behavior.

## What Changes

- Add a system smoke script that starts the existing four-service Compose stack
  with an isolated `BBB_DATA_ROOT`.
- Add a smoke-only Bybit-compatible REST/WebSocket fixture through a Compose
  override, without changing the base four-service Compose contract.
- Reuse the existing Strategy Engine touch-anchor EMA Pullback fixture while
  making MDS reach readiness through its production lower-bound, historical
  reconciliation, continuity, realtime admission, and notifier lifecycle.
- Observe Runtime journal, Engine live-entry result, ABI entry-package
  correlation behavior, and safe-mode execution boundary.
- Record a verification report for the exact boundary reached in safe ABI mode.

## Non-Goals

- No service code, service contract, or canonical service spec changes.
- No bridge between Runtime and Engine.
- No Bybit demo/live trading, API keys, real create-order, or fabricated fill.
- No open-trade management beyond the safe-mode boundary that is actually
  observable.

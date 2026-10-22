## Why

Strategy Runtime now changes the `enabled` field of a deployment file itself
(`strategy_runtime` change `runtime-strategy-enabled-control-v1`, PR #30), by replacing the file
atomically. The stack mounts the deployment catalog into Runtime read-only, so the route
could not write in the real stack.

## What Changes

- `docker-compose.yml`, service `strategy-runtime`: the `${BBB_DATA_ROOT}/strategy-runtime/specs`
  mount at `/runtime/specs` loses `read_only: true`. Nothing else in the stack changes.
- `bbb-live-stack` requirements that name this mount as read-only are modified.
- README: the sentence about the Runtime mount is corrected.

## Non-Goals

No other mount, port, image or pin change. The root filesystem of Runtime stays read-only.
Research stays create-only with `enabled: false`; Runtime writes only the `enabled` field of an
existing file. No deploy: it needs the owner's word, a Runtime image that contains the route, and a
container re-creation.

## Impact

`docker-compose.yml`, `README.md`, `openspec/specs/bbb-live-stack` (on archive).

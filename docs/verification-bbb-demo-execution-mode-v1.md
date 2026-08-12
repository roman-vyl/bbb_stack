# bbb-demo-execution-mode-v1 Verification

Date: 2026-08-12

## Scope

Verified the system-level Bybit Demo Compose override with an empty local secret
file. No order creation endpoints were called.

## Local Secret Permissions

```sh
chmod 700 /Users/mcroma/BBB_secrets
chmod 700 /Users/mcroma/BBB_secrets/abi
chmod 600 /Users/mcroma/BBB_secrets/abi/bybit-demo.env
```

Observed:

```text
drwx------ /Users/mcroma/BBB_secrets
drwx------ /Users/mcroma/BBB_secrets/abi
-rw------- /Users/mcroma/BBB_secrets/abi/bybit-demo.env
```

The secret file was empty during verification.

## Compose Checks

Base config:

```sh
BBB_DATA_ROOT=/Users/mcroma/BBB_data docker compose config
```

Result: rendered successfully without `BBB_SECRETS_ROOT`; ABI remained
`ABI_DRY_RUN=true`, `ABI_LIVE_TRADING_ENABLED=false`, and `BYBIT_ENV=testnet`.

Demo override without `BBB_SECRETS_ROOT`:

```sh
BBB_DATA_ROOT=/Users/mcroma/BBB_data \
  docker compose -f docker-compose.yml -f docker-compose.demo.yml config
```

Result: failed closed with `BBB_SECRETS_ROOT must be set`.

Demo override with `BBB_SECRETS_ROOT`:

```sh
BBB_DATA_ROOT=/Users/mcroma/BBB_data \
BBB_SECRETS_ROOT=/Users/mcroma/BBB_secrets \
  docker compose -f docker-compose.yml -f docker-compose.demo.yml config --quiet
```

Result: rendered successfully.

## Empty-Secret Startup

Started the stack without rebuilding, using the existing local service images:

```sh
BBB_DATA_ROOT=/Users/mcroma/BBB_data \
BBB_SECRETS_ROOT=/Users/mcroma/BBB_secrets \
  docker compose -f docker-compose.yml -f docker-compose.demo.yml up --no-build
```

Observed ABI startup mode:

```json
{
  "dryRun": false,
  "liveTradingEnabled": true,
  "bybitEnvironment": "demo",
  "bybitApiKeyConfigured": false
}
```

Queried only the read-only mode endpoint:

```sh
curl -sS http://127.0.0.1:8787/execution/mode
```

Response:

```json
{
  "dryRun": false,
  "liveTradingEnabled": true,
  "bybitEnvironment": "demo",
  "bybitTestnet": false,
  "bybitApiKeyConfigured": false,
  "bybitApiSecretConfigured": false,
  "canExecuteLive": false,
  "blockedReasons": [
    "BYBIT_API_KEY is required",
    "BYBIT_API_SECRET is required"
  ]
}
```

Result: passed. The Demo override enables ABI Demo execution mode, but empty
credentials keep live execution blocked.

## Notes

`docker compose ... up --build` was not used for final smoke because the local
`../strategy_engine` checkout did not contain a `Dockerfile`. The smoke used
the existing `bbb-stack/strategy-engine:local` image and verified the system
Compose override contract.

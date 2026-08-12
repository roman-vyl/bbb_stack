# Bybit Demo execution smoke v1

Second run date: 2026-08-12 (Europe/Moscow)

## Verdict

`BYBIT_DEMO_EXECUTION_SMOKE_BLOCKED`

Exact first failing boundary in the second run: **PHASE 5 — READ-ONLY
BYBIT DEMO SMOKE**, wallet balance authentication.

The standard ABI read-only smoke reached the real Demo account balance request
and received HTTP `502` from ABI with the sanitized upstream error:

```text
Bybit retCode 10003: API key is invalid.
```

This is an explicit credential/authentication failure and therefore a mandatory
STOP boundary. No entry package or other write/order request was sent. No
production code was changed.

The earlier PHASE 1 BLOCKED result remains preserved in Git history in commit
`85349cfe3ebdf33d587423cac43bdcb614ba9e24`.

## 1. Repository synchronization and exact SHAs

These are the exact source SHAs used by the second run, before this report-only
update:

| Repository | Verified SHA |
| --- | --- |
| `bbb_stack` | `85349cfe3ebdf33d587423cac43bdcb614ba9e24` |
| `market_data_service` | `0389837df03e48d0ccc17b4255e1f97a33cd5277` |
| `strategy_engine` | `4136d298531ae05c926df7aec04649c9e047c0d9` |
| `strategy_runtime` | `d1872be4531b5a2916d439fa00af9c08d9466220` |
| `abi_executor_bot` | `77559c272b69709702ea80e896a69f835862e868` |

The first run fetched all repositories and proved that their source commits
matched `origin/main`. The only subsequent source-tree change was the allowed
`bbb_stack` verification report commit above.

The existing untracked file
`strategy_runtime/var/journal/runtime.jsonl` remained untouched and was not
added to Git. No service commits were created.

## 2. Secret and Compose preflight

| Check | Result |
| --- | --- |
| `/Users/mcroma/BBB_secrets` mode | PASS (`700`) |
| `/Users/mcroma/BBB_secrets/abi` mode | PASS (`700`) |
| `bybit-demo.env` mode | PASS (`600`) |
| Credential file non-empty | PASS |
| Exactly two assignments | PASS |
| `BYBIT_API_KEY` present exactly once and non-empty | PASS |
| `BYBIT_API_SECRET` present exactly once and non-empty | PASS |
| Compose Demo `config --quiet` | PASS |

Only assignment names and boolean validation results were inspected. Credential
values, lengths, prefixes, and suffixes were not emitted. Rendered Compose
configuration was not printed.

## 3. Build and health

The required command was executed with the Demo override:

```text
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build
```

All four current service build definitions and contexts were processed; Docker
reported all four images built. Existing valid layers were reused by Docker's
build cache. The resulting image IDs were:

| Service | Image ID |
| --- | --- |
| `market-data-service` | `0d00adb376dd` |
| `strategy-engine` | `fce0bd4e7688` |
| `strategy-runtime` | `7ca97dd6f37b` |
| `abi` | `b5ac89ba4752` |

All four containers reached Docker `healthy`. All required host endpoints then
returned HTTP `200`:

| Endpoint | Sanitized result |
| --- | --- |
| MDS `/health` | `healthy` |
| Engine `/health` | `ok` |
| Runtime `/health/live` | `live` |
| Runtime `/health/ready` | `ready` |
| ABI `/health` | `ok=true`, `entryPackageReady=true` |

## 4. ABI execution mode

`GET /execution/mode` returned HTTP `200` with:

| Field | Value |
| --- | --- |
| `dryRun` | `false` |
| `liveTradingEnabled` | `true` |
| `bybitEnvironment` | `demo` |
| `canExecuteLive` | `true` |
| credential configuration flags | both `true` |
| `blockedReasons` | empty |

No credential values were returned or recorded.

## 5. Read-only Demo verification

The required existing smoke was run from `abi_executor_bot`:

```text
ABI_BASE_URL=http://127.0.0.1:8787 npm run smoke:sandbox:read
```

Results:

| Check | Result |
| --- | --- |
| ABI health | PASS |
| Demo mode guard | PASS (`demo`, `canExecuteLive=true`) |
| Demo authentication | **FAIL** |
| Balance endpoint | **FAIL**, ABI HTTP `502`; Bybit retCode `10003` |
| Active orders | Not queried; smoke stopped at balance |
| Open positions | Not queried; smoke stopped at balance |

One additional read-only balance request reproduced the same sanitized failure.
No full account payload was printed. Raw ABI container logs were not read because
they could contain sensitive request material.

## 6. Canonical-path and pre-trade gate

Not reached. Because authentication failed in PHASE 5, the task prohibited
continuing to canonical close-path discovery or any pre-trade exchange checks.

## 7. Trade fixture

Not created. No symbol, side, prices, risk multiplier, calculated quantity,
notional, `strategy_instance_id`, or `trade_cycle_id` was selected.

## 8. Entry result

No entry-package request was sent.

## 9. Exchange-confirmed fill evidence

Not applicable; no order was submitted.

## 10. Position/open-position evidence

Not applicable; no order was submitted and no position was opened by this run.

## 11. Initial protection evidence

Not applicable; no entry was created.

## 12. Close evidence

Not applicable; this run created no position to close.

## 13. Final zero-position/no-active-orders evidence

Global Demo account cleanliness could not be authenticated and is therefore not
claimed. This run sent no write/order requests, so it created no test position,
entry order, stop, or take-profit order.

## 14. ABI restart and durable correlation evidence

Not reached. The correlation store was not modified or dumped, and an ABI-only
restart was not performed because the lifecycle never reached a closed trade.

## 15. Shutdown

The four-service stack was stopped with the required Compose files. Containers
and the Compose network were removed, and a final `compose ps -a` returned no
containers. Persistent `BBB_DATA_ROOT` data was not deleted.

## Required external remediation before another run

Verify that the supplied API key is a currently valid **Bybit Demo Trading** key
for the Demo API domain selected by `BYBIT_ENV=demo`, and that the key/secret
pair belongs together. Do not switch this verification to mainnet or testnet and
do not disable the ABI live-execution guard.

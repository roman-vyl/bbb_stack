# Bybit Demo execution smoke v1

Third run date: 2026-08-12 (Europe/Moscow)

## Verdict

`BYBIT_DEMO_EXECUTION_SMOKE_BLOCKED`

Exact first failing boundary in the third run: **PHASE 10 — canonical ABI
protection application**.

The entry order filled, the position opened, and the entry-attached stop and
take-profit were independently visible in Bybit position state. A subsequent
canonical protection request for those same values returned ABI HTTP `500`:

```text
error.code=internal_error
```

No retry or production-code change was attempted. The position was immediately
closed through the canonical ABI close endpoint, final exchange cleanliness was
confirmed, ABI durability was checked after restart, and the stack was stopped.

## Run history

| Run | Result | First failing boundary | Audit commit |
| --- | --- | --- | --- |
| 1 | BLOCKED | PHASE 1: extra `BYBIT_TESTNET` assignment in the secret file | `85349cfe3ebdf33d587423cac43bdcb614ba9e24` |
| 2 | BLOCKED | PHASE 5: Bybit Demo balance authentication returned retCode `10003` | `99986521aabc5d15f9c49c82a9f71d7e1b5a50b1` |
| 3 | BLOCKED | PHASE 10: canonical protection PUT returned HTTP `500 internal_error` | this report-only update |

## 1. Repository synchronization and exact SHAs

All five repositories were fetched before the third run. Every repository was
on `main`, matched `origin/main`, and had no tracked modifications. These are
the exact source SHAs used, before this report-only update:

| Repository | Verified SHA |
| --- | --- |
| `bbb_stack` | `99986521aabc5d15f9c49c82a9f71d7e1b5a50b1` |
| `market_data_service` | `0389837df03e48d0ccc17b4255e1f97a33cd5277` |
| `strategy_engine` | `4136d298531ae05c926df7aec04649c9e047c0d9` |
| `strategy_runtime` | `d1872be4531b5a2916d439fa00af9c08d9466220` |
| `abi_executor_bot` | `77559c272b69709702ea80e896a69f835862e868` |

The four service source SHAs were unchanged from run 2. Per the third-run
instruction, existing current images were reused and `up -d` was used without
another rebuild. The existing untracked
`strategy_runtime/var/journal/runtime.jsonl` remained untouched and was not
added to Git. No service commits were created.

## 2. Secret preflight

| Check | Result |
| --- | --- |
| `/Users/mcroma/BBB_secrets` mode | PASS (`700`) |
| `/Users/mcroma/BBB_secrets/abi` mode | PASS (`700`) |
| `bybit-demo.env` mode | PASS (`600`) |
| Credential file non-empty | PASS |
| Exactly two assignments | PASS |
| `BYBIT_API_KEY` present exactly once and non-empty | PASS |
| `BYBIT_API_SECRET` present exactly once and non-empty | PASS |

Only assignment names and boolean validation results were inspected. No secret
value, length, prefix, suffix, or rendered Compose configuration was printed.

## 3. Startup and health

Because all service source SHAs were unchanged, the stack was started with the
required existing images:

```text
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d
```

All four containers reached Docker `healthy`. Required host endpoints returned
HTTP `200`:

| Endpoint | Sanitized result |
| --- | --- |
| MDS `/health` | `healthy` |
| Engine `/health` | `ok` |
| Runtime `/health/live` | `live` |
| Runtime `/health/ready` | `ready` |
| ABI `/health` | `ok=true`, `entryPackageReady=true` |

## 4. ABI execution mode

Before entry, protection, and close writes, the guard was checked and reported:

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

The required existing smoke completed successfully:

```text
ABI_BASE_URL=http://127.0.0.1:8787 npm run smoke:sandbox:read
```

| Check | Result |
| --- | --- |
| Authentication | PASS |
| Balance endpoint | PASS (`status=ok`) |
| Active BTCUSDT orders | PASS, count 0 |
| Open BTCUSDT positions | PASS, live position count 0 (flat placeholder row) |

No full account payload was printed.

## 6. Canonical path and pre-trade cleanliness

The implemented V1 paths were established from current OpenAPI, routes, and
application services before opening a position:

| Operation | Canonical ABI path |
| --- | --- |
| Entry package | `PUT /v1/strategy-instances/{id}/trade-cycles/{cycle}/entry-package` |
| Pair position | `GET /v1/strategy-instances/{id}/trade-cycles/{cycle}/open-position` |
| Protection | `PUT /v1/strategy-instances/{id}/trade-cycles/{cycle}/protection` |
| Full close | `DELETE /v1/strategy-instances/{id}/trade-cycles/{cycle}/open-position`, empty body |

The close implementation neutralizes the attributed entry order, queries the
actual remainder, sends a market reduce-only close when required, verifies both
zero position and terminal order state, and only then persists
`terminal_closed`.

For XRPUSDT, account reads confirmed zero active orders and zero position size.
No existing correlation record owned that scope.

## 7. Trade fixture

| Field | Value |
| --- | --- |
| Symbol / Runtime ticker | `XRPUSDT` / `XRPUSDT.P` |
| Side / trigger semantics | long / `falls_to` |
| Observed last price | `1.0101` |
| Tick size | `0.0001` |
| Minimum quantity / quantity step | `0.1` / `0.1` |
| Minimum notional | `5 USDT` |
| Planned entry | `1.0100` |
| Initial stop | `1.0000` |
| Initial take | `1.0200` |
| Risk multiplier | `0.01` |
| ABI V1 calculated quantity | `5 XRP` |
| Approximate planned notional | `5.05 USDT` |
| `strategy_instance_id` | `demo-execution-smoke-1786556267` |
| `trade_cycle_id` | `demo-cycle-1786556267` |

The quantity was predicted using the production V1 formula: the greater of
minimum quantity and minimum-notional quantity, rounded upward to quantity
step. The predicted result was `5.0`; ABI returned the numerically identical
`5`. The bounded notional was below the `25 USDT` safety limit.

## 8. Entry result

Exactly one public ABI entry-package request was sent. No automatic retry was
performed.

| Evidence | Result |
| --- | --- |
| HTTP status | `200` |
| Public status | `entry_package_applied` |
| Calculated quantity | `5` |
| Order link ID | `abi-ep-baf1ad56e79c833d5ade` |
| Exchange order ID | `0108d674-e18e-4493-90b2-683a7d8ce33f` |

## 9. Exchange-confirmed fill and open position

The pair-scoped ABI endpoint returned HTTP `200`, `position_open=true`, first
fill timestamp `1786556310754`, and average entry price `1.01`.

ABI has no public pair-scoped order-history route, so a permitted signed Bybit
Demo **read-only** history request was used for independent exchange evidence.
It returned retCode `0` and the matching identifiers with:

| Field | Value |
| --- | --- |
| Order status | `Filled` |
| Quantity / cumulative executed | `5` / `5` |
| Average fill price | `1.01` |
| Side | `Buy` |

The durable correlation record was `applied` and bound the test pair to the same
order link ID, exchange order ID, symbol, and quantity.

## 10. Initial protection and failing boundary

After fill, the Bybit position read returned size `5`, side `Buy`, average price
`1.01`, stop loss `1`, and take profit `1.02`. This independently confirmed
that the entry-attached initial protection package existed on the exchange.

The canonical protection endpoint was then called once with the numerically
identical accepted levels:

```json
{"stop_price":"1.0000","take_price":"1.0200"}
```

Result: HTTP `500`, public error code `internal_error`. The request was not
retried. No production code was modified, and no direct Bybit write was used to
work around the failure.

## 11. Close evidence

The execution guard was rechecked, then the canonical ABI close endpoint was
called with an empty body:

| Evidence | Result |
| --- | --- |
| HTTP status | `200` |
| Public status | `trade_cycle_closed` |
| Pair correlation | matching test identifiers |

The close response is only emitted by current ABI after it verifies both zero
position and no attributed active entry order.

## 12. Final clean state

Fresh post-close reads confirmed:

| Check | Result |
| --- | --- |
| Pair-scoped `position_open` | `false` |
| XRPUSDT position size | `0` |
| XRPUSDT active orders | count `0` |
| Stop / take on flat row | absent |
| Correlation status | `terminal_closed` |
| Correlation pending action | `null` |

The correlation file was read only for this test pair and was not rewritten or
dumped wholesale.

## 13. ABI restart and durability

Only the ABI container was restarted after cleanup. ABI returned to `healthy`;
execution mode remained Demo with `canExecuteLive=true`. After replay:

- correlation remained `terminal_closed` with the same order identifiers;
- pair-scoped `position_open` remained `false`;
- XRPUSDT position size remained `0`;
- XRPUSDT active-order count remained `0`.

## 14. Shutdown

The full stack was stopped with the two required Compose files. Containers and
the Compose network were removed; final `compose ps -a` was empty. Persistent
`BBB_DATA_ROOT` data was not deleted.

## Narrow follow-up proposal

Open a narrowly scoped specification/investigation for idempotent canonical
protection application when the requested stop/take values already match the
exchange-confirmed position state. It should first capture a sanitized upstream
classification for this exact HTTP `500`, then specify whether an already-equal
fresh readback earns `protection_applied` without an exchange mutation or
whether a specific non-mutating Bybit response must be treated as success. No
broader retry, recovery, contract, or execution refactor is justified by this
run.

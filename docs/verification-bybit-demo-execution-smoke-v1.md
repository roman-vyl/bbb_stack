# Bybit Demo execution smoke v1

Date: 2026-08-12 (Europe/Moscow)

## Verdict

`BYBIT_DEMO_EXECUTION_SMOKE_BLOCKED`

Exact first failing boundary: **PHASE 1 — SECRET PREFLIGHT**.

The Demo credential file has the required permissions and contains both required,
non-empty credential variables, but it also contains an additional assignment
named `BYBIT_TESTNET`. This does not satisfy the requested exact credential
contract consisting of `BYBIT_API_KEY` and `BYBIT_API_SECRET` only. No secret
values, lengths, prefixes, or suffixes were printed or copied.

Per the task STOP policy, Compose validation, rebuild, service startup, account
requests, and trading operations were not attempted after this boundary.

## 1. Repository synchronization and exact SHAs

All five repositories were fetched from `origin`. Each was on `main`, had no
tracked worktree modifications, and matched `origin/main` exactly (ahead 0,
behind 0):

| Repository | Final SHA |
| --- | --- |
| `bbb_stack` | `f8b0d7e8a4096409c6cff41fcec7575ca8eb88b1` |
| `market_data_service` | `0389837df03e48d0ccc17b4255e1f97a33cd5277` |
| `strategy_engine` | `4136d298531ae05c926df7aec04649c9e047c0d9` |
| `strategy_runtime` | `d1872be4531b5a2916d439fa00af9c08d9466220` |
| `abi_executor_bot` | `77559c272b69709702ea80e896a69f835862e868` |

The existing untracked file
`strategy_runtime/var/journal/runtime.jsonl` was preserved and was not added to
Git.

No service commits were created.

## 2. Secret preflight

| Check | Result |
| --- | --- |
| `/Users/mcroma/BBB_secrets` mode | PASS (`700`) |
| `/Users/mcroma/BBB_secrets/abi` mode | PASS (`700`) |
| `bybit-demo.env` mode | PASS (`600`) |
| Credential file non-empty | PASS |
| `BYBIT_API_KEY` present exactly once and non-empty | PASS |
| `BYBIT_API_SECRET` present exactly once and non-empty | PASS |
| Exact two-variable credential contract | **FAIL** — additional assignment `BYBIT_TESTNET` present |

Only assignment names and boolean validation results were inspected. Credential
values were not emitted.

## 3. Build and health

Not run because PHASE 1 failed. Therefore this run does not claim that images
were rebuilt or that the four containers were healthy.

## 4. ABI execution mode

Not queried because PHASE 1 failed. No claims are made for `dryRun`,
`liveTradingEnabled`, `bybitEnvironment`, or `canExecuteLive`.

## 5. Read-only Demo verification

Not run because PHASE 1 failed. Authentication, balance, active-order count,
and open-position count remain unverified in this run.

## 6. Trade fixture

Not created. No symbol, side, prices, risk multiplier, quantity, notional,
`strategy_instance_id`, or `trade_cycle_id` was selected because the safety gate
failed before any market or account request.

## 7. Entry result

No entry-package request was sent.

## 8. Exchange-confirmed fill evidence

Not applicable; no order was submitted.

## 9. Position/open-position evidence

Not applicable; no order was submitted and no position was opened by this run.

## 10. Initial protection evidence

Not applicable; no entry was created.

## 11. Close evidence

Not applicable; this run created no position to close.

## 12. Final zero-position/no-active-orders evidence

No account read was performed after the PHASE 1 failure, so global Demo account
cleanliness is not claimed. This run itself sent no write/order requests and
therefore created no test position, entry order, stop, or take-profit order.

## 13. ABI restart and durable correlation evidence

Not run because the stack was not started. The correlation store was not
modified or dumped.

## Required remediation before a new verification run

Make the secret file satisfy the exact credential-only contract requested for
this smoke: retain only the two required credential assignments and keep
execution mode in the Compose Demo override. This report does not modify the
secret file because the task authorizes verification, not secret mutation.

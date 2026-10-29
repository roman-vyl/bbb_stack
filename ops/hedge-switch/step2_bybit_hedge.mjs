// Step 2: inside the running abi container, using ABI's own config and Bybit
// adapter (keys never printed). Checks that Bybit has no open positions and no
// active orders and that ABI has no active records, then (APPLY=1 only)
// switches all USDT linear contracts to hedge mode (mode 3) and verifies.
// Refuses anything but BYBIT_ENV=demo.
//
// Usage (Mac host):
//   docker exec -i bbb_stack-abi-1 node --input-type=module < step2_bybit_hedge.mjs
//   docker exec -i -e APPLY=1 bbb_stack-abi-1 node --input-type=module < step2_bybit_hedge.mjs
import { readFileSync } from "node:fs";

const { loadConfig } = await import("/app/dist/config/config.js");
const { RestBybitAdapter } = await import("/app/dist/exchange/bybitAdapter.js");

const config = loadConfig(process.env);
if (config.bybitEnvironment !== "demo") {
  console.log("STOP: BYBIT_ENV is not demo:", config.bybitEnvironment);
  process.exit(2);
}
const bybit = new RestBybitAdapter(config);
const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT", "BCHUSDT", "LINKUSDT", "TRXUSDT", "HYPEUSDT"];
// Same set as ABI isDurablyClosedEntryPackageStatus; anything else blocks hedge startup.
const TERMINAL = new Set(["absent", "terminal_unfilled", "terminal_closed"]);

const list = (r) => (r && r.retCode === 0 && Array.isArray(r.result?.list) ? r.result.list : null);

// ABI durable memory: last line per pair
const last = new Map();
for (const line of readFileSync("/app/var/abi_entry_package_correlation.jsonl", "utf8").split("\n")) {
  if (!line.trim()) continue;
  try {
    const r = JSON.parse(line);
    last.set(`${r.strategy_instance_id}|${r.trade_cycle_id}`, r);
  } catch {}
}
const active = [...last.values()].filter((r) => !TERMINAL.has(r.status));
console.log("ABI active records:", active.length);
for (const r of active) console.log("  ", r.strategy_instance_id, r.exchange_symbol, r.status, r.position_binding_mode);

const positions = list(await bybit.getOpenPositions({ category: "linear", settleCoin: "USDT" }));
const orders = list(await bybit.getActiveOrders({ category: "linear", settleCoin: "USDT" }));
if (positions === null || orders === null) {
  console.log("STOP: Bybit read failed");
  process.exit(2);
}
const open = positions.filter((p) => Number(p.size) > 0);
console.log("Bybit open positions:", open.map((p) => `${p.symbol} ${p.side} ${p.size} idx${p.positionIdx}`));
console.log("Bybit active orders:", orders.map((o) => `${o.symbol} ${o.side} ${o.orderType} ${o.orderStatus}`));

if (active.length || open.length || orders.length) {
  console.log("STOP: not flat, nothing switched");
  process.exit(1);
}
if (process.env.APPLY !== "1") {
  console.log("Flat. Dry run: set APPLY=1 to switch to hedge.");
  process.exit(0);
}

const res = await bybit.signedPost("/v5/position/switch-mode", { category: "linear", coin: "USDT", mode: 3 });
console.log("switch-mode:", res?.retCode, res?.retMsg);

let ok = true;
for (const symbol of SYMBOLS) {
  const rows = list(await bybit.getOpenPositions({ category: "linear", symbol }));
  const idx = rows ? rows.map((p) => p.positionIdx).sort().join(",") : "read failed";
  if (idx !== "1,2") ok = false;
  console.log(`  ${symbol}: positionIdx ${idx}`);
}
console.log(ok ? "HEDGE VERIFIED on all symbols" : "NOT all symbols in hedge");
process.exit(ok ? 0 : 1);

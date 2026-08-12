#!/usr/bin/env python3
"""Minimal Bybit-compatible REST/WS fixture for the touch-anchor smoke."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.server import serve


STEP_MS = 300_000
HISTORY_BARS = 12
SYMBOL = "BTCUSDT"
TOPIC = f"kline.5.{SYMBOL}"


@dataclass
class FixtureState:
    launch_time_ms: int
    max_rest_open_served: int | None = None
    websocket_trigger_open_time_ms: int | None = None
    websocket_sent: bool = False

    def row_for_open(self, open_time_ms: int) -> list[str]:
        index = ((open_time_ms - self.launch_time_ms) // STEP_MS) + 1
        return [
            str(open_time_ms),
            str(index),
            str(index + 1),
            str(index - 1),
            str(index),
            "10",
            "0",
        ]

    def ws_row_for_open(self, open_time_ms: int) -> dict[str, object]:
        index = ((open_time_ms - self.launch_time_ms) // STEP_MS) + 1
        return {
            "start": open_time_ms,
            "end": open_time_ms + STEP_MS - 1,
            "interval": "5",
            "open": str(index),
            "high": str(index + 1),
            "low": str(index - 1),
            "close": str(index),
            "volume": "10",
            "turnover": "0",
            "confirm": True,
            "timestamp": int(time.time() * 1000),
        }


class StateStore:
    def __init__(self, state: FixtureState, path: Path) -> None:
        self._state = state
        self._path = path
        self._lock = threading.Lock()
        self.write()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return self.snapshot_locked()

    def snapshot_locked(self) -> dict[str, object]:
        return {
            "symbol": SYMBOL,
            "topic": TOPIC,
            "timeframe": "5m",
            "launch_time_ms": self._state.launch_time_ms,
            "max_rest_open_served": self._state.max_rest_open_served,
            "websocket_trigger_open_time_ms": self._state.websocket_trigger_open_time_ms,
            "websocket_sent": self._state.websocket_sent,
        }

    def instrument_payload(self) -> dict[str, object]:
        return {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "category": "linear",
                "list": [
                    {
                        "symbol": SYMBOL,
                        "contractType": "LinearPerpetual",
                        "status": "Trading",
                        "settleCoin": "USDT",
                        "launchTime": str(self._state.launch_time_ms),
                    }
                ],
            },
        }

    def kline_payload(self, start_ms: int, end_ms_inclusive: int, limit: int) -> dict[str, object]:
        if limit <= 0 or limit > 1000:
            return {"retCode": 10001, "retMsg": "invalid limit", "result": {"list": []}}
        end_exclusive = end_ms_inclusive + 1
        rows: list[list[str]] = []
        open_time = start_ms - (start_ms % STEP_MS)
        if open_time < start_ms:
            open_time += STEP_MS
        while open_time < end_exclusive and len(rows) < limit:
            if open_time >= self._state.launch_time_ms:
                rows.append(self._state.row_for_open(open_time))
            open_time += STEP_MS
        with self._lock:
            if rows:
                self._state.max_rest_open_served = max(
                    int(row[0]) for row in rows
                )
            self.write_locked()
        # Bybit returns newest first. MDS parser sorts ascending after parsing.
        return {"retCode": 0, "retMsg": "OK", "result": {"category": "linear", "list": rows[::-1]}}

    def mark_websocket_sent(self, open_time_ms: int) -> None:
        with self._lock:
            self._state.websocket_trigger_open_time_ms = open_time_ms
            self._state.websocket_sent = True
            self.write_locked()

    def next_trigger_open_time_ms(self) -> int:
        with self._lock:
            if self._state.max_rest_open_served is None:
                return self._state.launch_time_ms + HISTORY_BARS * STEP_MS
            return self._state.max_rest_open_served + STEP_MS

    def write(self) -> None:
        with self._lock:
            self.write_locked()

    def write_locked(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self.snapshot_locked(), indent=2, sort_keys=True),
            encoding="utf-8",
        )


def aligned_launch_time() -> int:
    now_ms = int(time.time() * 1000)
    current_open = now_ms - (now_ms % STEP_MS)
    return current_open - HISTORY_BARS * STEP_MS


def make_handler(store: StateStore) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            if parsed.path == "/health":
                self.send_json(200, {"ok": True, **store.snapshot()})
                return
            if parsed.path == "/state":
                self.send_json(200, store.snapshot())
                return
            if parsed.path == "/v5/market/instruments-info":
                if params.get("category", [""])[0] != "linear" or params.get("symbol", [""])[0] != SYMBOL:
                    self.send_json(200, {"retCode": 10001, "retMsg": "unsupported instrument", "result": {"list": []}})
                    return
                self.send_json(200, store.instrument_payload())
                return
            if parsed.path == "/v5/market/kline":
                try:
                    if params.get("category", [""])[0] != "linear":
                        raise ValueError("category")
                    if params.get("symbol", [""])[0] != SYMBOL:
                        raise ValueError("symbol")
                    if params.get("interval", [""])[0] != "5":
                        raise ValueError("interval")
                    start_ms = int(params["start"][0])
                    end_ms = int(params["end"][0])
                    limit = int(params["limit"][0])
                except (KeyError, ValueError):
                    self.send_json(200, {"retCode": 10001, "retMsg": "bad kline request", "result": {"list": []}})
                    return
                self.send_json(200, store.kline_payload(start_ms, end_ms, limit))
                return
            self.send_json(404, {"error": "not_found", "path": parsed.path})

        def log_message(self, fmt: str, *args: object) -> None:
            print("fixture_http " + (fmt % args), flush=True)

        def send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


async def websocket_handler(connection: Any, store: StateStore) -> None:
    raw = await connection.recv()
    try:
        subscribe = json.loads(raw)
        topics = subscribe["args"]
    except Exception:
        topics = [TOPIC]
    await connection.send(
        json.dumps(
            {
                "req_id": "subscribe-1",
                "op": "subscribe",
                "success": True,
                "ret_msg": "subscribe",
                "data": {"successTopics": topics},
            }
        )
    )
    await asyncio.sleep(1.0)
    trigger_open = store.next_trigger_open_time_ms()
    await connection.send(
        json.dumps(
            {
                "topic": TOPIC,
                "type": "snapshot",
                "ts": int(time.time() * 1000),
                "data": [store._state.ws_row_for_open(trigger_open)],
            }
        )
    )
    store.mark_websocket_sent(trigger_open)
    while True:
        try:
            message = await connection.recv()
        except Exception:
            return
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            continue
        if payload.get("op") == "ping":
            await connection.send(json.dumps({"op": "pong"}))
        elif payload.get("op") == "unsubscribe":
            await connection.send(
                json.dumps(
                    {
                        "req_id": payload.get("req_id", "unsubscribe-1"),
                        "op": "unsubscribe",
                        "success": True,
                        "ret_msg": "unsubscribe",
                        "data": {"successTopics": payload.get("args", [TOPIC])},
                    }
                )
            )
            return


async def main() -> None:
    state_path = Path(os.environ.get("BYBIT_FIXTURE_STATE_PATH", "/fixture-state/state.json"))
    store = StateStore(FixtureState(launch_time_ms=aligned_launch_time()), state_path)
    http_host = os.environ.get("BYBIT_FIXTURE_HTTP_HOST", "0.0.0.0")
    http_port = int(os.environ.get("BYBIT_FIXTURE_HTTP_PORT", "8088"))
    ws_host = os.environ.get("BYBIT_FIXTURE_WS_HOST", "0.0.0.0")
    ws_port = int(os.environ.get("BYBIT_FIXTURE_WS_PORT", "8089"))

    httpd = ThreadingHTTPServer((http_host, http_port), make_handler(store))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(name, stop.set)
        except NotImplementedError:
            pass
    async with serve(lambda conn: websocket_handler(conn, store), ws_host, ws_port):
        print(
            f"fixture_ready rest=http://{http_host}:{http_port} ws=ws://{ws_host}:{ws_port}",
            flush=True,
        )
        await stop.wait()
    httpd.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

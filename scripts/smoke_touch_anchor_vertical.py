#!/usr/bin/env python3
"""Run the BBB touch-anchor vertical smoke against the four-service stack.

This is an orchestration/observation script for bbb_stack. It prepares an
isolated BBB_DATA_ROOT, starts the ratified Docker Compose stack with a
smoke-only Bybit-compatible upstream fixture, waits for MDS to emit a genuine
committed-bar webhook, and reports the first real boundary reached.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TICKER = "BTCUSDT.P"
TIMEFRAME = "5m"
STEP_MS = 300_000
STRATEGY_ID = "ema_pullback"

RAW_SPEC: dict[str, Any] = {
    "anchor_stack": {
        "fast": {"source": "close", "timeframe": "base", "period": 2},
        "anchor": {"source": "close", "timeframe": "base", "period": 3},
        "slow": {"source": "close", "timeframe": "base", "period": 5},
    },
    "trade_sides": {"enabled": ["long"]},
    "components": {"blockers": [], "trigger": {"component_id": "touch_anchor"}},
    "setups": [],
    "contexts": {},
    "trade_management": {
        "exit_policy": {
            "always_on": {
                "exits": [
                    {
                        "instance_id": "initial-stop",
                        "component_id": "constant_usd_stop_loss",
                        "exit_kind": "stop_loss",
                        "usd_distance": 0.25,
                    },
                    {
                        "instance_id": "initial-take",
                        "component_id": "constant_usd_take_profit",
                        "exit_kind": "take_profit",
                        "usd_distance": 0.5,
                    },
                ]
            },
            "profiles": {
                "aligned": {"exits": []},
                "countertrend": {"exits": []},
                "neutral": {"exits": []},
            },
        },
        "exit_management": {},
    },
}


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: dict[str, Any]


class SmokeFailure(RuntimeError):
    pass


def main() -> int:
    if sys.version_info < (3, 11):
        raise SmokeFailure("Python 3.11+ is required")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", default="bbb-touch-anchor-smoke")
    parser.add_argument("--keep-running", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()

    defaults_root = Path("/private/tmp/bbb-stack-src")
    mds_repo = Path(os.environ.get("MDS_REPO_PATH", defaults_root / "market_data_service"))
    engine_repo = Path(
        os.environ.get("STRATEGY_ENGINE_REPO_PATH", defaults_root / "strategy_engine")
    )
    runtime_repo = Path(
        os.environ.get("STRATEGY_RUNTIME_REPO_PATH", defaults_root / "strategy_runtime")
    )
    abi_repo = Path(os.environ.get("ABI_REPO_PATH", defaults_root / "abi_executor_bot"))
    for path in (mds_repo, engine_repo, runtime_repo, abi_repo):
        if not path.exists():
            raise SmokeFailure(f"repository path does not exist: {path}")

    smoke_root = Path(
        os.environ.get(
            "BBB_TOUCH_ANCHOR_SMOKE_ROOT",
            tempfile.mkdtemp(prefix="bbb-touch-anchor-smoke-", dir="/private/tmp"),
        )
    )
    create_smoke_layout(smoke_root)
    write_runtime_deployment(smoke_root)
    write_mds_smoke_market_config(smoke_root)

    env = os.environ.copy()
    env.update(
        {
            "BBB_DATA_ROOT": str(smoke_root),
            "MDS_REPO_PATH": str(mds_repo),
            "STRATEGY_ENGINE_REPO_PATH": str(engine_repo),
            "STRATEGY_RUNTIME_REPO_PATH": str(runtime_repo),
            "ABI_REPO_PATH": str(abi_repo),
        }
    )

    report: dict[str, Any] = {
        "smoke_root": str(smoke_root),
        "ticker": TICKER,
        "timeframe": TIMEFRAME,
        "trigger_mode": "MDS-originated via fixture WebSocket -> MDS notifier",
        "fixture": "strategy_engine tests/test_live_entry_projection.py touch_anchor fixture",
    }

    try:
        compose(args, env, "config", check=True)
        compose(args, env, "up", "-d", "--build", check=True)
        wait_for_stack(args, env, args.timeout_seconds)
        wait_for_mds_ready(args.timeout_seconds)

        health = {
            "mds_health": get_json("http://127.0.0.1:8080/health").body,
            "mds_readiness": get_json("http://127.0.0.1:8080/readiness").body,
            "engine_health": get_json("http://127.0.0.1:8090/health").body,
            "runtime_live": get_json("http://127.0.0.1:8093/health/live").body,
            "runtime_ready": get_json("http://127.0.0.1:8093/health/ready").body,
            "abi_health": get_json("http://127.0.0.1:8787/health").body,
            "abi_execution_mode": get_json("http://127.0.0.1:8787/execution/mode").body,
        }
        report["health"] = health
        assert_abi_safe_mode(health["abi_execution_mode"])

        fixture_state = wait_for_fixture_trigger(
            smoke_root / "bybit-fixture" / "state.json",
            args.timeout_seconds,
        )
        report["bybit_fixture"] = fixture_state
        trigger_open_time_ms = int(fixture_state["websocket_trigger_open_time_ms"])
        launch_time_ms = int(fixture_state["launch_time_ms"])
        report["trigger_open_time_ms"] = trigger_open_time_ms

        journal_path = smoke_root / "strategy-runtime" / "journal" / "runtime.jsonl"
        records = wait_for_runtime_journal(
            journal_path,
            trigger_open_time_ms,
            args.timeout_seconds,
        )
        report["runtime_journal"] = summarize_journal(records)

        mds_window_result = get_json(
            "http://127.0.0.1:8080/v1/candles?"
            + urllib.parse.urlencode(
                {
                    "ticker": TICKER,
                    "timeframe": TIMEFRAME,
                    "from_ms": launch_time_ms,
                    "to_ms": trigger_open_time_ms + STEP_MS,
                }
            )
        )
        if mds_window_result.status != 200:
            report["mds_window"] = {
                "status": mds_window_result.status,
                "body": mds_window_result.body,
            }
            report["boundary"] = "MDS_STREAM_NOT_READY_AFTER_FIXTURE_LIFECYCLE"
            print(json.dumps(report, indent=2, sort_keys=True))
            raise SmokeFailure(
                "MDS did not serve the fixture lifecycle window through /v1/candles"
            )
        mds_window = mds_window_result.body
        expected_candles = ((trigger_open_time_ms - launch_time_ms) // STEP_MS) + 1
        if len(mds_window.get("candles", [])) != expected_candles:
            raise SmokeFailure(
                f"MDS returned unexpected candle count expected={expected_candles}: {mds_window}"
            )
        report["mds_window"] = {
            "from_ms": mds_window["from_ms"],
            "to_ms": mds_window["to_ms"],
            "candle_count": len(mds_window["candles"]),
            "market_data_hash": mds_window["market_data_hash"],
        }

        engine_result = post_json(
            "http://127.0.0.1:8090/v1/strategy-evaluations/live-entry",
            {
                "strategy_id": STRATEGY_ID,
                "raw_spec": RAW_SPEC,
                "ticker": TICKER,
                "base_timeframe": TIMEFRAME,
                "target_bar_open_time_ms": trigger_open_time_ms,
            },
        )
        if engine_result.status != 200:
            raise SmokeFailure(f"Engine live-entry failed: {engine_result}")
        desired_entry = engine_result.body.get("desired_entry")
        if not isinstance(desired_entry, dict):
            raise SmokeFailure(f"Engine did not return desired_entry: {engine_result.body}")
        if desired_entry.get("side") != "long":
            raise SmokeFailure(f"unexpected desired_entry side: {desired_entry}")
        if desired_entry.get("source_plan_bar_open_time_ms") != trigger_open_time_ms:
            raise SmokeFailure(f"desired_entry did not target trigger bar: {desired_entry}")
        report["engine_desired_entry"] = desired_entry

        correlation_path = smoke_root / "abi" / "abi_entry_package_correlation.jsonl"
        correlations = read_jsonl(correlation_path)
        report["abi_correlation"] = summarize_correlations(correlations)

        abi_logs = compose(args, env, "logs", "--no-color", "abi", check=True).stdout
        runtime_logs = compose(args, env, "logs", "--no-color", "strategy-runtime", check=True).stdout
        report["logs"] = {
            "abi_contains_entry_package_operation": "entry_package" in abi_logs,
            "runtime_contains_strategy_cycle_failure": "strategy_cycle_dispatch_failed"
            in runtime_logs,
        }

        boundary = classify_boundary(report)
        report["boundary"] = boundary
        print(json.dumps(report, indent=2, sort_keys=True))
        if boundary != "ABI_SAFE_MODE_BLOCKED_ENTRY_PACKAGE_APPLICATION":
            raise SmokeFailure(f"unexpected smoke boundary: {boundary}")
        return 0
    finally:
        if not args.keep_running:
            compose(args, env, "down", check=False)


def create_smoke_layout(root: Path) -> None:
    for relative in (
        "market-data",
        "market-config",
        "strategy-runtime/specs",
        "strategy-runtime/journal",
        "abi",
        "bybit-fixture",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)


def write_runtime_deployment(root: Path) -> None:
    deployment = {
        "enabled": True,
        "ticker": TICKER,
        "base_timeframe": TIMEFRAME,
        "strategy_id": STRATEGY_ID,
        "raw_spec": RAW_SPEC,
    }
    path = root / "strategy-runtime" / "specs" / "deployment.json"
    path.write_text(json.dumps(deployment, indent=2, sort_keys=True), encoding="utf-8")


def write_mds_smoke_market_config(root: Path) -> None:
    (root / "market-config" / "markets.toml").write_text(
        """
schema_version = 1

[source]
venue = "bybit"
category = "linear"

[[instruments]]
ticker = "BTCUSDT.P"
exchange_symbol = "BTCUSDT"
enabled = true
canonical_timeframes = ["5m"]
history_policy = "full_available"
""".lstrip(),
        encoding="utf-8",
    )


def compose(
    args: argparse.Namespace,
    env: dict[str, str],
    *command: str,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    full = [
        "docker",
        "compose",
        "--project-name",
        args.project_name,
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.touch-anchor-smoke.yml",
        *command,
    ]
    return subprocess.run(
        full,
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def wait_for_stack(args: argparse.Namespace, env: dict[str, str], timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    expected = {"abi", "strategy-engine", "strategy-runtime", "market-data-service", "bybit-fixture"}
    while time.monotonic() < deadline:
        result = compose(args, env, "ps", "--format", "json", check=True)
        rows = parse_compose_ps(result.stdout)
        services = {row.get("Service"): row for row in rows}
        if expected <= services.keys():
            unhealthy = {
                name: services[name]
                for name in expected
                if services[name].get("Health") not in {"healthy", ""}
                or services[name].get("State") != "running"
            }
            if not unhealthy:
                return
        time.sleep(2)
    raise SmokeFailure("stack did not reach running/healthy state before timeout")


def wait_for_mds_ready(timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        response = get_json("http://127.0.0.1:8080/readiness")
        last = response.body
        if response.status == 200 and response.body.get("ready") is True:
            return
        time.sleep(1)
    raise SmokeFailure(f"MDS did not reach readiness before timeout: {last}")


def wait_for_fixture_trigger(path: Path, timeout_seconds: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        if path.exists():
            last = json.loads(path.read_text(encoding="utf-8"))
            if last.get("websocket_sent") and last.get("websocket_trigger_open_time_ms") is not None:
                return last
        time.sleep(1)
    raise SmokeFailure(f"Bybit fixture did not send websocket trigger before timeout: {last}")


def parse_compose_ps(output: str) -> list[dict[str, Any]]:
    text = output.strip()
    if not text:
        return []
    try:
        loaded = json.loads(text)
        return loaded if isinstance(loaded, list) else [loaded]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def get_json(url: str) -> HttpResult:
    return request_json("GET", url, None)


def post_json(url: str, body: dict[str, Any]) -> HttpResult:
    return request_json("POST", url, body)


def request_json(method: str, url: str, body: dict[str, Any] | None) -> HttpResult:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return HttpResult(response.status, json.loads(response.read().decode("utf-8")))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            body_payload = json.loads(payload)
        except json.JSONDecodeError:
            body_payload = {"raw": payload}
        return HttpResult(exc.code, body_payload)


def assert_abi_safe_mode(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, sort_keys=True)
    for expected in ("dry", "testnet"):
        if expected not in text.lower():
            raise SmokeFailure(f"ABI execution mode missing {expected!r}: {payload}")
    if "canExecuteLive" in payload and payload["canExecuteLive"] is not False:
        raise SmokeFailure(f"ABI unexpectedly allows live execution: {payload}")
    if "live_execution" in text.lower() and "unavailable" not in text.lower():
        raise SmokeFailure(f"ABI live execution boundary unclear: {payload}")


def wait_for_runtime_journal(
    path: Path,
    open_time_ms: int,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        records = read_jsonl(path)
        matching = [
            item
            for item in records
            if item.get("payload", {}).get("open_time_ms") == open_time_ms
        ]
        if any(item.get("event_type") == "committed_bar_orchestration_completed" for item in matching):
            return matching
        time.sleep(1)
    raise SmokeFailure("Runtime journal did not record completed processing before timeout")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def summarize_journal(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "event_type": record.get("event_type"),
            "severity": record.get("severity"),
            "strategy_instance_id": record.get("strategy_instance_id"),
            "payload": record.get("payload"),
            "diagnostics": record.get("diagnostics"),
        }
        for record in records
    ]


def summarize_correlations(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for record in records:
        summary.append(
            {
                "strategy_instance_id": record.get("strategy_instance_id"),
                "trade_cycle_id": record.get("trade_cycle_id"),
                "status": record.get("status"),
                "pending_action": record.get("pending_action"),
                "side": record.get("side"),
                "entry_price": record.get("entry_price"),
                "stop_price": record.get("stop_price"),
                "take_price": record.get("take_price"),
                "order_link_id": record.get("order_link_id"),
                "exchange_order_id": record.get("exchange_order_id"),
            }
        )
    return summary


def classify_boundary(report: dict[str, Any]) -> str:
    journal = report.get("runtime_journal", [])
    correlations = report.get("abi_correlation", [])
    failed = [item for item in journal if item.get("event_type") == "strategy_cycle_dispatch_failed"]
    if failed and correlations:
        diagnostics_text = json.dumps(failed[-1].get("diagnostics", {}), sort_keys=True)
        if "abi_entry_package" in diagnostics_text or "entry-package" in diagnostics_text:
            return "ABI_SAFE_MODE_BLOCKED_ENTRY_PACKAGE_APPLICATION"
    succeeded = [item for item in journal if item.get("event_type") == "strategy_cycle_dispatch_succeeded"]
    if succeeded:
        return "RUNTIME_ENTRY_PACKAGE_APPLIED"
    return "UNKNOWN"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"SMOKE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

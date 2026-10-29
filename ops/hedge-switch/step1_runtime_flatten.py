#!/usr/bin/env python3
"""Step 1: close positions, cancel entry orders and disable every strategy through
Runtime's own operator commands (strategy_runtime #42), so Runtime and ABI durable
state stay consistent. Nothing goes to Bybit directly.

Default is a dry run that only prints the plan. Run with --apply to execute.
Saves the list of strategies that were enabled to SNAPSHOT before any change
(never overwritten), for re-enabling after the switch.

Usage (Mac host): python3 step1_runtime_flatten.py [--apply]
"""
import json
import os
import sys
import urllib.error
import urllib.request

RUNTIME = os.environ.get("RUNTIME_URL", "http://127.0.0.1:8093")
SNAPSHOT = os.environ.get(
    "SNAPSHOT", "/Users/mcroma/BBB_data/abi/hedge_switch_enabled_before.json"
)


def call(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(RUNTIME + path, data=data, method=method)
    if data is not None:
        req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"null")


def main():
    apply = "--apply" in sys.argv
    status, catalog = call("GET", "/v1/strategy-instances")
    assert status == 200, (status, catalog)
    status, states = call("GET", "/v1/strategy-instance-states")
    assert status == 200, (status, states)

    enabled = {i["strategy_instance_id"]: i for i in catalog["strategy_instances"] if i["enabled"]}
    by_id = {s["strategy_instance_id"]: s for s in states["strategy_instances"]}

    recovering = [s for s in by_id.values() if s["recovery_pending"] is not None]
    if recovering:
        print("STOP: recovery pending, resolve first:", json.dumps(recovering, indent=1))
        sys.exit(2)

    plan = []
    ids = sorted(set(enabled) | {i for i, s in by_id.items() if s["trade_state"] != "flat"})
    for sid in ids:
        st = by_id.get(sid, {"trade_state": "flat", "side": None})
        if st["trade_state"] == "in_position":
            plan.append((sid, "close-position", st))
        elif st["trade_state"] == "entry_pending":
            plan.append((sid, "cancel-entry-orders", st))
        else:
            plan.append((sid, "disable", st))

    for sid, action, st in plan:
        inst = enabled.get(sid, {}).get("instrument", "?")
        print(f"{sid}  {inst:10}  {st['trade_state']:13} {st.get('side') or '':5}  -> {action}")
    if not apply:
        print("\nDry run. Re-run with --apply to execute.")
        return

    if not os.path.exists(SNAPSHOT):
        with open(SNAPSHOT, "w") as f:
            json.dump(sorted(enabled), f, indent=1)
        print("saved enabled list:", SNAPSHOT)

    failed = False
    for sid, action, _ in plan:
        if action == "disable":
            status, body = call("PUT", f"/v1/strategy-instances/{sid}/enabled", {"enabled": False})
        else:
            status, body = call("POST", f"/v1/strategy-instances/{sid}/{action}")
        print(sid, action, status, json.dumps(body))
        failed |= status != 200

    status, states = call("GET", "/v1/strategy-instance-states")
    left = [s for s in states["strategy_instances"] if s["trade_state"] != "flat" or s["recovery_pending"]]
    print("\nnot flat after step 1:", json.dumps(left, indent=1) if left else "none")
    sys.exit(1 if failed or left else 0)


if __name__ == "__main__":
    main()

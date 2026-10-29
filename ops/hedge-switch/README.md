# One-time switch of the demo account and ABI to hedge mode

Each step is run separately, on the owner's word, from `BBB_project/bbb_stack` on the Mac.

1. `python3 ops/hedge-switch/step1_runtime_flatten.py` (dry run), then `--apply`.
   Runtime closes positions, cancels entry orders, disables every strategy
   (its own operator commands). Saves the enabled list to
   `BBB_data/abi/hedge_switch_enabled_before.json`.
2. `docker exec -i bbb_stack-abi-1 node --input-type=module < ops/hedge-switch/step2_bybit_hedge.mjs` (dry run),
   then with `-e APPLY=1`: checks Bybit and ABI are flat, switches USDT linear to hedge, verifies positionIdx 1,2.
3. Set `ABI_BYBIT_LINEAR_POSITION_BINDING_MODE: "hedge"` for abi (docker-compose.demo.yml, separate PR),
   recreate abi only, check `/health` ready.
4. Re-enable the saved strategies (`PUT /v1/strategy-instances/{id}/enabled {"enabled": true}`).

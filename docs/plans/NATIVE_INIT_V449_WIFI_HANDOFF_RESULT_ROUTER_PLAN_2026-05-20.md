# Native Init V449 Wi-Fi Handoff Result Router Plan

Date: 2026-05-20

## Goal

V449 adds an evidence router for the V448/V447/V445 Wi-Fi handoff chain.  After
the operator runs the generated scripts, the repo should be able to route the
latest result without manual manifest inspection or secret handling.

## Scope

Allowed:

- read existing V448 packet, V447 private preflight, V447 live, and nested V445
  manifests;
- ignore synthetic/plan/env-missing evidence by default;
- emit the next safe command when available;
- write private router evidence under ignored `tmp/`.

Not allowed:

- read Wi-Fi secret env values;
- execute generated handoff scripts;
- boot/flash Android, enable Wi-Fi, scan, connect, or mutate the device;
- expose any server listener.

## Implementation

- Router: `scripts/revalidation/wifi_handoff_result_router_v449.py`
  - `plan`: records the router plan without reading live evidence;
  - `run`: classifies the latest relevant handoff evidence;
  - recommends the V448 host preflight script, V448 live script, triage, or
    post-live stability planning depending on evidence state.

## Validation Plan

```text
python3 -m py_compile scripts/revalidation/wifi_handoff_result_router_v449.py

python3 scripts/revalidation/wifi_handoff_result_router_v449.py \
  --out-dir tmp/wifi/v449-wifi-handoff-result-router-plan-<ts> \
  plan

python3 scripts/revalidation/wifi_handoff_result_router_v449.py \
  --out-dir tmp/wifi/v449-wifi-handoff-result-router-run-<ts> \
  run

git diff --check
```

## Expected Decisions

- `v449-wifi-handoff-result-router-plan-ready`
- `v449-wifi-needs-handoff-packet`
- `v449-wifi-handoff-packet-blocked`
- `v449-wifi-handoff-packet-ready-run-preflight`
- `v449-wifi-private-preflight-blocked`
- `v449-wifi-private-preflight-ready-run-live`
- `v449-wifi-live-failed-needs-triage`
- `v449-wifi-live-pass-next-stability`

## Pass Criteria

V449 passes when it can identify a safe next action from current evidence.  In
the current state, pass means:

- V448 packet evidence is present and passed;
- no private V447 host preflight result exists yet;
- router recommends the generated V448 host preflight script;
- no device command or Wi-Fi bring-up occurs.

## Next Gate

Run the router after each V448/V447 step.  Current expected next gate is the
generated host preflight script.  If private preflight passes, rerun V449; it
should then recommend the generated live script.

Server exposure remains blocked.

# v343 Break V331/V336 Handoff Cycle Report

- date: `2026-05-19`
- scope: host-side V317 gate dependency correction
- device command: none
- device mutation: none
- result: `PRE-COMMIT PASS / POST-COMMIT REGEN REQUIRED`

## Summary

v342 post-commit evidence regeneration showed a circular dependency between the
V317 pre-live gate and the operator handoff artifacts. V336 was checking V331 and
V333, while V331 already checks V336 and V333 checks V331. That made the final
handoff impossible to regenerate from a clean head.

v343 corrects the dependency direction by keeping V336 limited to true pre-live
inputs and leaving V331/V340 as handoff artifacts.

## Code Change

- `scripts/revalidation/wifi_v317_prelive_gate_audit.py`
  - removed `v331-live-readiness-packet` from V336 gate inputs
  - removed `v333-post-v317-router` from V336 gate inputs

## Pre-commit Validation

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_v317_prelive_gate_audit.py \
  scripts/revalidation/wifi_private_property_namespace_proof.py \
  scripts/revalidation/wifi_v317_live_readiness_packet.py \
  scripts/revalidation/wifi_v317_live_surface_linter.py \
  scripts/revalidation/wifi_v317_handoff_packet.py
python3 scripts/revalidation/wifi_v317_prelive_gate_audit.py \
  --out-dir tmp/wifi/v336-v317-prelive-gate-audit audit || true
```

Observed pre-commit result:

```text
V331/V333 are no longer V336 blockers.
V326/V327/V328/V335 still block because current evidence was generated from a dirty or stale affected head.
```

## Post-commit Validation Plan

After this report is committed, regenerate V326/V327/V328/V335/V336/V331/V339/V340
on the clean current head, then run the approved preflight. Expected final state:

```text
V336: v317-prelive-gate-awaiting-approval
V331: v317-live-readiness-packet-ready
V339: v317-live-surface-lint-pass
V340: v317-handoff-awaiting-approval
V342 approved preflight: private-property-namespace-proof-preflight-ready
```

## Safety

- No live V317 proof was executed.
- No device command was executed.
- No device mutation was performed.
- The exact V317 approval phrase remains the only live execution gate after
  clean-head regeneration succeeds.

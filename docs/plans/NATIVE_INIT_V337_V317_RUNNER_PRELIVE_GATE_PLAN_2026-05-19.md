# v337 Plan: V317 Runner Pre-live Gate Requirement

- date: `2026-05-19`
- scope: host-side V317 runner safety gate hardening
- boot image change: none planned
- device mutation: none planned
- status: implemented / validated

## Summary

v336 proved the pre-live gate chain is ready and blocked only by the exact V317
approval phrase. v337 makes that audit a hard requirement inside the V317 runner
before any exact-approval live path can execute.

The change is deliberately fail-closed:

- partial approval still returns `private-property-namespace-proof-approval-required`;
- exact approval on a dirty or stale tree returns `private-property-namespace-proof-blocked`;
- live device commands remain unexecuted unless approval and the V336 gate both
  pass.

## Implementation

- Add `--prelive-gate-manifest`, defaulting to
  `tmp/wifi/v336-v317-prelive-gate-audit/manifest.json`.
- Add `v336-prelive-gate` to the V317 runner checks.
- Require the V336 decision `v317-prelive-gate-awaiting-approval`,
  `pass=true`, no device command/mutation, the exact approval phrase, and a
  clean current git head match.
- Keep no-approval behavior unchanged so regression gates remain stable.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_private_property_namespace_proof.py \
  scripts/revalidation/wifi_approval_gate_regression.py \
  scripts/revalidation/wifi_v317_prelive_gate_audit.py
python3 scripts/revalidation/wifi_private_property_namespace_proof.py \
  --out-dir tmp/wifi/v337-v317-runner-no-approval \
  run || true
python3 scripts/revalidation/wifi_private_property_namespace_proof.py \
  --out-dir tmp/wifi/v337-v317-runner-full-approval-dirty \
  --approval-phrase 'approve v317 minimal private property namespace proof only; no daemon start and no Wi-Fi bring-up' \
  --allow-device-mutation \
  --assume-yes \
  run || true
python3 scripts/revalidation/wifi_approval_gate_regression.py \
  --out-dir tmp/wifi/v337-approval-gate-regression-after-runner-gate \
  run
git diff --check
```

## Acceptance

- No-approval V317 run still produces `private-property-namespace-proof-approval-required`.
- Dirty-tree exact approval is blocked by `v336-prelive-gate`.
- Approval gate regression still passes.
- `device_commands_executed=false` and `device_mutations=false` for all v337 checks.

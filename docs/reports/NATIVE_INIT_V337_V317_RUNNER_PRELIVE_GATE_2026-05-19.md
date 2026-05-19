# v337 V317 Runner Pre-live Gate Report

- date: `2026-05-19`
- scope: host-side V317 runner safety gate hardening
- device command: none
- device mutation: none
- result: `PASS`

## Summary

v337 makes the V336 pre-live gate audit a hard live-path prerequisite in
`scripts/revalidation/wifi_private_property_namespace_proof.py`. The runner now
requires a clean current git head and a matching V336 audit before exact approval
can execute live commands.

## Evidence

- runner: `scripts/revalidation/wifi_private_property_namespace_proof.py`
- V336 gate: `tmp/wifi/v336-v317-prelive-gate-audit/manifest.json`
- no-approval evidence: `tmp/wifi/v337-v317-runner-no-approval/`
- dirty exact-approval evidence: `tmp/wifi/v337-v317-runner-full-approval-dirty/`
- regression evidence: `tmp/wifi/v337-approval-gate-regression-after-runner-gate/`

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

Observed results:

```text
no approval: private-property-namespace-proof-approval-required
full approval on dirty tree: private-property-namespace-proof-blocked, blocker=v336-prelive-gate
approval regression: wifi-approval-gate-regression-pass
```

## Interpretation

- V317 live proof remains unexecuted.
- Exact approval is no longer sufficient by itself; the V336 pre-live gate must
  also be current and clean.
- No Wi-Fi daemon, scan, connect, link-up, DHCP, routing, or credential path was
  exercised.

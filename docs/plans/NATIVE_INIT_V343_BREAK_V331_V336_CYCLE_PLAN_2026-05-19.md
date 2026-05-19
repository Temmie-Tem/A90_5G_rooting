# v343 Plan: Break V331/V336 Handoff Cycle

- date: `2026-05-19`
- scope: host-side V317 gate dependency correction
- boot image change: none planned
- device mutation: none planned
- status: implemented / pending post-commit regeneration

## Summary

v342 exposed a circular dependency in the host-only V317 approval chain:

```text
V331 readiness packet -> requires V336 pre-live gate
V333 post-V317 router -> requires V331 readiness packet
V336 pre-live gate -> required V331/V333 evidence
```

That direction is wrong. V336 is the pre-live gate that should decide whether the
operator may request V317 approval. V331 and V340 are handoff artifacts produced
from that gate; V333 is a post-V317 router and cannot be a V336 prerequisite.

v343 fixes the dependency direction by removing V331 and V333 from the V336 gate
list. V340 remains the aggregation point for V331, V336, and V339.

## Implementation

- Update `scripts/revalidation/wifi_v317_prelive_gate_audit.py`.
- Remove `v331-live-readiness-packet` from the V336 gate list.
- Remove `v333-post-v317-router` from the V336 gate list.
- Keep V336 focused on host-only/read-only prerequisites that do not depend on
  the handoff packet or the post-live router.
- Do not change the V317 runner live boundary.
- Do not execute V317 live proof.

## Dependency Direction

Expected direction after v343:

```text
V325/V326/V327/V328/V329/V332/V334/V335 -> V336
V336 -> V331
V331 + V336 + V339 -> V340
V317 live proof -> V333 post-live routing
```

This keeps pre-live readiness, operator handoff, static live-surface linting, and
post-live routing separate.

## Validation

Pre-commit validation:

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

Expected pre-commit result:

- V331/V333 no longer appear as V336 blockers.
- Dirty/stale affected gates may still block until clean-head evidence is
  regenerated after commit.

Post-commit regeneration:

```bash
python3 scripts/revalidation/wifi_private_property_namespace_proof.py --out-dir tmp/wifi/v317-private-property-namespace-proof-current-plan plan
python3 scripts/revalidation/wifi_private_property_chain_audit.py --out-dir tmp/wifi/v326-private-property-chain-audit audit
python3 scripts/revalidation/wifi_private_property_approval_refresh.py --out-dir tmp/wifi/v327-private-property-approval-refresh run
python3 scripts/revalidation/wifi_private_property_namespace_proof.py --out-dir tmp/wifi/v328-v317-runner-plan plan
python3 scripts/revalidation/wifi_private_property_namespace_proof.py --out-dir tmp/wifi/v328-v317-runner-refuse run || true
python3 scripts/revalidation/wifi_approval_gate_regression.py --out-dir tmp/wifi/v335-approval-gate-regression run
python3 scripts/revalidation/wifi_v317_prelive_gate_audit.py --out-dir tmp/wifi/v336-v317-prelive-gate-audit audit
python3 scripts/revalidation/wifi_v317_live_readiness_packet.py --out-dir tmp/wifi/v331-v317-live-readiness-packet packet
python3 scripts/revalidation/wifi_v317_live_surface_linter.py --out-dir tmp/wifi/v339-v317-live-surface-linter lint
python3 scripts/revalidation/wifi_v317_handoff_packet.py --out-dir tmp/wifi/v340-v317-final-handoff-packet packet
python3 scripts/revalidation/wifi_post_v317_router.py --out-dir tmp/wifi/v333-post-v317-router route
```

Approved preflight check remains host-only and must not execute device commands:

```bash
python3 scripts/revalidation/wifi_private_property_namespace_proof.py \
  --out-dir tmp/wifi/v342-v317-approved-preflight \
  --prelive-gate-manifest tmp/wifi/v336-v317-prelive-gate-audit/manifest.json \
  --approval-phrase 'approve v317 minimal private property namespace proof only; no daemon start and no Wi-Fi bring-up' \
  --allow-device-mutation \
  --assume-yes \
  preflight
```

## Acceptance

- V336 no longer depends on V331 or V333.
- V336 reaches `v317-prelive-gate-awaiting-approval` after clean-head evidence is
  regenerated.
- V331 readiness packet reaches `v317-live-readiness-packet-ready` after V336.
- V340 handoff reaches `v317-handoff-awaiting-approval` with remaining blocker
  `exact-v317-approval-phrase`.
- Approved preflight reaches `private-property-namespace-proof-preflight-ready`
  with `commands=[]`, `device_commands_executed=false`, and
  `device_mutations=false`.
- V317 live proof remains unexecuted.

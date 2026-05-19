# v336 Plan: V317 Pre-live Gate Audit

- date: `2026-05-19`
- scope: host-only V317 pre-live gate audit
- boot image change: none planned
- device mutation: none planned
- status: implemented / validated

## Summary

v335 proved partial approval combinations fail closed. v336 consolidates the
V325-V335 Wi-Fi gate evidence and decides whether the V317 private-property live
proof is blocked by anything other than the exact operator approval phrase.

The audit is host-only. It does not run V317, does not open a bridge command,
and does not mutate the device.

## Implementation

- Add `scripts/revalidation/wifi_v317_prelive_gate_audit.py`.
- Load V325-V335 manifests.
- Check each expected decision/pass value and no device mutation.
- Accept older evidence only when `git diff <evidence_head>..HEAD` does not
  touch that gate's critical implementation paths.
- Emit a single go/no-go style manifest and summary.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_prelive_gate_audit.py
python3 scripts/revalidation/wifi_v317_prelive_gate_audit.py \
  --out-dir tmp/wifi/v336-v317-prelive-gate-audit \
  audit
git diff --check
```

Expected result:

```text
decision: v317-prelive-gate-awaiting-approval
pass: True
remaining_blockers: [exact-v317-approval-phrase]
```

## Acceptance

- All V325-V335 host-only/read-only gates pass or are stale-unaffected.
- `device_commands_executed=false`.
- `device_mutations=false`.
- The only remaining blocker is the exact V317 approval phrase.

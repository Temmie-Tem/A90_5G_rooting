# v340 Plan: V317 Final Handoff Packet

- date: `2026-05-19`
- scope: host-only final V317 live handoff packet
- boot image change: none planned
- device mutation: none planned
- status: implemented / validated

## Summary

v340 consolidates the final pre-live evidence into one operator-facing packet.
It reads V331 readiness packet, V336 pre-live gate audit, and V339 live-surface
linter evidence, then emits the exact live command and cleanup command only as
text. It does not execute either command.

## Implementation

- Add `scripts/revalidation/wifi_v317_handoff_packet.py`.
- Require:
  - V331 `v317-live-readiness-packet-ready`.
  - V336 `v317-prelive-gate-awaiting-approval`.
  - V339 `v317-live-surface-lint-pass`.
  - exact V317 approval phrase match.
  - generated command includes `--prelive-gate-manifest`.
  - no device command/mutation/live approval recorded in prerequisites.
- Accept stale evidence only when `git diff <evidence_head>..HEAD` does not touch
  that gate's critical implementation paths.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_handoff_packet.py
python3 scripts/revalidation/wifi_v317_handoff_packet.py \
  --out-dir tmp/wifi/v340-v317-final-handoff-packet \
  packet
git diff --check
```

Expected result:

```text
decision: v317-handoff-awaiting-approval
pass: True
remaining_blockers: [exact-v317-approval-phrase]
```

## Acceptance

- Handoff packet is PASS.
- It emits the exact live command and cleanup command as text only.
- It records `device_commands_executed=false` and `device_mutations=false`.
- The only remaining blocker is `exact-v317-approval-phrase`.

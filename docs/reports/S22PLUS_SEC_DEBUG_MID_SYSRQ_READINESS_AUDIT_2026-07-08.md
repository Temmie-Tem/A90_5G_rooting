# S22+ Sec Debug MID Sysrq Readiness Audit (2026-07-08)

## Verdict

HOST-ONLY READINESS AUDIT PASS.

Codex added a no-device readiness auditor for the Samsung sec_debug MID
sysrq-panic gate:

```text
workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_readiness_audit.py
```

The audit performs no flash, reboot, partition write, procfs/sysfs write,
sysrq trigger, Odin transfer, Magisk module install, native-init candidate
action, ADB device access, or intentional crash.

## What It Checks

Current inactive-policy mode:

```text
draft policy markers complete
AGENTS.md active policy markers incomplete
gate --offline-check passes
gate --print-plan passes and includes live/collect commands
gate default execution fails closed at the expected AGENTS marker gate
```

Active-policy marker dry-check mode:

```text
AGENTS.md + inert draft, built in a temporary file, has complete marker coverage
same --offline-check and --print-plan host-only checks pass
default dry-run is intentionally skipped in this temp-file mode because the gate
itself reads real AGENTS.md and would otherwise be a device-facing dry-run after
policy promotion
```

Required markers are imported from
`s22plus_sec_debug_mid_sysrq_gate.required_policy_markers()` so the auditor
tracks the helper's gate contract instead of duplicating stale strings.

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_readiness_audit.py \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_readiness_audit.py \
  --out workspace/private/runs/s22plus_sec_debug_mid_sysrq_readiness_latest.json
```

Inactive-policy result:

```text
result: pass
device_action: false
writes_performed: false
reboots_performed: false
flashes_performed: false
sysrq_triggered: false
draft.complete: true
draft.missing: []
agents.complete: false
offline_check.rc: 0
print_plan.rc: 0
default_dryrun.rc: 1
default_dryrun gate: agents_exception missing sec_debug MID sysrq markers
```

Temporary active-marker validation:

```bash
tmp=$(mktemp /tmp/s22_secdebug_agents_active.XXXXXX.md)
cp AGENTS.md "$tmp"
sed -n '/^```text$/,/^```$/p' \
  docs/operations/S22PLUS_SEC_DEBUG_MID_SYSRQ_PANIC_AGENTS_EXCEPTION_DRAFT_2026-07-08.md |
  sed '1d;$d' >> "$tmp"
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_readiness_audit.py \
  --agents "$tmp" \
  --expect-agents-active \
  --no-default-dryrun-check \
  --out workspace/private/runs/s22plus_sec_debug_mid_sysrq_readiness_active_tmp_latest.json
rm -f "$tmp"
```

Temporary active-marker result:

```text
result: pass
agents.complete: true
agents.missing: []
draft.complete: true
offline_check.rc: 0
print_plan.rc: 0
device_action: false
```

## Next Gate

The live sec_debug MID positive control remains inactive. The next step requires
explicit operator approval to promote the inert exception into `AGENTS.md`, then:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_readiness_audit.py \
  --expect-agents-active \
  --no-default-dryrun-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --live-panic \
  --ack S22PLUS-SECDEBUG-MID-SYSRQ-PANIC-LIVE-GATE \
  --confirm-debug-level-mid DEBUG_LEVEL_MID_SET_BY_OPERATOR
```

Manual recovery may be required after `--live-panic`, followed by:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --collect-after-recovery
```

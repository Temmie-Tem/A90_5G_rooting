# S22+ Sec Debug MID Sysrq Policy Activation (2026-07-08)

## Verdict

ACTIVE POLICY / DRY-RUN PASS. LIVE PANIC NOT YET TRIGGERED IN THIS UNIT.

After explicit operator approval, Codex promoted the inert Samsung sec_debug MID
sysrq-panic exception into `AGENTS.md`. The active exception is limited to one
bounded zero-flash Android-side positive control through:

```text
workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py
```

Live ack token:

```text
S22PLUS-SECDEBUG-MID-SYSRQ-PANIC-LIVE-GATE
```

Confirmation token:

```text
DEBUG_LEVEL_MID_SET_BY_OPERATOR
```

The exception authorizes no Odin flash, no partition write, no boot image write,
no DTBO write, no vendor_boot write, no recovery/vbmeta/BL/CP/CSC/super/userdata/
EFS/sec_efs/RPMB/keymaster/modem/bootloader write, no raw host `dd`, no fastboot,
and no Magisk module install.

## Validation

Active readiness audit:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_readiness_audit.py \
  --expect-agents-active \
  --no-default-dryrun-check \
  --out workspace/private/runs/s22plus_sec_debug_mid_sysrq_readiness_active_policy.json
```

Result:

```text
result: pass
agents.complete: true
agents.missing: []
draft.complete: true
offline_check.rc: 0
print_plan.rc: 0
device_action: false
flashes_performed: false
reboots_performed: false
writes_performed: false
sysrq_triggered: false
```

Active dry-run:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py
```

Private run, not committed:

```text
workspace/private/runs/s22plus_sec_debug_mid_sysrq_20260707T211537Z
```

Dry-run result:

```text
dry-run ok
android_stability_result=ok samples=4
current_boot_hash_rc=0
current boot hash matched known-booting Magisk baseline
```

Live precheck sec_debug state:

```text
debug_level decimal   18765
debug_level hex       0x494d
debug_level ascii_le  MI
likely_low_code       false
enable                1
enable_user           0
force_upload          5
/proc/sys/kernel/sysrq 0
```

This satisfies the helper's hardened precondition for a later attended
`--live-panic` run. No live panic was executed by this report.

## Next Gate

Run exactly one attended live trigger:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --live-panic \
  --ack S22PLUS-SECDEBUG-MID-SYSRQ-PANIC-LIVE-GATE \
  --confirm-debug-level-mid DEBUG_LEVEL_MID_SET_BY_OPERATOR
```

Expected operator role after the trigger:

```text
observe screen state
if the device enters Upload Mode / Download / stuck reboot state, perform manual
recovery as needed
reconnect ADB or confirm Download/Odin state so retained evidence can be collected
```

After recovery:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --collect-after-recovery
```

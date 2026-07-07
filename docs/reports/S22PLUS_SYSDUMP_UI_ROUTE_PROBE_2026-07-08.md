# S22+ SysDump UI Route Probe (2026-07-08)

## Verdict

LIVE ROUTE PROBE PASS, WITH NEGATIVE RESULT FOR ADB-OPEN.

The S22+ stayed in normal Android after the probe (`sys.boot_completed=1`).
No bootloop, flash, reboot, partition write, procfs/sysfs write, sysrq trigger,
or Odin transfer was performed.

The Samsung ServiceMode manifest exposes SysDump and CPDebugLevel activities,
but ADB/root shell cannot directly open them on this build. The physical dialer
`*#9900#` remains the next operator path for changing DEBUG LEVEL.

## Helper

`workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py`

New route-probe mode:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --probe-sysdump-ui-route
```

This mode is intentionally not the panic gate. It performs Android/root
prechecks, verifies the known Magisk boot hash, probes ServiceMode UI routes,
and records whether the UI became visible.

## Live Result

Private run directory, not committed:

`workspace/private/runs/s22plus_sec_debug_mid_sysrq_20260707T204001Z`

Public metadata:

```text
mode                              probe_sysdump_ui_route
visible_after_any_attempt          false
explicit_activity_startable        false
secret_code_broadcast_startable    false
writes_performed                   false
reboots_performed                  false
flashes_performed                  false
sysrq_triggered                    false
post-probe Android boot_completed  1
post-probe debug_level             20300 / 0x4f4c / LO
```

Attempt matrix:

```text
shell am start SysDump            rc=1    Error type 3, not visible
root  am start SysDump            rc=1    Error type 3, not visible
root  am start CPDebugLevel        rc=1    Error type 3, not visible
shell secret-code 9900 broadcast   rc=255  Permission Denial, not visible
root  secret-code 9900 broadcast   rc=0    Broadcast completed, not visible
```

Manifest/tool evidence from the same live APK:

```text
package        com.sec.android.app.servicemodeapp
apk path       /system/priv-app/serviceModeApp_FB/serviceModeApp_FB.apk
SysDump        activity .SysDump, exported=true
CPDebugLevel   activity .CPDebugLevel, exported=true
both require   com.sec.android.app.servicemodeapp.permission.KEYSTRING
receiver       .ServiceModeAppBroadcastReceiver
receiver requires KEYSTRING and handles com.samsung.android.action.SECRET_CODE
9900 authority present
```

## Interpretation

The prior read-only route inventory was correct that the package contains the
SysDump and CPDebugLevel surfaces. The missing piece is launch authority:
`am start` from shell/root is not a working way to reach the UI, and a root
secret-code broadcast completes without making SysDump visible.

Therefore do not list ADB direct-start as an operator path. The practical next
step is physical dialer entry of `*#9900#`, then set DEBUG LEVEL to MID if the
menu exposes it, then rerun `--read-only-probe`. The intentional sysrq-panic
gate stays parked while `debug_level` remains LOW.

A follow-up `--read-only-probe` after the route attempts still decoded
`debug_level` as `20300 / 0x4f4c / LO`, confirming the probe did not change
the sec_debug state.

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --print-plan

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --probe-sysdump-ui-route

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --read-only-probe
```

Results:

- `py_compile`: pass.
- `--offline-check`: pass, `rc=0`, no device action.
- `--print-plan`: pass and now lists `--probe-sysdump-ui-route`.
- `--probe-sysdump-ui-route`: pass, `rc=0`, negative UI-open result recorded.
- post-probe `--read-only-probe`: pass, `debug_level` still LOW.

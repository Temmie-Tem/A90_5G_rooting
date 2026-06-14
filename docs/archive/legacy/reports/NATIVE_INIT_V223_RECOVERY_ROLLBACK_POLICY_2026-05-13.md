# v223 Report: Recovery / Rollback Policy Hardening

## Summary

v223 implements a host-side read-only recovery policy generator and runs it
against existing v214/v217/v220/v222 evidence.

- script: `scripts/revalidation/wifi_recovery_rollback_policy.py`
- plan: `docs/plans/NATIVE_INIT_V223_RECOVERY_ROLLBACK_POLICY_PLAN_2026-05-13.md`
- output: `tmp/wifi/v223-recovery-rollback-policy`
- result: PASS
- decision: `reboot-recovery-accepted`
- reason: `reboot is the only accepted recovery primitive for later opt-in mutation planning`

This does not approve Wi-Fi daemon execution, scan, connect, rfkill writes, or
generic ICNSS rebind. It only records that future opt-in mutation plans may use
native reboot as the last-resort recovery path if all preflight/stop/post-reboot
conditions are met.

## What Was Implemented

`wifi_recovery_rollback_policy.py` now:

- loads existing host evidence only;
- reads v214 reprobe manifest and report;
- reads v217 native ICNSS debug/recovery inventory;
- reads v220 lifecycle-aware gate result;
- reads v222 vendor-root export result;
- emits `manifest.json`, `recovery-policy.json`, and `summary.md`;
- classifies recovery primitives:
  - `native_reboot`: accepted;
  - generic ICNSS `unbind`/`bind`: denied;
  - `driver_override`: denied;
  - unreviewed sysfs/debugfs/configfs writes: denied;
- lists stop conditions, preflight requirements, and post-reboot verification.

## Validation

Static validation:

```bash
python3 -m py_compile scripts/revalidation/wifi_recovery_rollback_policy.py

python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import wifi_recovery_rollback_policy
wifi_recovery_rollback_policy.validate_no_active_commands()
print('v223 command guard PASS')
PY
```

Result:

```text
v223 command guard PASS
```

Policy run:

```bash
python3 scripts/revalidation/wifi_recovery_rollback_policy.py \
  --v214-manifest tmp/wifi/v214-icnss-reprobe/manifest.json \
  --v217-native-manifest tmp/wifi/v217-icnss-debug-recovery-inventory-native/manifest.json \
  --v220-manifest tmp/wifi/v220-bringup-gate-v2/manifest.json \
  --v222-manifest tmp/wifi/v222-vendor-root-evidence-export/manifest.json \
  --out-dir tmp/wifi/v223-recovery-rollback-policy
```

Result:

```text
PASS out_dir=/home/temmie/dev/A90_5G_rooting/tmp/wifi/v223-recovery-rollback-policy decision=reboot-recovery-accepted reason=reboot is the only accepted recovery primitive for later opt-in mutation planning
```

Manifest assertion:

```text
reboot-recovery-accepted True reboot is the only accepted recovery primitive for later opt-in mutation planning
post_reboot True
icnss_gate blocked
```

Output file modes:

```text
600 tmp/wifi/v223-recovery-rollback-policy/manifest.json
600 tmp/wifi/v223-recovery-rollback-policy/recovery-policy.json
600 tmp/wifi/v223-recovery-rollback-policy/summary.md
```

## Evidence Summary

| item | value |
| --- | --- |
| v214 decision | `icnss-rebind-failed` |
| v214 post reboot complete | `True` |
| v217 decision | `state-only-inventory` |
| v217 unsafe write count | `10` |
| v220 decision | `no-go` |
| v220 icnss gate | `blocked` |
| v222 decision | `export-source-required` |
| v222 source root | `not-provided` |

## Recovery Policy

| primitive | status | reason |
| --- | --- | --- |
| native reboot | accepted | v214 post-reboot evidence restored ICNSS bound state |
| generic ICNSS unbind/bind | denied | v214 bind/rebind failed and left driver state broken until reboot |
| driver_override | denied | v217 classifies driver_override as dangerous recovery surface |
| unreviewed sysfs/debugfs/configfs write | denied | v217 found unsafe writable/recovery controls |

## Artifact Hashes

```text
ae0375919f183a3d48b3f4d4a6a4343097c23d3c25fd9c8abe740d6135825413  scripts/revalidation/wifi_recovery_rollback_policy.py
5fccc433e33c453c1acf8dac73c6e73f8765f6808510bd5e6999a32db6f20994  docs/plans/NATIVE_INIT_V223_RECOVERY_ROLLBACK_POLICY_PLAN_2026-05-13.md
35c8b84a3c34d93cd4664efd119c33d55baf98d019b6da7249357e56a731c055  tmp/wifi/v223-recovery-rollback-policy/manifest.json
bb1f7372e712d17e2686eafebdfe5bf21a9e4b44cc0121b469faa184c76c8655  tmp/wifi/v223-recovery-rollback-policy/recovery-policy.json
d5c9002ecc9399a64550323cfbf6ddb895e74d526ea2401bbf5f5af6d807d4f2  tmp/wifi/v223-recovery-rollback-policy/summary.md
```

## Interpretation

v223 closes the recovery policy ambiguity by accepting only reboot-backed
recovery for later explicitly approved mutation plans.

Still blocked:

- active Wi-Fi scan/connect;
- `cnss-daemon`/`cnss_diag` execution;
- Wi-Fi HAL, `wificond`, supplicant, hostapd execution;
- generic ICNSS bind/unbind;
- unreviewed sysfs/debugfs/configfs writes.

## Next

v224 can plan Android-env shim materialization as a reversible dry-run, but it
must depend on this v223 policy and must not execute daemons or start active
Wi-Fi networking.

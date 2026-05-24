# Native Init V815 Subsystem/Sysmon Snapshot Plan

## Goal

Collect a read-only stock-v724 idle snapshot of subsystem, sysmon,
service-locator, esoc metadata, ICNSS, QRTR, and focused dmesg surfaces before
any new Wi-Fi trigger.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py`
- Input:
  - V814 source classifier manifest.
- Runtime:
  - Current native build `A90 Linux init 0.9.68 (v724)`.
  - Serial bridge only; NCM is not required.

## Hard Gates

- Read-only live: no sysfs/debugfs/control writes.
- No custom kernel flash, boot image write, partition write, reboot, or
  bootloader handoff.
- No daemon start, service-manager start, Wi-Fi HAL start, scan/connect/link-up,
  or credential use.
- No DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate` write, `esoc0` open, bind/unbind,
  driver override, or module load/unload.

## Success Criteria

- V815 compiles and plan-only manifest passes.
- V814 is present and passed.
- Runtime health matches stock v724 and `selftest` passes.
- Read-only captures all complete without bridge busy/failure.
- Snapshot records `/sys/bus/msm_subsys/devices/*`, read-only esoc metadata,
  ICNSS/platform state, QRTR/netlink state, process focus, and dmesg focus.
- Classifier separates runtime dmesg/proc markers from static devicetree/sysfs
  strings to avoid false WLFW/service-publication positives.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py

python3 scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py \
  --out-dir tmp/wifi/v815-subsystem-sysmon-snapshot-plan-check \
  plan

python3 scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py \
  --allow-live-readonly \
  --assume-yes \
  run

git diff --check
```

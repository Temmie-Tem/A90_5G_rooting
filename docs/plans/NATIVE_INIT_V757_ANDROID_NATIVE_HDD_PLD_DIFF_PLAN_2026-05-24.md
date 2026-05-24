# Native Init V757 Android/Native HDD/PLD Differential Plan

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_android_native_hdd_pld_diff_v757.py`
- scope: host-only Android/native dmesg differential; no device command

## Goal

V756 showed that live ftrace, dynamic-debug, and kprobe observability are not
available for the current kernel state. V757 compares existing Android success
logs and native failure logs to decide whether dmesg alone can identify the
missing HDD/PLD/register-driver boundary, or whether V758 must first classify
rollback-safe boot-image/kernel-log instrumentation feasibility.

## Basis Evidence

- `docs/reports/NATIVE_INIT_V753_HDD_PLD_PREREQ_CLASSIFIER_2026-05-24.md`
- `docs/reports/NATIVE_INIT_V756_NONFTRACE_HDD_PLD_OBSERVABILITY_2026-05-24.md`
- Android dmesg evidence from V612, V622, and V649
- Native lower-window `boot_wlan` evidence from V752 and V753

## Work Items

1. Validate V753 and V756 as input decisions.
2. Parse existing Android dmesg for service-notifier, CNSS daemon, WLAN-PD,
   ICNSS-QMI, BDF, FW-ready, HDD, and `wlan0` markers.
3. Parse native V752/V753/V756 evidence for HDD entry, qcwlanstate creation,
   success-marker absence, and modules-not-initialized markers.
4. Determine whether Android dmesg contains pre-QMI HDD/PLD/register-driver
   boundary markers.
5. Select V758 route:
   - existing dmesg route if pre-QMI boundary markers are sufficient,
   - rollback-safe boot-image/kernel-log instrumentation feasibility otherwise.

## Forbidden

- no device command
- no tracefs/debugfs mount
- no ftrace, dynamic-debug, or kprobe write
- no `boot_wlan`, `qcwlanstate`, bind/unbind, module, or subsystem write
- no service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or
  external ping
- no boot image or partition write

## Success Criteria

- Produce `manifest.json`, `summary.md`, and bounded host extracts.
- Prove Android reference still contains QMI/BDF/FW-ready/`wlan0`.
- Prove native reference still contains HDD entry with success-marker absence.
- Prove whether existing dmesg can or cannot locate the PLD/HDD/register-driver
  boundary.
- Select a V758 route without live device action.

## Source References

- QCACLD `__hdd_module_init`:
  <https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_main.c#9341>
- QCACLD `boot_wlan` callback:
  <https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_main.c#9406>
- QCACLD driver ops:
  <https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_driver_ops.c>

# V1021 V1020 Android Reset Handshake Classifier Plan

- date: `2026-05-26`
- type: host-only classifier
- selected after: V1020 scoped `/dev/subsys_esoc0` live gate

## Objective

Classify the V1020 stall before another native live retry.

V1020 reached the fd-positive upper Wi-Fi userspace surface and opened
`/dev/subsys_esoc0`, but the child blocked in `sdx50m_toggle_soft_reset`.
V1021 compares that result with existing Android-good evidence and prior
PeripheralManager/eSoC classifiers.

## Inputs

- `tmp/wifi/v1020-after-fd-subsys-window-live/manifest.json`
- `tmp/wifi/v1020-after-fd-subsys-window-live/native/mdm-helper-cnss-before-esoc.txt`
- `tmp/wifi/v1000-android-esoc-gpio-recapture-handoff-live/v913-android-esoc-gpio-timeline-run/android/commands/dmesg-full.txt`
- `tmp/wifi/v1000-android-esoc-gpio-recapture-handoff-live/v913-android-esoc-gpio-timeline-run/android/commands/process-fd.txt`
- `tmp/wifi/v968-android-dmesg-esoc-gpio-timing/manifest.json`
- `docs/reports/NATIVE_INIT_V867_PM_INIT_CONTRACT_START_ONLY_2026-05-25.md`
- `docs/reports/NATIVE_INIT_V868_PM_ESOC_CONTRACT_CLASSIFIER_2026-05-25.md`
- `docs/reports/NATIVE_INIT_V944_V943_QUEUE_TIMING_CLASSIFIER_2026-05-26.md`
- `docs/overview/MDM3_ESOC_SDX50M_BRINGUP_RESEARCH_2026-05-25.md`
- `docs/overview/ESOC_PERIPHERAL_MANAGER_BRINGUP_RESEARCH_2026-05-25.md`

## Questions

- Did V1020 reach the real SDX50M soft-reset path?
- Does Android-good evidence include `per_proxy_helper`, `per_mgr`, `per_proxy`,
  `mdm_helper`, `/dev/subsys_esoc0`, and WLFW in the same boot?
- Are exact Android `per_proxy_helper` fd timing and GPIO/PMIC transitions
  already captured?
- Is blind native `pm_proxy_helper` retry still closed by prior D-state evidence?

## Hard Gates

- host-only
- no bridge/device command
- no Android boot handoff
- no actor start
- no `/dev/subsys_esoc0` open
- no eSoC ioctl, notify, or BOOT_DONE
- no GPIO/sysfs/debugfs write
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping

## Success Criteria

The classifier must produce a decision and next route without using new device
state. Expected successful decision:

```text
v1021-select-android-pm-esoc-timing-recapture
```

## Validation

Run:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v1020_android_reset_handshake_classifier_v1021.py
python3 scripts/revalidation/native_wifi_v1020_android_reset_handshake_classifier_v1021.py
git diff --check
```


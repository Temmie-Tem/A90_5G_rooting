# V1021 V1020 Android Reset Handshake Classifier

- date: `2026-05-26`
- scope: host-only Android/native reset-handshake classifier
- decision: `v1021-select-android-pm-esoc-timing-recapture`
- pass: `True`
- evidence: `tmp/wifi/v1021-v1020-android-reset-handshake-classifier/manifest.json`

## Summary

V1021 classifies V1020 as a real lower reset-handshake blocker, not an upper
userspace sequencing miss.

V1020 proved:

- fd-positive `mdm_helper` lower surface
- service-manager trio
- Wi-Fi HAL legacy/ext
- `wificond`
- `cnss_diag`
- `cnss-daemon`
- scoped `/dev/subsys_esoc0` open

The child still blocked in:

```text
sdx50m_toggle_soft_reset
mdm4x_do_first_power_on
mdm_cmd_exe
mdm_subsys_powerup
__subsystem_get
subsys_device_open
```

Existing Android evidence proves a positive chain exists, but it does not yet
capture exact `per_proxy_helper` fd timing or GPIO/PMIC transition timing. The
next step should therefore be Android read-only recapture, not another blind
native retry.

## Findings

| Item | Value |
| --- | --- |
| V1020 upper surface reached | pass |
| V1020 `/dev/subsys_esoc0` attempted | pass |
| V1020 stall location | `sdx50m_toggle_soft_reset` |
| V1020 WLFW/BDF/`wlan0` | absent |
| Android `vendor.per_proxy_helper` lifecycle | present |
| Android `vendor.per_mgr` lifecycle | present |
| Android `vendor.per_proxy` lifecycle | present |
| Android `mdm_helper` → `/dev/subsys_esoc0` → WLFW chain | present |
| Android full V968 WLFW/BDF/FW-ready/`wlan0` chain | present |
| blind `pm_proxy_helper` native retry | closed by V867/V868 |
| provider lifetime gap | V944 already selected |

Android timing from existing V1000 evidence:

| Measurement | Value |
| --- | ---: |
| `per_proxy_helper` start → `mdm_helper` start | `2386.188ms` |
| `mdm_helper` start → `/dev/subsys_esoc0` get | `170.463ms` |
| `/dev/subsys_esoc0` get → `wlfw_start` | `7.762ms` |
| `wlfw_start` → WLAN-PD indication | `1013.789ms` |

Existing Android fd snapshot shows:

| Snapshot | Visible |
| --- | --- |
| `mdm_helper` `/dev/esoc-0` fd | yes |
| `pm-service` `/dev/subsys_modem` fd | yes |
| `pm_proxy_helper` fd during active window | no |
| `pm-proxy` process during active window | no |

## Gaps

- Exact Android `pm_proxy_helper` fd timing is missing because the late process
  snapshot no longer caught that oneshot helper.
- GPIO135/AP2MDM assertion timing is still missing.
- PMIC GPIO9 soft-reset deassert timing is still missing.
- Native V1020 did not model `vendor.per_proxy_helper` or `vendor.per_proxy`
  lifecycle, but prior V867/V868 evidence makes blind retry unsafe.

## Decision

Proceed to V1022 as an Android read-only PM/eSoC timing recapture.

The recapture should collect:

- full dmesg focused on `per_proxy_helper`, `per_mgr`, `per_proxy`,
  `mdm_helper`, `/dev/subsys_esoc0`, WLFW, PMIC, and GPIO
- short repeated early `ps`/fd snapshots if the handoff script can run before
  `vendor.per_proxy_helper` exits
- `/proc/interrupts` snapshots for `mdm status`
- `/sys/kernel/debug/gpio` snapshots for GPIO135, GPIO142, and PMIC GPIO9 if
  readable
- init service state for `vendor.per_proxy_helper`, `vendor.per_mgr`,
  `vendor.per_proxy`, `vendor.mdm_helper`, and `cnss-daemon`

## Guardrails

- no device command in V1021
- no native `/dev/subsys_esoc0` retry
- no blind native `pm_proxy_helper` retry
- no eSoC notify or BOOT_DONE
- no GPIO/sysfs/debugfs write
- no `IWifi.start`
- no `qcwlanstate`
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v1020_android_reset_handshake_classifier_v1021.py
python3 scripts/revalidation/native_wifi_v1020_android_reset_handshake_classifier_v1021.py
```

Result:

```text
decision: v1021-select-android-pm-esoc-timing-recapture
pass: True
next: V1022 Android read-only PM/eSoC timing recapture before any native retry
```

## Next

Write and run V1022 Android read-only recapture. If existing Android boot
handoff tooling can capture early enough, use that path. If it cannot catch the
oneshot `vendor.per_proxy_helper` window, use a small Magisk/early-ADB sampler
that only reads dmesg, process/fd state, interrupts, and debug gpio.


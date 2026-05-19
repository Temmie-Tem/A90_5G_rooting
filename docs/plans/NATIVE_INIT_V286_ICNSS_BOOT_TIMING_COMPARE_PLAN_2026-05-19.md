# Native Init v286 ICNSS Boot Timing Compare Plan

- date: `2026-05-19`
- scope: host-side Wi-Fi boot timing analysis
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- target artifact: `scripts/revalidation/wifi_icnss_boot_timing_compare.py`

## Summary

v283-v285 proved that bounded `cnss-daemon -n -l` start-only runs are safe and
observable, but do not produce native ICNSS/QCA6390 readiness deltas.  Repeating
the same start-only experiment is unlikely to add evidence.

v286 shifts from live start-only repetition to timing analysis.  It compares
existing Android/TWRP evidence with current native-init evidence and identifies
which Android boot-time ICNSS/WLAN transition is missing in native init.

## Reference Notes

- Kernel messages are normally emitted through `printk()` and read through
  `dmesg`: https://www.kernel.org/doc/html/latest/core-api/printk-basics.html
- Android bug reports and debugging workflows use `logcat`, `dumpsys`, and
  kernel logs as complementary evidence sources:
  https://source.android.google.cn/docs/core/tests/debug/read-bug-reports?hl=en
- Android init timing often needs kernel log comparison because early boot
  actions span kernel, first-stage init, vendor init, and userspace services:
  https://android.googlesource.com/platform/system/core/+/refs/heads/main-kernel/init/

## Design

The comparator is read-only and input-driven:

1. Android source:
   - default: `tmp/wifi/v204-android-baseline/root-dmesg-wifi-tail.txt`
   - optional manifest fallback: `tmp/wifi/v204-android-baseline/manifest.json`
2. TWRP source:
   - default: `tmp/wifi/v204-twrp-baseline/manifest.json`
3. Native source:
   - default: collect live native `version`, `dmesg`, netdev, wiphy/rfkill,
     module, and process state through cmdv1;
   - can be skipped or replaced with explicit files for offline analysis.

The parser extracts timestamped event classes:

- `icnss_platform_probe`
- `android_wifi_action`
- `wifi_hal_start`
- `cnss_diag_start`
- `wificond_start`
- `cnss_daemon_start`
- `wlfw_start`
- `qmi_server_connected`
- `bdf_download`
- `wlan_fw_ready`
- `firmware_load`
- `wlan_driver_log`
- `fw_ready_event`
- `wlan_netdev`
- `wiphy_rfkill`

The output is a timeline matrix and a missing-event list.

## Guardrails

- No `cnss-daemon` execution.
- No `cnss_diag` execution.
- No QMI payload.
- No QRTR nameservice packet.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.
- No rfkill write.
- No ICNSS bind/unbind or `driver_override`.
- No reboot/recovery/poweroff.
- No Android partition write.

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_icnss_boot_timing_compare.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Plan gate:

```bash
python3 scripts/revalidation/wifi_icnss_boot_timing_compare.py \
  --out-dir tmp/wifi/v286-icnss-boot-timing-plan \
  plan
```

Live native comparison:

```bash
python3 scripts/revalidation/wifi_icnss_boot_timing_compare.py \
  --out-dir tmp/wifi/v286-icnss-boot-timing-native-$(date +%Y%m%d-%H%M%S) \
  run
```

Expected PASS decisions:

- `icnss-boot-timing-plan-ready`
- `icnss-boot-timing-gap-mapped`
- `icnss-boot-timing-refresh-needed`

Expected blocked decisions:

- `icnss-boot-timing-input-missing`
- `icnss-boot-timing-native-capture-failed`

## Acceptance

- Android evidence contains at least one Wi-Fi readiness transition.
- Native evidence is captured read-only from the current build.
- The report identifies the first Android transition missing in native init.
- The tool produces private manifest/summary evidence under `tmp/wifi/...`.

## Next

If v286 maps the gap to Android userspace service ordering, v287 should build a
minimal no-scan service-order replay plan.  If it maps the gap to QMI/WLFW
handshake, v287 should plan a separately approved minimal WLFW/QMI handshake
probe with explicit packet boundaries and rollback gates.

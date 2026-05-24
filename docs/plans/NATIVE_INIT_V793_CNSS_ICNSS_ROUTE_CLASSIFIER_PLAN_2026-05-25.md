# Native Init V793 CNSS/ICNSS Route Classifier Plan

## Goal

Use current V792 live evidence plus prior CNSS, binder, ICNSS, `boot_wlan`,
mdm3, and memshare classifiers to select the next Wi-Fi blocker closest to
WLFW/service `69`, BDF, and `wlan0`.

## Scope

- Read V792 live manifest and dmesg only from local evidence.
- Compare V660/V661/V666 service-manager and binder retry evidence.
- Compare V750/V752 `boot_wlan` and qcwlanstate evidence.
- Compare V763 ICNSS architecture rebase evidence.
- Compare V783/V785 mdm3 and memshare evidence.
- Select the next bounded gate without touching the device.

## Hard Gates

- Host-only only.
- No device command, reboot, mount, daemon start, Wi-Fi HAL, scan/connect,
  credential use, DHCP/routes, external ping, boot image write, partition
  write, or custom kernel flash.
- No broad evidence scan: local reads are bounded.
- No Wi-Fi secret material in tracked output.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_icnss_route_classifier_v793.py
python3 scripts/revalidation/native_wifi_cnss_icnss_route_classifier_v793.py plan
python3 scripts/revalidation/native_wifi_cnss_icnss_route_classifier_v793.py run
git diff --check
```

## Expected Routing

- If V792 CNSS/WLFW state is ambiguous, recapture V792 before any new live gate.
- If service-manager readiness remains unproven, route to service-manager
  readiness.
- If service-manager and binder-only retries are already demoted, and
  `boot_wlan`/memshare-only are demoted, route to a bounded mdm3 + ICNSS/WLFW
  surface observer below HAL/connect.

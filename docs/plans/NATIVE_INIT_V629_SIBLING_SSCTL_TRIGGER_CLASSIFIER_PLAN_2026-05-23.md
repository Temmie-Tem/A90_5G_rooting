# Native Init V629 Sibling-SSCTL Trigger Classifier Plan

- date: `2026-05-23 KST`
- cycle: `v629`
- scope: host-only classifier
- target: choose the next safe gate for the missing Android-equivalent
  SLPI/CDSP/ADSP sibling SSCTL path after V628 classified service `74` as the
  active blocker.

## Background

V627 proved the safe V598/v100 modem-only path still reaches
service-locator and `service-notifier 180` without kernel warnings, but does
not publish service `74`, WLAN-PD, or WLFW service `69`.

V628 narrowed that delta to the sibling SLPI/CDSP/ADSP SSCTL layer:

```text
Android: sibling sysmon + service-notifier 74
Native:  service-locator + service-notifier 180 only
```

V619 is the negative safety bound. Late direct writes to ADSP/CDSP/SLPI boot
nodes exposed sibling `sysmon-qmi`, but also triggered `pm_qos` warnings and
still did not publish service `74`.

## Guardrails

V629 must not:

- contact the device;
- write sysfs or DSP boot nodes;
- build, flash, or upload a boot image;
- open `esoc0`;
- start daemons, service-manager, Wi-Fi HAL, supplicant, or hostapd;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally.

## Inputs

- V628 classifier:
  `tmp/wifi/v628-service74-publisher-classifier/manifest.json`
- V627 live evidence:
  `tmp/wifi/v627-post-180-observer-live-v2/manifest.json`
- V619 live evidence:
  `tmp/wifi/v619-android-order-post-sysmon-observer-run/manifest.json`
- V622 Android same-boot timing evidence:
  `tmp/wifi/v622-android-mdm-helper-timing-handoff-live-20260523-032506/v622-android-mdm-helper-timing-recapture-run/manifest.json`
- V614 vendor init snapshot:
  `tmp/wifi/v614-mdm3-trigger-path-classifier/native/vendor-init-readonly-snapshot.txt`
- Native source tree:
  `stage3/linux_init/`

## Checks

1. Extract Android vendor init boot-node writes for:
   - `/sys/kernel/boot_adsp/boot`
   - `/sys/kernel/boot_cdsp/boot`
   - `/sys/kernel/boot_slpi/boot`
2. Check whether native v319 currently has an equivalent boot-time path.
3. Confirm V627 safe path is warning-free but lacks sibling sysmon/service `74`.
4. Confirm V619 late direct writes are unsafe and still negative for service
   `74`.
5. Keep `boot_wlan`, `qcwlanstate`, and `shutdown_wlan` blocked because they
   are WLAN/HAL-stage controls, not lower service `74` publisher triggers.

## Success Criteria

V629 passes if it selects one of these outcomes without touching the device:

- `v629-boot-time-sibling-ssctl-candidate-classified`
- `v629-sibling-ssctl-trigger-evidence-gap`

Passing V629 does not authorize HAL, scan/connect, credentials, DHCP, routes,
or external ping. A positive result only authorizes planning V630 as a
rollback-ready, opt-in boot-time one-shot proof.


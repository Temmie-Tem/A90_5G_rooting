# Native Init V640 Safe Sibling Trigger Reclassification Plan

- date: `2026-05-23 KST`
- cycle: `v640`
- scope: host-only reclassification plan
- target: choose the next lower Wi-Fi gate after V639 blocked late
  all-sibling direct boot-node writes

## Background

The active Wi-Fi blocker is still below HAL/connect:

- V627/V636 can reproduce warning-free service-notifier `180`.
- Android V622 publishes service `74` only after sibling SLPI/CDSP/ADSP
  `sysmon-qmi` appears.
- V628 classified sibling SSCTL publication as the service `74` prerequisite.
- V619 and V638 prove late direct ADSP/CDSP/SLPI boot-node writes are unsafe:
  they trigger `pm_qos_add_request()` kernel warnings and still do not publish
  service `74`.
- V635 proves CDSP-only firmware-backed write can be warning-free, but CDSP
  alone does not publish service `74`.

Therefore V640 must not simply retry `/sys/kernel/boot_adsp/boot`,
`/sys/kernel/boot_cdsp/boot`, and `/sys/kernel/boot_slpi/boot`.

## Guardrails

V640 must not:

- contact the device unless a later live gate is separately approved;
- write sysfs, DSP boot nodes, `boot_wlan`, `qcwlanstate`, or
  `shutdown_wlan`;
- start CNSS, service-manager, Wi-Fi HAL, supplicant, hostapd, scan/connect, or
  credential handling;
- run DHCP, change routes, or ping externally;
- build, flash, or reboot as part of this host-only classification.

## Inputs

- V622 Android same-boot lower surface:
  `tmp/wifi/v622-android-mdm-helper-timing-handoff-live-20260523-032506/v622-android-mdm-helper-timing-recapture-run/manifest.json`
- V627 post-`180` observer:
  `docs/reports/NATIVE_INIT_V627_POST_180_OBSERVER_LIVE_2026-05-23.md`
- V628 service `74` publisher classifier:
  `docs/reports/NATIVE_INIT_V628_SERVICE74_PUBLISHER_CLASSIFIER_2026-05-23.md`
- V635 CDSP-only warning-free proof:
  `tmp/wifi/v635-cdsp-proof-20260523-052940/manifest.json`
- V636 CDSP+V598 warning-free service `180` proof:
  `tmp/wifi/v636-cdsp-v598-live-20260523-054728/manifest.json`
- V638 all-sibling warning proof:
  `tmp/wifi/v638-firmware-sibling-live-20260523-060104/manifest.json`
- V639 warning attribution:
  `tmp/wifi/v639-sibling-warning-attribution-classifier/manifest.json`

## Checks

1. Re-list every known service `74` prerequisite and mark direct
   ADSP/CDSP/SLPI boot-node writes as blocked by V639.
2. Compare Android V622 timing:
   - sibling `sysmon-qmi`;
   - service-locator;
   - service `180`;
   - service `74`;
   - `rmt_storage`, `tftp_server`, `pd_mapper`, `mdm_helper`, CNSS.
3. Determine whether any non-write Android userspace service starts before
   service `74` and is still untested in the warning-free native path.
4. If no non-write trigger exists, classify the next safe option as a
   boot-window-only or boot-image gated proof, not a late live write.
5. Use V638 warning timestamps to decide whether any per-node late proof remains
   defensible. CDSP-only is warning-free, but ADSP/SLPI and all-sibling late
   paths remain blocked unless a new safety guard is proven.
6. Keep credentials, scan/connect, DHCP, routes, and external ping blocked until
   service `74`, WLAN-PD, WLFW/BDF, firmware-ready, or `wlan0` advances.

## Candidate Outcomes

V640 should select one of:

- `v640-nonwrite-service74-publisher-candidate`
- `v640-boot-window-only-sibling-trigger-needed`
- `v640-kernel-source-or-android-recapture-needed`
- `v640-unsafe-direct-write-paths-exhausted`

## Success Criteria

V640 passes if it identifies the next gate without reauthorizing late direct
all-sibling writes. The next gate must be closer to native service `74`
publication than the current warning-free service `180` baseline and must keep
Wi-Fi credentials and external connectivity blocked until lower markers
advance.

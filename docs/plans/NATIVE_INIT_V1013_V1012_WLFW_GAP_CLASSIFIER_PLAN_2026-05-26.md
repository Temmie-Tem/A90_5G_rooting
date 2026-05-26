# V1013 V1012 WLFW Gap Classifier Plan

- date: `2026-05-26`
- type: host-only evidence classifier
- selected after: V1012 after-fd CNSS/service-manager matrix
- next candidate on pass: V1014 helper `v172` after-fd Wi-Fi surface matrix

## Objective

Classify why V1012 preserved the `mdm_helper` `/dev/esoc-0` fd predicate and
started service-manager/CNSS, but still did not observe the WLFW precondition.

The classifier decides whether the next safe unit should add Android upper
Wi-Fi surface actors after the proven fd predicate, instead of retrying
`/dev/subsys_esoc0`, direct eSoC ioctls, scan/connect, or Wi-Fi HAL bring-up.

## Inputs

- V1012 live manifest:
  `tmp/wifi/v1012-after-fd-cnss-service-manager-matrix-live/manifest.json`
- V1008 Android service-window fd-poll live manifest:
  `tmp/wifi/v1008-android-service-window-fd-poll-live/manifest.json`
- Android-good dmesg timing from the V1000/V913 handoff:
  `tmp/wifi/v1000-android-esoc-gpio-recapture-handoff-live/v913-android-esoc-gpio-timeline-run/android/commands/dmesg-full.txt`
- Current helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`

## Method

1. Confirm V1012 preserved the lower fd predicate with
   `service_manager_order=after-mdm-helper-esoc-fd`.
2. Confirm V1012 started service-manager and CNSS, but did not observe WLFW and
   did not open `/dev/subsys_esoc0`.
3. Confirm V1008 had Wi-Fi HAL, `wificond`, and CNSS upper actors, but lost the
   `mdm_helper` fd predicate.
4. Parse Android-good dmesg for Wi-Fi HAL legacy/ext, `wificond`,
   `mdm_helper`, CNSS, `/dev/subsys_esoc0`, WLFW, WLAN-PD, and ICNSS QMI timing.
5. Inspect helper source to verify upper actor contracts exist, the after-fd
   lower matrix exists, and the combined after-fd Wi-Fi surface matrix does not
   yet exist.

## Hard Gates

- host-only classification
- no bridge/device command
- no Android boot or ADB command
- no Magisk module install
- no live eSoC ioctl
- no `/dev/subsys_esoc0` open
- no Wi-Fi HAL start, scan/connect, credential use, DHCP/route, or external ping
- no boot image, partition, firmware, GPIO, sysfs, or debugfs write

## Success Criteria

- Private evidence manifest and summary are written under
  `tmp/wifi/v1013-v1012-wlfw-gap-classifier/`.
- Decision is `v1013-select-after-fd-wifi-surface-matrix-support`.
- The next route is
  `v1014-source-build-helper-v172-after-fd-dual-hal-wificond-matrix`.
- The result explains why Android dmesg/Magisk timing work does not need to
  block this unit: V968/V1000 already provide enough service-window ordering for
  the upper-surface route, while exact GPIO level timing remains a separate
  sampler candidate only if the parity route fails again.

## Implementation

Add:

```text
scripts/revalidation/native_wifi_v1012_wlfw_gap_classifier_v1013.py
```

The script produces:

- `manifest.json`
- `summary.md`
- `tmp/wifi/latest-v1013-v1012-wlfw-gap-classifier.txt`

## Validation

Run:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v1012_wlfw_gap_classifier_v1013.py
python3 scripts/revalidation/native_wifi_v1012_wlfw_gap_classifier_v1013.py
git diff --check
```

Then run a secret scan over only changed and untracked files.

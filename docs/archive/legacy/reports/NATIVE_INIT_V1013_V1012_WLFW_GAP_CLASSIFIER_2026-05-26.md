# V1013 V1012 WLFW Gap Classifier

- date: `2026-05-26`
- scope: host-only classifier over V1012/V1008/Android dmesg/helper-source evidence
- decision: `v1013-select-after-fd-wifi-surface-matrix-support`
- pass: `True`
- evidence: `tmp/wifi/v1013-v1012-wlfw-gap-classifier/manifest.json`

## Summary

V1013 closes the V1012 gap as an ordering/surface-composition problem:

- V1012 proved `mdm_helper` can keep `/dev/esoc-0` open while service-manager and
  CNSS are started afterward.
- V1012 still did not observe WLFW, and did not open `/dev/subsys_esoc0`.
- V1008 proved Wi-Fi HAL, `wificond`, and CNSS can be started in the fuller
  Android service window, but that route lost the `mdm_helper` fd predicate.
- Android-good dmesg shows Wi-Fi HAL legacy/ext and `wificond` precede
  `mdm_helper`, CNSS, `/dev/subsys_esoc0`, WLFW, WLAN-PD, and ICNSS QMI.

The next unit should therefore combine the two halves: preserve the after-fd
predicate first, then add the Android upper Wi-Fi surface actors before CNSS,
without scan/connect or `IWifi.start`.

## Evidence Split

| Evidence | Result |
| --- | --- |
| V1012 | fd predicate, service-manager, and CNSS are present; WLFW precondition is absent |
| V1008 | Wi-Fi HAL, `wificond`, and CNSS are present; fd predicate is absent |
| Android dmesg | upper Wi-Fi surface appears before WLFW-positive lower events |
| helper source | upper actor contracts exist, but after-fd Wi-Fi surface matrix is missing |

## Android Timing

| Event | Time |
| --- | ---: |
| Wi-Fi HAL legacy start | `6.854689s` |
| Wi-Fi HAL ext start | `6.965385s` |
| `wificond` start | `8.147853s` |
| `mdm_helper` start | `8.256167s` |
| `cnss-daemon` start | `8.263292s` |
| `/dev/subsys_esoc0` get | `8.426630s` |
| `cnss-daemon wlfw_start` | `8.434392s` |
| WLAN-PD indication | `9.448181s` |
| ICNSS QMI connected | `9.450701s` |

## Relation To Android dmesg / Magisk Direction

The Android dmesg direction is valid, but it is not a new blocker for V1013:

- V968 already classified existing Android dmesg/sysfs evidence and found that
  exact GPIO135/GPIO142 level-transition timing would require an early sampler.
- V1000 later recaptured Android lower timing and provided enough ordering
  evidence for this service-window route.
- A Magisk module or early ADB sampler remains useful only if the combined
  after-fd Wi-Fi surface matrix still fails and exact GPIO transition timing
  becomes the remaining variable.

## Decision

Proceed to V1014:

```text
v1014-source-build-helper-v172-after-fd-dual-hal-wificond-matrix
```

V1014 should add source/build-only helper support for an
`after-mdm-helper-esoc-fd` Wi-Fi surface matrix:

1. start property shim and lower `per_mgr`/`mdm_helper`
2. prove `/dev/esoc-0` fd before expanding the surface
3. start service-manager trio
4. start Wi-Fi HAL legacy, Wi-Fi HAL ext, and `wificond`
5. start CNSS actors
6. observe WLFW only

## Guardrails

V1013 did not run bridge/device commands, Android ADB, Magisk modules, live eSoC
ioctls, `/dev/subsys_esoc0`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes,
external ping, boot image writes, partition writes, firmware writes, GPIO
writes, sysfs writes, or debugfs writes.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v1012_wlfw_gap_classifier_v1013.py
python3 scripts/revalidation/native_wifi_v1012_wlfw_gap_classifier_v1013.py
git diff --check
```

Result:

```text
decision: v1013-select-after-fd-wifi-surface-matrix-support
pass: True
route: v1014-source-build-helper-v172-after-fd-dual-hal-wificond-matrix
```

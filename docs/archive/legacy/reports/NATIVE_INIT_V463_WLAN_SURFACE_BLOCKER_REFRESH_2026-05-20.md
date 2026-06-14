# Native Init V463 WLAN Surface Blocker Refresh

Date: 2026-05-20

## Summary

V463 refreshed the WLAN surface blocker after V462 proved that native init
cannot yet run the requested Wi-Fi external ping proof.  The refresh confirms
the blocker is not stale:

```text
decision: icnss-boot-timing-gap-mapped
pass: True
reason: first Android timing event missing in native: android_wifi_action
native_version_matches: True
```

The current native build is `A90 Linux init 0.9.61 (v319)`.  The missing step is
still before credentials, scan/connect, DHCP, or external ping: native init has
not recreated Android's Wi-Fi service-order transition that eventually creates
`wlan0`/wiphy readiness.

## Evidence

Native connect/ping gate:

```text
tmp/wifi/v462-native-wifi-connect-ping-run-20260520-230620/
decision: v462-native-wifi-ping-blocked-no-wlan-surface
pass: False
```

Boot timing refresh:

```text
tmp/wifi/v463-icnss-boot-timing-refresh-v319-20260520-230801/
decision: icnss-boot-timing-gap-mapped
pass: True
reason: first Android timing event missing in native: android_wifi_action
```

Service-order replay refresh:

```text
tmp/wifi/v463-service-order-replay-refresh-v319-20260520-230805/
decision: wifi-service-order-replay-model-ready
pass: True
reason: Android service-order gap is mapped without live execution
```

An initial refresh without `--expect-version "A90 Linux init 0.9.61 (v319)"`
failed only because the comparator default still expected an older build.  The
v319 rerun passed.

## Reference Check

The current repo evidence matches the upstream architecture:

- Android's Wi-Fi stack is split across vendor Wi-Fi HAL, supplicant HAL, and
  hostapd HAL surfaces; the supplicant HAL fronts `wpa_supplicant`.
  Reference: <https://source.android.com/docs/core/connect/wifi-hal>
- Qualcomm ICNSS/WLFW code paths gate WLAN work on firmware-ready state, and
  WLFW QMI definitions include BDF download and firmware-ready/init-done
  messages.
  References:
  <https://android.googlesource.com/kernel/msm/+/15cf51a0f2ebde6529357685543e0b4170fb3b5c/drivers/soc/qcom/icnss.c>
  and
  <https://android.googlesource.com/kernel/msm/+/c2aee3401467314b48882a22d71906f380a5c17a/drivers/net/wireless/cnss2/wlan_firmware_service_v01.h>

This supports the current local conclusion: a native ping attempt must wait
until the Android-like Wi-Fi service/firmware readiness chain has produced a
real kernel WLAN surface.

## Interpretation

The next blocker is **WLAN surface creation**, not AP credentials or ping
syntax.

Current facts:

- Android live flow can scan/connect/cleanup/rollback successfully.
- Native v319 after rollback has no `wlan*`, no `phy*`, and no Wi-Fi rfkill.
- Isolated `cnss-daemon` start-only previously stayed safe but did not create
  WLAN readiness.
- Bounded HAL/service-manager start-only previously made processes observable
  but still did not prove registration or create WLAN readiness.
- V463 refresh maps the first missing native event to Android Wi-Fi action /
  service-order transition.

## Next

Recommended next implementation: V464 native WLAN surface bring-up delta.

V464 should be bounded and still avoid credentials and external traffic:

1. collect before snapshot: `wlan*`, `phy*`, rfkill, ICNSS/QCA6390 sysfs,
   dmesg focus, process table;
2. run the smallest approved native service-order attempt that can plausibly
   trigger Android's `wlan_fw_ready` path;
3. collect during/after snapshots and classify only whether `wlan0`/wiphy
   appears;
4. clean all started processes and require postflight process/link safety;
5. proceed to native scan/connect/ping only after V464 proves a WLAN surface.

V464 must still block Wi-Fi credentials, scan/connect, DHCP, route changes, and
external ping until the native WLAN surface exists.

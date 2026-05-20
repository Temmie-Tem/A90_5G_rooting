# Native Init V464 Native WLAN Surface Composite

Date: 2026-05-20

## Summary

V464 added and executed a bounded native-init WLAN surface composite gate.  The
new helper mode starts the smallest currently implemented native runtime set in
one private namespace:

- `servicemanager`
- `hwservicemanager`
- Samsung vendor Wi-Fi HAL
- `cnss-daemon -n -l`

The run stayed clean, but it did **not** create a native WLAN surface:

```text
decision: v464-native-wlan-surface-not-observed
pass: True
reason: bounded composite start stayed clean but did not create wlan/wiphy/rfkill surface
next: add the next Android runtime primitive before native scan/connect
```

This means the native Wi-Fi connect/ping objective is still blocked before
credentials, scan, DHCP, route, or external ping.

## Implementation

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
  - bumped helper marker to `a90_android_execns_probe v31`;
  - added `wifi-surface-composite-start-only`;
  - added bounded surface snapshots for `wlan*`, `phy*`, `/proc/net/wireless`,
    and Wi-Fi rfkill before/during/after cleanup;
  - starts CNSS together with service-manager and Wi-Fi HAL only when
    `--allow-cnss-start-only`, `--allow-service-manager-start-only`, and
    `--allow-wifi-hal-start-only` are all present.
- `scripts/revalidation/wifi_execns_helper_v31_deploy_preflight.py`
  - deploys only `/cache/bin/a90_android_execns_probe`;
  - requires the exact V464 deploy phrase;
  - does not start daemons or bring up Wi-Fi.
- `scripts/revalidation/native_wifi_surface_composite_v464.py`
  - runs plan/preflight/live modes;
  - verifies helper v31, SELinuxfs runtime surface, private property/runtime
    material, service-manager binaries, vendor block source, clean process
    surface, and clean Wi-Fi link surface;
  - blocks credentials, scan/connect, DHCP, route changes, and external ping.

## Evidence

Helper build:

```text
tmp/wifi/v464-a90_android_execns_probe-v31/a90_android_execns_probe
sha256: 96179d75ee81586cf8f46edb7354eeb8c57569e56a047a2c55e678c794a514e9
marker: a90_android_execns_probe v31
```

SELinuxfs runtime surface:

```text
tmp/wifi/v464-selinuxfs-mount-20260520-232657/
decision: toybox-selinuxfs-mount-live-executor-run-pass
pass: True
```

Helper deploy:

```text
tmp/wifi/v464-helper-v31-deploy-live-20260520-232721/
decision: execns-helper-v31-deploy-pass
pass: True
```

Preflight:

```text
tmp/wifi/v464-native-wlan-surface-preflight-fixed-20260520-233438/
decision: v464-native-wlan-surface-preflight-ready
pass: True
```

Live:

```text
tmp/wifi/v464-native-wlan-surface-live-fixed-20260520-233438/
decision: v464-native-wlan-surface-not-observed
pass: True
postflight.clean: True
helper_result: start-only-pass
child_started: 4
cnss_daemon_requested: True
```

Surface snapshots:

| phase | wlan | phy | wireless | Wi-Fi rfkill |
| --- | ---: | ---: | ---: | ---: |
| before | 0 | 0 | 0 | 0 |
| during | 0 | 0 | 0 | 0 |
| after cleanup | 0 | 0 | 0 | 0 |

Post-V464 native ping gate:

```text
tmp/wifi/v462-post-v464-native-wifi-connect-ping-20260520-233519/
decision: v462-native-wifi-ping-blocked-no-wlan-surface
pass: False
```

## Interpretation

V464 proves four useful facts:

1. Native can run service-manager, hwservicemanager, Samsung Wi-Fi HAL, and
   `cnss-daemon` together in one bounded private namespace.
2. The helper can observe and clean all four child processes safely.
3. `cnss-daemon` reaches the kernel `cld80211` generic netlink family, so the
   path is not failing at basic exec/identity/netlink setup.
4. Daemon presence alone is still insufficient: no `wlan0`, `phy*`,
   `/proc/net/wireless` entry, or Wi-Fi rfkill appears.

The next missing primitive is therefore not the AP password or ping syntax.  It
is the Android Wi-Fi framework/HAL control transition that calls into the Wi-Fi
HAL to start the chip/driver path.

This matches the reference architecture:

- Android Wi-Fi is split across vendor Wi-Fi HAL, supplicant HAL, and hostapd
  HAL surfaces, so daemon presence is only one part of bring-up:
  <https://source.android.com/docs/core/connect/wifi-hal>
- Qualcomm ICNSS/WLFW paths gate WLAN readiness on firmware-ready/BDF/QMI
  state rather than simple process lifetime:
  <https://android.googlesource.com/kernel/msm/+/15cf51a0f2ebde6529357685543e0b4170fb3b5c/drivers/soc/qcom/icnss.c>
  and
  <https://android.googlesource.com/kernel/msm.git/+/856fb46bfd444b8fbf18afb4c469d12fa9fb6275/drivers/net/wireless/cnss2/wlan_firmware_service_v01.h>

## Next

Recommended next version: V465 native `IWifi.start` control gate.

V465 should not use Wi-Fi credentials yet.  It should first prove one of these
bounded control paths can create a WLAN surface:

1. start the same private runtime used by V464;
2. issue a minimal vendor Wi-Fi HAL start control equivalent to Android's
   framework Wi-Fi enable path;
3. observe only `wlan*`/`phy*`/rfkill/dmesg readiness delta;
4. clean all children;
5. keep scan/connect/DHCP/external ping blocked until a WLAN surface exists.

Only if V465 creates `wlan0` or `phy*` should the next gate read credentials
and attempt scan/connect/ping.

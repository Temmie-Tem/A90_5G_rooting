# Native Init V435 Android Wi-Fi Auto-connect Disable Plan

Date: 2026-05-20

## Goal

V435 implements the containment policy selected by V434.  It is the first
bounded cleanup gate that may mutate Android Wi-Fi state.  The only permitted
mutation is disabling Android Wi-Fi with:

```text
cmd wifi set-wifi-enabled disabled
```

The gate then proves whether route, DNS, validated-connectivity, and listener
exposure are removed.

## Scope

Allowed:

- temporarily flash the known Android boot image;
- wait for Android ADB and `sys.boot_completed=1`;
- capture pre-disable Wi-Fi status, settings, routes, `wlan0`, connectivity,
  and listener state;
- run exactly one Wi-Fi cleanup mutation:
  `cmd wifi set-wifi-enabled disabled`;
- capture post-disable route/DNS/connectivity/listener state;
- restore native init v319 with rollback evidence.

Not allowed:

- Wi-Fi scan/connect, credential operations, saved-network edits, or server
  exposure;
- DHCP/routing mutation, external packet probes, `ip link set`, rfkill/sysfs
  writes, module operations, `setprop`, or direct daemon starts;
- Wi-Fi re-enable in this gate.

## Implementation

- Collector: `scripts/revalidation/wifi_android_autoconnect_disable_v435.py`
  - requires `--allow-wifi-disable` and
    `--i-understand-android-wifi-setting-mutation` for live run;
  - blocks scan/connect/server/probe/routing/sysfs command patterns;
  - captures pre/post status and exposure state;
  - treats active connectivity as active `NetworkAgentInfo{...WIFI CONNECTED...}`
    evidence, not stale `NetworkRequest` or history lines.
- Handoff wrapper:
  `scripts/revalidation/android_wifi_autoconnect_disable_handoff_v435.py`
  - reuses Android boot-complete handoff and native rollback primitives;
  - requires both boot/rollback approval flags and V435 Wi-Fi-disable flags;
  - restores native init even if the V435 collector fails.

## Validation Plan

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_autoconnect_disable_v435.py \
  scripts/revalidation/android_wifi_autoconnect_disable_handoff_v435.py

python3 scripts/revalidation/wifi_android_autoconnect_disable_v435.py \
  --out-dir tmp/wifi/v435-android-wifi-disable-plan-<ts> \
  --allow-wifi-disable --i-understand-android-wifi-setting-mutation \
  plan

python3 scripts/revalidation/android_wifi_autoconnect_disable_handoff_v435.py \
  --out-dir tmp/wifi/v435-android-wifi-disable-handoff-dryrun-<ts> \
  --allow-android-boot-flash --assume-yes --i-understand-native-rollback \
  --allow-wifi-disable --i-understand-android-wifi-setting-mutation \
  dry-run

git diff --check
```

Live sequence:

1. confirm native v319 status over the bridge;
2. boot Android and wait for boot-complete;
3. run V435 disable proof;
4. verify post-disable Wi-Fi/route/DNS/connectivity/listener containment;
5. restore native v319;
6. verify native `version`, `selftest`, and `status`;
7. scan evidence for raw SSID/BSSID/security-type leaks.

## Expected Decisions

- `v435-android-wifi-disable-plan-ready`
- `v435-handoff-plan-ready`
- `v435-handoff-dryrun-ready`
- `v435-android-wifi-autoconnect-contained-pass`
- `v435-android-wifi-disable-partial-containment`
- `v435-android-wifi-disable-not-contained`
- `v435-android-wifi-disable-command-failed`
- `v435-handoff-disable-approval-required`

Any PASS decision must keep `wifi_bringup_executed=False`.

## Next Gate Rule

If V435 passes, V436 should verify persistence: Android should stay contained on
a fresh Android boot without requiring another disable command.  Re-enable,
scan/connect, credentials, and server exposure remain blocked until a later
explicit policy gate.

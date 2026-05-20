# Native Init V432 Android Wi-Fi Control Gate Plan

Date: 2026-05-20

## Goal

V432 defines the first Android-managed Wi-Fi control gate after V431 proved the
Android boot-complete runtime already owns the complete Wi-Fi service surface.
The gate is intentionally read-only: it determines whether the next action
should be enable-only, status/stability, or containment before any explicit
scan/connect operation is allowed.

## Scope

Allowed:

- temporarily flash the known Android boot image;
- wait for Android ADB and `sys.boot_completed=1`;
- run read-only Android Wi-Fi framework, settings, process, netdev, rfkill, and
  filtered `dumpsys wifi` captures;
- restore native init v319 with rollback evidence;
- redact MAC, IP, SSID/BSSID, serial, and credential-like fields from evidence.

Not allowed:

- `svc wifi enable/disable`;
- mutating `cmd wifi` subcommands such as `set-wifi-enabled`, `start-scan`,
  `connect-network`, `add-network`, `forget-network`, or country-code changes;
- `iw` scan/connect/set, `wpa_cli`, credentials, DHCP, routing, rfkill/sysfs
  writes, module load/unload, `setprop`, or direct daemon starts.

## Implementation

- Collector: `scripts/revalidation/wifi_android_control_gate_v432.py`
  - records `cmd wifi status`, safe `cmd wifi` help output, global/secure
    settings, framework service names, Wi-Fi processes, `wlan0` state, rfkill
    state, and filtered `dumpsys wifi`;
  - has a fail-fast command-pattern guard to block mutating Wi-Fi control
    commands from entering the capture list;
  - classifies Android state into disabled/enable-ready, already-up,
    already-connected-auto, review-required, or blocked;
  - keeps `wifi_bringup_executed=False` for all modes.
- Handoff wrapper: `scripts/revalidation/android_wifi_control_gate_handoff_v432.py`
  - reuses Android boot-complete handoff and native rollback primitives;
  - replaces the V423 inventory step with the V432 control-gate collector after
    boot-complete settle;
  - maps the collector decision into a rollback-verified handoff decision.

## Validation Plan

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_control_gate_v432.py \
  scripts/revalidation/android_wifi_control_gate_handoff_v432.py

python3 scripts/revalidation/wifi_android_control_gate_v432.py \
  --out-dir tmp/wifi/v432-android-control-gate-plan-<ts> plan

python3 scripts/revalidation/android_wifi_control_gate_handoff_v432.py \
  --out-dir tmp/wifi/v432-android-control-gate-handoff-dryrun-<ts> \
  --allow-android-boot-flash --assume-yes --i-understand-native-rollback \
  dry-run

git diff --check
```

Live sequence:

1. confirm native v319 status over the bridge;
2. flash Android boot image from recovery;
3. wait for Android `sys.boot_completed=1`;
4. run V432 read-only Android Wi-Fi control collector;
5. reboot to recovery and restore native v319;
6. verify native `version`, `selftest`, and `status`.

## Expected Decisions

- `v432-android-control-gate-plan-ready`
- `v432-handoff-plan-ready`
- `v432-handoff-dryrun-ready`
- `v432-android-wifi-enable-only-ready`
- `v432-android-wifi-already-up-control-gate-pass`
- `v432-android-wifi-already-connected-auto-gate-pass`
- `v432-android-wifi-control-review-required`
- `v432-android-wifi-control-blocked`

Any PASS decision must keep `wifi_bringup_executed=False`.

## Next Gate Rule

If Android is already connected from saved framework state, the next gate is not
enable-only and not scan/connect.  It must first characterize containment,
stability, routing exposure, and cleanup behavior around the existing
auto-connected state.

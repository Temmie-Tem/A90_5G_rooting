# Native Init V431 Android Wi-Fi Runtime Gap Map Plan

Date: 2026-05-20

## Goal

V431 maps the Android boot-complete Wi-Fi runtime that native private namespace
experiments do not yet reproduce.  V430 proved Android has the Samsung
`ISehWifi/default` target rows while native V429 still times out on binderized
`lshal`.  V431 therefore stops using `lshal -S` as the decisive probe and maps
what Android already has running.

## Scope

Allowed:

- temporarily flash the known Android boot image;
- wait for Android ADB and `sys.boot_completed=1`;
- run read-only Android shell captures, optionally through `su -c` for read-only
  visibility into `/data/vendor/wifi` layout;
- collect service definitions, properties, process metadata, sockets, devnodes,
  netdev/rfkill state, and Wi-Fi data directory layout;
- restore native init v319 with rollback evidence.

Not allowed:

- Wi-Fi enable, scan, connect, link-up, credentials, DHCP, or routing;
- `svc wifi`, mutating `cmd wifi`, `iw` scan/connect/set, `wpa_cli`, rfkill or
  sysfs writes, module load/unload, or `setprop`;
- direct daemon start commands;
- reading Wi-Fi credential file contents.

## Implementation

- Collector: `scripts/revalidation/wifi_android_runtime_gap_v431.py`
  - captures target runtime processes for:
    - `android.hardware.wifi@1.0-service`;
    - `vendor.samsung.hardware.wifi@2.0-service`;
    - `wificond`;
    - `wpa_supplicant`;
  - captures init rc context, framework service names, proc status/fd/maps,
    socket surface, devnode surface, netdev/rfkill state, and data directory
    layout;
  - strips command lines from surface classification so command text cannot
    create false-positive evidence;
  - redacts serial, MAC, SSID/passphrase-like fields.
- Handoff wrapper: `scripts/revalidation/android_wifi_runtime_gap_handoff_v431.py`
  - reuses the V424/V425 Android boot-complete and rollback path;
  - runs the V431 collector after boot-complete settle;
  - supports `--collector-su` for read-only privileged collection.

## Validation Plan

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_runtime_gap_v431.py \
  scripts/revalidation/android_wifi_runtime_gap_handoff_v431.py

python3 scripts/revalidation/wifi_android_runtime_gap_v431.py \
  --out-dir tmp/wifi/v431-android-runtime-gap-plan-<ts> plan

python3 scripts/revalidation/android_wifi_runtime_gap_handoff_v431.py \
  --out-dir tmp/wifi/v431-android-runtime-gap-handoff-dryrun-<ts> \
  --collector-su \
  --allow-android-boot-flash --assume-yes --i-understand-native-rollback \
  dry-run

git diff --check
```

Live sequence:

1. confirm native v319 status over the bridge;
2. flash Android boot image from recovery;
3. wait for Android `sys.boot_completed=1`;
4. run V431 read-only runtime gap collector through `su -c`;
5. reboot to recovery and restore native v319;
6. verify native `version`, `selftest`, and `status`.

## Expected Decisions

- `v431-android-runtime-gap-map-plan-ready`
- `v431-handoff-plan-ready`
- `v431-handoff-dryrun-ready`
- `v431-android-runtime-gap-map-pass`
- `v431-android-runtime-gap-map-partial-surface-pass`
- `v431-android-runtime-gap-runtime-present-definitions-partial`

Any PASS decision must keep `wifi_bringup_executed=False`.

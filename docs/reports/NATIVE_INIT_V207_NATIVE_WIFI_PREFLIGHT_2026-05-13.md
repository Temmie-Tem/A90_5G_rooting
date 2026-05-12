# v207 Native Read-Only Wi-Fi Preflight

## Summary

v207 adds and validates a native-side read-only Wi-Fi preflight collector. It
does not modify the native boot image and does not enable Wi-Fi.

Result: PASS.

Final decision: `missing-mounted-vendor`.

Reason: native control, `/mnt/system`, and the ICNSS platform node are visible,
but Android-mapped vendor firmware/init paths are not reliably visible from the
current native mount layout.

Active Wi-Fi bring-up remains blocked.

## Changes

- Added `scripts/revalidation/native_wifi_preflight.py`.
- Added v207 plan:
  `docs/plans/NATIVE_INIT_V207_NATIVE_WIFI_PREFLIGHT_PLAN_2026-05-13.md`.
- Updated task queue and next-work notes.

## Scope

The collector captures native read-only evidence from:

- version/status/bootstatus
- `mountsystem ro`
- mounted-system init and firmware candidate paths
- ICNSS sysfs
- WLAN netdev, rfkill, and `ieee80211` state
- firmware loader state
- optional existing `/cache/bin/a90_nl80211_ro` GET-only helper state
- v205/v206 manifest comparison

## Guardrails

- No Wi-Fi enablement.
- No rfkill write.
- No WLAN link-up.
- No scan/connect.
- No active `nl80211` set/scan/connect commands.
- No module load/unload.
- No firmware path write.
- No firmware mutation.
- No `cnss-daemon`, `wificond`, Wi-Fi HAL, supplicant, or hostapd start.
- Default mode does not deploy helper or write device files.

## Static Validation

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_preflight.py \
  scripts/revalidation/wifi_icnss_nl80211_probe.py \
  scripts/revalidation/android_icnss_cnss_map.py \
  scripts/revalidation/a90harness/evidence.py
```

Result: PASS.

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import native_wifi_preflight
native_wifi_preflight.validate_no_active_wifi_commands()
print('v207 command guard PASS')
PY
```

Result: PASS.

```bash
git diff --check
```

Result: PASS.

## Device Validation

Bridge precheck:

```bash
python3 scripts/revalidation/a90ctl.py --json version
```

Result: PASS.

Runtime:

- `A90 Linux init 0.9.59 (v159)`

Collector run:

```bash
python3 scripts/revalidation/a90ctl.py hide || true
python3 scripts/revalidation/a90ctl.py mountsystem ro

python3 scripts/revalidation/native_wifi_preflight.py \
  --native-bridge \
  --v205-manifest tmp/wifi/v205-icnss-nl80211-readonly/manifest.json \
  --v206-manifest tmp/wifi/v206-android-icnss-cnss-map/manifest.json \
  --out-dir tmp/wifi/v207-native-wifi-preflight
```

Result: PASS.

Decision:

```text
missing-mounted-vendor
```

Evidence:

- `tmp/wifi/v207-native-wifi-preflight/manifest.json`
- `tmp/wifi/v207-native-wifi-preflight/summary.md`
- `tmp/wifi/v207-native-wifi-preflight/native/commands/`

Hashes:

- `tmp/wifi/v207-native-wifi-preflight/manifest.json`:
  `d3d88598d9b66b179044416a404d5649f377567482a74e214ac07706e9aae7b4`
- `tmp/wifi/v207-native-wifi-preflight/summary.md`:
  `ef1dd5cfa4acca5003fb2041f194834b796ab1402981d3a712228ef31490edb6`

## Current Result

- `basic_control_ok`: `true`
- `mountsystem_ok`: `true`
- `mounted_system_visible`: `true`
- `mounted_vendor_visible`: `false`
- `firmware_visible`: `false`
- `native_icnss`: `true`
- `native_wiphy`: `false`
- `native_wifi_rfkill`: `false`
- `nl80211_helper_present`: `false`
- `nl80211_helper_ran`: `false`
- `android_ready_from_v206`: `true`
- `v205_decision`: `native-icnss-present-no-wiphy`
- `v206_decision`: `ready-for-native-preflight-plan`

Important evidence:

```text
/sys/devices/platform/soc/18800000.qcom,icnss
/vendor/firmware_mnt/image
ls: /mnt/system/vendor/firmware: No such file or directory
ls: /mnt/system/vendor/firmware_mnt: No such file or directory
ls: /mnt/system/vendor/etc/wifi: No such file or directory
stat: /mnt/system/vendor/firmware/wlan/qca_cld/bdwlan.bin: No such file or directory
stat: /mnt/system/vendor/firmware/wlan/qca_cld/regdb.bin: No such file or directory
stat: /mnt/system/vendor/firmware/wlanmdsp.mbn: No such file or directory
stat: /sys/class/net/wlan0: No such file or directory
stat: /cache/bin/a90_nl80211_ro: No such file or directory
```

## Interpretation

v206 proved Android can map the Wi-Fi service/firmware/ICNSS chain. v207 proves
the current native environment can control the device and can see ICNSS, but the
Android-mapped vendor firmware/init paths are not exposed by the current
`mountsystem ro` view.

The next useful step is not Wi-Fi bring-up and not `ip link set wlan0 up`.
Native still lacks the visible vendor firmware/init prerequisites needed for a
safe daemon feasibility step.

## Acceptance

- Native read-only preflight collector implemented.
- Command guard blocks active Wi-Fi command patterns.
- Evidence output uses private/no-follow `EvidenceStore`.
- Live native run completed through the bridge.
- Decision produced without enabling Wi-Fi.
- Active Wi-Fi bring-up remains blocked.

## Next

Recommended v208 scope: native vendor/firmware mount visibility plan.

The next plan should identify which partition or bind-mount path exposes
Android vendor firmware/init assets from native, read-only first. It should
compare `/proc/partitions`, by-name links if available, `/proc/mounts`, and
Android v206 firmware/init paths before any CNSS daemon feasibility work.

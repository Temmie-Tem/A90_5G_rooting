# v205 ICNSS/WCNSS/QCA + nl80211 Read-Only Probe

## Summary

v205 implements and validates a native read-only ICNSS/WCNSS/QCA + `nl80211`
probe collector. It does not enable Wi-Fi, write rfkill state, bring up a WLAN
interface, scan, connect, load or unload modules, mutate firmware, or start
Android Wi-Fi services.

Result: PASS.

Final decision: `native-icnss-present-no-wiphy`.

Reason: native init can see the ICNSS platform sysfs node, but still does not
see WLAN netdevs, Wi-Fi rfkill, `ieee80211` wiphy entries, or a deployed
read-only `nl80211` helper result.

## Changes

- Added `scripts/revalidation/wifi_icnss_nl80211_probe.py`.
- Added optional static helper source:
  `stage3/linux_init/helpers/a90_nl80211_ro.c`.
- Built helper artifact:
  `stage3/linux_init/helpers/a90_nl80211_ro`.
- Added v205 plan:
  `docs/plans/NATIVE_INIT_V205_ICNSS_NL80211_READONLY_PLAN_2026-05-13.md`.
- Updated task queue and next-work notes.

## Static Validation

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_icnss_nl80211_probe.py \
  scripts/revalidation/android_twrp_wifi_baseline.py \
  scripts/revalidation/wifi_baseline_refresh.py \
  scripts/revalidation/a90harness/evidence.py
```

Result: PASS.

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import wifi_icnss_nl80211_probe
wifi_icnss_nl80211_probe.validate_no_active_wifi_commands()
print('v205 command guard PASS')
PY
```

Result: PASS.

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/helpers/a90_nl80211_ro \
  stage3/linux_init/helpers/a90_nl80211_ro.c
```

Result: PASS.

Helper artifact:

- file: `ELF 64-bit LSB executable, ARM aarch64, statically linked`
- SHA256:
  `fafa89f9c707d43f3d00f0c327d410f53b24569b858d9199770d0d163e3daf79`

## Device Validation

Preflight:

```bash
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py mountsystem ro
```

Result: PASS.

Collector run:

```bash
python3 scripts/revalidation/wifi_icnss_nl80211_probe.py \
  --native-bridge \
  --v203-manifest tmp/wifi/v203-baseline/manifest.json \
  --v204-android-manifest tmp/wifi/v204-android-baseline/manifest.json \
  --out-dir tmp/wifi/v205-icnss-nl80211-readonly
```

Result: PASS.

Evidence:

- `tmp/wifi/v205-icnss-nl80211-readonly/summary.md`
- `tmp/wifi/v205-icnss-nl80211-readonly/manifest.json`
- `tmp/wifi/v205-icnss-nl80211-readonly/native/commands/`

Hashes:

- `tmp/wifi/v205-icnss-nl80211-readonly/manifest.json`:
  `281910b9dfb67489025c69e03949a7df9050eb1683493e03788baa438c3d693b`
- `tmp/wifi/v205-icnss-nl80211-readonly/summary.md`:
  `c82fc22501cf2e41565a753a70ee327716b3ac75a5a5e791c2422a8193991f1f`

## Live Result

- Device build: `A90 Linux init 0.9.59 (v159)`
- v203 comparison: `no-go`
- v204 Android comparison: `ready-for-readonly-nl80211-probe-plan`
- v205 decision: `native-icnss-present-no-wiphy`
- `native_icnss`: `true`
- `native_wiphy`: `false`
- `native_wifi_rfkill`: `false`
- `native_interfaces`: none
- `nl80211` helper remote path: `/cache/bin/a90_nl80211_ro`
- `nl80211` helper remote state: missing on current v159 runtime

Important native evidence:

```text
/sys/devices/platform/soc/18800000.qcom,icnss
/sys/devices/platform/soc/18800000.qcom,icnss/wakeup
/sys/devices/platform/soc/18800000.qcom,icnss/iommu_group
/sys/devices/platform/soc/18800000.qcom,icnss/ramdump
/sys/devices/platform/soc/18800000.qcom,icnss/modalias
```

Missing native gates:

```text
/sys/class/net/wlan0
/sys/class/net/swlan0
/sys/class/net/p2p0
/sys/class/net/wifi-aware0
/sys/class/rfkill/rfkill1
/sys/class/ieee80211/phy0
/cache/bin/a90_nl80211_ro
```

Android v204 had those WLAN/ICNSS readiness signals, so the current difference is
not "hardware absent"; it is a native userspace/init/service dependency gap.

## Interpretation

The result is more specific than v203:

- v203 said native had no kernel-facing WLAN/rfkill/module gates.
- v204 Android proved Android can bring up ICNSS/WLAN interfaces and firmware.
- v205 proves native can at least see the ICNSS platform device, but does not
  yet trigger the Android-like WLAN netdev/wiphy/rfkill state.

Therefore active Wi-Fi bring-up remains blocked. The next useful work is not
`ip link set wlan0 up`; there is no `wlan0` in native. The next useful work is a
read-only dependency map for Android's ICNSS/CNSS daemon, firmware mount, QMI,
and service ordering path.

## Guardrails

- No Wi-Fi enablement.
- No rfkill write.
- No WLAN link-up.
- No scan/connect.
- No module load/unload.
- No firmware mutation.
- No Android Wi-Fi service, supplicant, hostapd, or cnss-daemon start.
- Optional `a90_nl80211_ro` helper is GET-only by design.

## Acceptance

- v205 evidence was captured into private/no-follow output.
- Native ICNSS sysfs state was recorded.
- Native WLAN netdev, Wi-Fi rfkill, and wiphy absence was recorded.
- v203 and v204 evidence were compared.
- Active Wi-Fi enablement remains blocked.

## Next

Recommended v206 scope: Android ICNSS/CNSS dependency map. Collect read-only
Android init rc/service ordering, `cnss-daemon` properties, firmware mount paths,
and native missing prerequisites. The goal is to answer what Android does before
the WLAN netdevs appear, still without starting Wi-Fi from native init.

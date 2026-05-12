# v205 Plan: ICNSS/WCNSS/QCA + nl80211 Read-Only Probe

## Summary

v205 follows the v204 Android/Magisk evidence result:
`ready-for-readonly-nl80211-probe-plan`.

The goal is not to enable Wi-Fi. The goal is to compare Android's working WLAN
state with native init's current state using read-only ICNSS, firmware, rfkill,
netdev, wiphy, and `nl80211` probes.

Target output is a host-side private evidence bundle and a clear decision:

- whether native init can see an ICNSS platform device;
- whether native init can see a WLAN netdev, Wi-Fi rfkill, or wiphy;
- whether read-only `nl80211` GET operations can return data;
- whether firmware paths visible in Android are visible from native init;
- whether active bring-up must remain blocked.

## Current Evidence

v203 native baseline:

- Result: PASS, final decision: `no-go`
- Native default state:
  - no `wlan*` netdev;
  - no Wi-Fi rfkill;
  - no WLAN/CNSS/QCA module evidence;
  - Android-side file candidates existed, but kernel-facing gates were missing.

v204 TWRP baseline:

- Result: PASS, decision: `driver-candidate-found`
- TWRP exposed ICNSS/WLAN kernel log hints and firmware search path.
- TWRP still did not expose WLAN interface, Wi-Fi rfkill, or loaded WLAN module.

v204 Android + Magisk baseline:

- Result: PASS, decision: `ready-for-readonly-nl80211-probe-plan`
- Android exposed:
  - `wlan0`, `swlan0`, `p2p0`, `wifi-aware0`;
  - ICNSS-backed netdev paths under
    `/sys/devices/platform/soc/18800000.qcom,icnss`;
  - Wi-Fi rfkill under `ieee80211/phy0/rfkill1`;
  - vendor firmware/HAL/init service assets;
  - root-readable ICNSS/WLAN dmesg readiness.

## References

- Linux `cfg80211` is the kernel configuration API used by modern 802.11
  drivers and userspace Wi-Fi tooling:
  <https://docs.kernel.org/driver-api/80211/cfg80211.html>
- Linux `nl80211` netlink spec includes read-oriented operations such as
  `get-wiphy`, `get-interface`, and `get-protocol-features`:
  <https://www.kernel.org/doc/html/latest/networking/netlink_spec/nl80211.html>
- Linux firmware loading uses built-in paths plus `firmware_class.path=` and
  `/sys/module/firmware_class/parameters/path`:
  <https://www.kernel.org/doc/html/v6.15/driver-api/firmware/fw_search_path.html>
- Android Wi-Fi architecture routes framework requests through Wi-Fi services,
  `wificond`, Wi-Fi HAL, supplicant/hostapd, and kernel driver paths:
  <https://source.android.com/docs/core/connect/wifi-overview>
- Android Wi-Fi HAL components split framework/HAL/supplicant/hostapd surfaces:
  <https://source.android.com/docs/core/connect/wifi-hal>
- Qualcomm ICNSS documentation describes WLAN firmware/QMI control around the
  CNSS/ICNSS platform driver:
  <https://android.googlesource.com/kernel/msm/+/android-7.1.0_r0.2/Documentation/devicetree/bindings/cnss/icnss.txt>

## Goals

- Add a v205 read-only probe plan and implementation target.
- Collect native init ICNSS/sysfs/netdev/rfkill/firmware state.
- Add a read-only `nl80211` probe path that only performs GET operations.
- Compare native v205 evidence against v204 Android evidence.
- Produce one of the v205 decisions without mutating Wi-Fi state.

## Non-Goals

- Do not enable Wi-Fi.
- Do not run `svc wifi enable`, `cmd wifi set-wifi-enabled`, or Android Wi-Fi
  service start/stop commands.
- Do not write rfkill state.
- Do not run `ip link set wlan0 up`.
- Do not run active scan commands.
- Do not send `NL80211_CMD_TRIGGER_SCAN`, `NL80211_CMD_SET_INTERFACE`,
  `NL80211_CMD_SET_WIPHY`, or similar mutating commands.
- Do not load or unload modules.
- Do not mount debugfs if it is not already mounted.
- Do not mutate firmware paths or copy firmware into new live locations.
- Do not collect `/data/misc/wifi`, saved networks, PSKs, tokens, or account
  material.

## Proposed Artifacts

- Plan:
  `docs/plans/NATIVE_INIT_V205_ICNSS_NL80211_READONLY_PLAN_2026-05-13.md`
- Host collector:
  `scripts/revalidation/wifi_icnss_nl80211_probe.py`
- Optional device helper:
  `stage3/linux_init/helpers/a90_nl80211_ro.c`
- Output:
  `tmp/wifi/v205-icnss-nl80211-readonly/`
- Report:
  `docs/reports/NATIVE_INIT_V205_ICNSS_NL80211_READONLY_2026-05-13.md`

The helper should be built and copied to `/cache/bin/a90_nl80211_ro` only if the
host environment cannot obtain the needed `nl80211` data through existing native
tools. The helper must hard-code a read-only allowlist.

## Probe Design

### Native sysfs and proc collection

Collect these paths through the existing native bridge or broker:

```text
/proc/cmdline
/proc/modules
/sys/class/net
/sys/class/rfkill
/sys/class/ieee80211
/sys/module/firmware_class/parameters/path
/sys/devices/platform/soc/18800000.qcom,icnss
/mnt/system/vendor/firmware
/mnt/system/vendor/firmware_mnt
/mnt/system/vendor/etc/wifi
/mnt/system/vendor/etc/init
/mnt/system/vendor/etc/vintf
```

Rules:

- list directories and read ordinary text attributes only;
- skip write-only and binary-looking nodes;
- redact MAC-like values;
- treat missing paths as evidence, not as errors;
- do not mount extra filesystems as part of this probe.

### Android evidence comparison

Use v204 Android evidence as the comparison anchor:

```text
tmp/wifi/v204-android-baseline/manifest.json
tmp/wifi/v204-android-baseline/root-dmesg-wifi-tail.txt
tmp/wifi/v204-android-baseline/root-icnss-sysfs-files.txt
```

Expected Android anchors:

```text
wlan0
swlan0
p2p0
wifi-aware0
/sys/devices/platform/soc/18800000.qcom,icnss
ieee80211/phy0/rfkill1
WLAN FW is ready
HostSW: 5.2.022.3Q-HL210630A
HW: WCN39xx
```

### Read-only nl80211 probe

Allowed operations:

```text
NL80211_CMD_GET_PROTOCOL_FEATURES
NL80211_CMD_GET_WIPHY
NL80211_CMD_GET_INTERFACE
```

Allowed style:

- dump/read only;
- no scan trigger;
- no link-up;
- no interface type change;
- no regulatory change;
- no rfkill write.

If `nl80211` generic netlink family is missing, record:

```text
nl80211=missing
decision=no-native-wiphy
```

If the family exists but returns no wiphy/interface, record the exact errno and
message in the bundle.

## Decision Model

The v205 report must emit one final decision:

- `no-native-icnss`
  - Native init cannot see ICNSS sysfs, Wi-Fi rfkill, wiphy, or WLAN netdev.
  - Active Wi-Fi remains blocked.
- `native-icnss-present-no-wiphy`
  - Native init sees ICNSS or firmware hints, but no wiphy/WLAN netdev.
  - Next step should investigate vendor daemon/QMI/init dependency mapping.
- `native-wiphy-readonly-ok`
  - Native init can read wiphy/interface data through read-only `nl80211`.
  - Next step may plan passive status diagnostics, still not active association.
- `android-only-driver-ready`
  - Android has full ICNSS/WLAN readiness, native does not.
  - Next step should map Android services and firmware/QMI prerequisites.
- `manual-review-required`
  - Evidence conflicts or collector permissions are insufficient.

No v205 decision may approve active Wi-Fi enablement.

## Guardrails

The collector and optional helper must reject these patterns:

```text
rfkill unblock
ip link set .* up
iw .* scan
iw .* connect
NL80211_CMD_TRIGGER_SCAN
NL80211_CMD_SET_INTERFACE
NL80211_CMD_SET_WIPHY
insmod
rmmod
modprobe
svc wifi
cmd wifi set-wifi-enabled
wpa_supplicant
hostapd
cnss-daemon start
```

Read-only path searches may mention binary names as filenames, but must not
execute those binaries.

## Validation

Static validation:

```bash
git diff --check

python3 -m py_compile \
  scripts/revalidation/wifi_icnss_nl80211_probe.py \
  scripts/revalidation/android_twrp_wifi_baseline.py \
  scripts/revalidation/wifi_baseline_refresh.py \
  scripts/revalidation/a90harness/evidence.py
```

Native bridge validation:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py 'mountsystem ro'
python3 scripts/revalidation/wifi_icnss_nl80211_probe.py \
  --native-bridge \
  --v203-manifest tmp/wifi/v203-baseline/manifest.json \
  --v204-android-manifest tmp/wifi/v204-android-baseline/manifest.json \
  --out-dir tmp/wifi/v205-icnss-nl80211-readonly
```

Optional helper validation:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/helpers/a90_nl80211_ro \
  stage3/linux_init/helpers/a90_nl80211_ro.c

python3 scripts/revalidation/a90ctl.py 'run /cache/bin/a90_nl80211_ro'
```

The optional helper is acceptable only if it performs the allowed GET operations
and exits without changing link, rfkill, scan, service, module, or firmware
state.

## Acceptance

- v205 evidence is captured into private/no-follow output.
- Native ICNSS/sysfs/netdev/rfkill/firmware state is recorded.
- `nl80211` family/wiphy/interface state is recorded or explicitly missing.
- v204 Android WLAN anchors are compared against native state.
- Active Wi-Fi enablement remains blocked unless a later, separate plan changes
  the policy.
- The report recommends the next step based on the decision model above.

## Next

If v205 returns `native-wiphy-readonly-ok`, plan a later passive diagnostics
step. If v205 returns `android-only-driver-ready` or
`native-icnss-present-no-wiphy`, plan a vendor daemon/QMI/firmware dependency
map before any bring-up attempt.

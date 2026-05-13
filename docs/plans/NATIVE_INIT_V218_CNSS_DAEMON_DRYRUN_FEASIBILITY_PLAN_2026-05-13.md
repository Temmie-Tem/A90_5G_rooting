# v218 Plan: CNSS Daemon Dry-Run Feasibility

## Summary

v218 follows v217 `state-only-inventory`. The goal is to determine whether
`cnss-daemon` and `cnss_diag` could be prepared for a later native experiment
without executing either binary.

This version is read-only or manifest-only by default. It must not start
`cnss-daemon`, `cnss_diag`, Wi-Fi HAL, `wificond`, supplicant, hostapd, rfkill,
link-up, scan, or connect.

- baseline native runtime: `A90 Linux init 0.9.59 (v159)`
- previous result: v217 PASS, `state-only-inventory`
- planned modeler: `scripts/revalidation/wifi_cnss_daemon_dryrun.py`
- evidence input:
  - `tmp/wifi/v216-service-replay-model/manifest.json`
  - `tmp/wifi/v217-icnss-debug-recovery-inventory/manifest.json`
  - `tmp/wifi/v217-icnss-debug-recovery-inventory-native/manifest.json`
  - `tmp/wifi/v210-vendor-asset-classifier/manifest.json`
- evidence output: `tmp/wifi/v218-cnss-daemon-dryrun`
- report after execution:
  `docs/reports/NATIVE_INIT_V218_CNSS_DAEMON_DRYRUN_FEASIBILITY_2026-05-13.md`

## Reference Notes

- Android init service definitions provide the service executable, user/group,
  capabilities, sockets, classes, and property triggers. v218 must model these
  fields instead of replacing Android init with a blind `execve`:
  <https://chromium.googlesource.com/aosp/platform/system/core/+/master/init/README.md>
- `cnss-daemon` is part of the Qualcomm ICNSS/CNSS userspace lifecycle, while
  the kernel side exposes QMI, PDR/SSR, ramdump, firmware service, and debugfs
  surfaces. v218 can inspect dependencies but must not drive the lifecycle:
  <https://android.googlesource.com/kernel/msm/+/289f176f9259d8f663478a246542cf6be4ed3d24/drivers/soc/qcom/icnss.c>
- The Linux ELF interpreter and dynamic linker requirements must be resolved
  before native execution. Host-side `readelf`/`objdump` parsing is acceptable;
  device execution is not:
  <https://man7.org/linux/man-pages/man5/elf.5.html>
- v217 found state evidence but no safe active recovery control. That means a
  later service experiment must treat reboot as the only proven recovery path.

## Current Evidence Chain

- v216 service graph:
  - `cnss-daemon`: `/system/vendor/bin/cnss-daemon`, groups
    `system inet net_admin wifi`, capability `NET_ADMIN`
  - `cnss_diag`: `/system/vendor/bin/cnss_diag`
- v217:
  - ICNSS state/debug/ramdump surfaces are visible
  - dangerous controls include ICNSS `bind`, `unbind`, and `driver_override`
  - reboot is still the only proven recovery from broken ICNSS state
- v210:
  - vendor Wi-Fi/CNSS binaries, init rc files, firmware assets, and VINTF
    evidence are visible through the temporary vendor read-only model

## Scope

Allowed:

- parse v210/v216/v217 manifests and summaries
- inspect host-side copied/captured init rc, service graph, and asset maps
- run host-side `readelf`, `objdump`, `file`, or equivalent on copied evidence
  only if the binary is locally available
- produce dependency and blocker reports
- optionally run native bridge read-only commands for file existence/stat only
- write host-only private evidence bundles

Forbidden:

- executing `cnss-daemon` or `cnss_diag`
- executing Wi-Fi HAL, `wificond`, `wpa_supplicant`, or `hostapd`
- `ctl.start`, `ctl.restart`, `class_start`, or Android property mutation
- ICNSS `bind`/`unbind`, `driver_override`, or debugfs/sysfs writes
- firmware path mutation
- vendor/system mount mutation in v218 default mode
- rfkill writes
- link-up
- Wi-Fi scan/connect
- credential collection from `/data/misc/wifi`

## Modeler Design

Add `scripts/revalidation/wifi_cnss_daemon_dryrun.py`.

Default behavior:

- manifest-only
- no live device command
- no mount or copy operation
- active-command guard must reject daemon execution and sysfs writes

Optional native read-only mode:

- `stat` expected binary paths only
- `cat /proc/mounts`
- `cat /sys/module/firmware_class/parameters/path`
- no execution, no mount, no path mutation

First-class targets:

- `cnss-daemon`
- `cnss_diag`

For each target, classify:

- executable path and native visibility
- alias requirement: `/system/vendor/...` versus `/vendor/...`
- ELF interpreter requirement
- direct shared library names
- config file candidates
- device node/sysfs dependency hints
- required users/groups/capabilities
- Android property/service assumptions
- sockets or binder/HIDL/VINTF assumptions
- ICNSS recovery risk inherited from v217

## Output Model

The modeler should write:

- `manifest.json`
- `daemon-dependencies.json`
- `summary.md`

Each daemon entry should include:

- name
- executable
- native path status
- source service model
- required users/groups/capabilities
- direct library requirements
- unresolved paths
- Android runtime assumptions
- blockers
- risk class

## Decision Model

- `daemon-dryrun-ready`
  - executable, direct dependencies, mount aliases, and runtime assumptions are
    mapped well enough for v219 shim planning.
- `daemon-dryrun-partial`
  - service metadata is mapped, but local ELF/library evidence is incomplete.
- `daemon-native-blocked`
  - required Android runtime, property, binder/HIDL, SELinux, or recovery
    assumptions are too broad for near-term native execution.
- `insufficient-evidence`
  - required v210/v216/v217 evidence is missing or inconsistent.
- `manual-review-required`
  - evidence conflicts or the modeler finds a risky assumption.

## Validation

Static:

```sh
python3 -m py_compile scripts/revalidation/wifi_cnss_daemon_dryrun.py
git diff --check
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import wifi_cnss_daemon_dryrun
wifi_cnss_daemon_dryrun.validate_no_active_commands()
print('v218 command guard PASS')
PY
```

Manifest-only:

```sh
python3 scripts/revalidation/wifi_cnss_daemon_dryrun.py \
  --v210-manifest tmp/wifi/v210-vendor-asset-classifier/manifest.json \
  --v216-manifest tmp/wifi/v216-service-replay-model/manifest.json \
  --v217-manifest tmp/wifi/v217-icnss-debug-recovery-inventory/manifest.json \
  --v217-native-manifest tmp/wifi/v217-icnss-debug-recovery-inventory-native/manifest.json \
  --out-dir tmp/wifi/v218-cnss-daemon-dryrun
```

Optional native read-only:

```sh
python3 scripts/revalidation/wifi_cnss_daemon_dryrun.py \
  --native-bridge \
  --out-dir tmp/wifi/v218-cnss-daemon-dryrun-native
```

## Acceptance

- No command list contains daemon execution, service start, ICNSS sysfs/debugfs
  writes, rfkill writes, link-up, scan, or connect.
- Manifest-only mode works from existing v210/v216/v217 evidence.
- The model names every unresolved dependency explicitly.
- The summary states whether v219 can design a minimal native Android-env shim.
- If the result is `daemon-native-blocked`, v219 must pause shim work and
  either gather more Android evidence or keep Wi-Fi active bring-up blocked.

## Next Step

If v218 returns `daemon-dryrun-ready` or `daemon-dryrun-partial`, v219 should
design the minimal native Android-env shim. If v218 returns
`daemon-native-blocked`, keep Wi-Fi bring-up blocked and reassess whether a
larger Android compatibility layer is out of scope for this project.

# Native Init V1161 Late pm-proxy Helper Build Report

Date: `2026-05-27`

## Result

- Decision: `v1161-late-per-proxy-helper-build-pass`
- Pass: `true`
- Helper: `a90_android_execns_probe v216`
- Build gate: `scripts/revalidation/native_wifi_late_per_proxy_helper_build_v1161.py`
- Evidence: `tmp/wifi/v1161-execns-helper-v216-build/manifest.json`
- Summary: `tmp/wifi/v1161-execns-helper-v216-build/summary.md`
- SHA256: `b9518555ef53f8e721f8a057c8145085b3ba91899c34609c59cb1885e8b71241`
- Size: `1253872`

## Summary

V1161 implements the V1160 conclusion in the static execns helper.  The PM
observer can now defer `pm-proxy` while the upper PM/CNSS path starts, confirm
that `mdm_helper` is alive with `/dev/esoc-0`, then start `pm-proxy` late as
the bounded eSoC trigger candidate.

The new path remains below Wi-Fi bring-up:

- Wi-Fi HAL start: disabled
- scan/connect/link-up: disabled
- credentials: disabled
- DHCP/routes: disabled
- external ping: disabled
- boot image writes: not part of this unit

## Helper Changes

- Bumped `stage3/linux_init/helpers/a90_android_execns_probe.c` to `a90_android_execns_probe v216`.
- Added `--pm-observer-start-per-proxy-after-mdm-helper-esoc-fd`.
- Requires `wifi-companion-post-pm-mdm-helper-esoc-observer`,
  `--allow-post-pm-mdm-helper-esoc-observer`,
  `--pm-observer-start-mdm-helper-after-cnss`, and
  `--pm-observer-start-cnss-before-per-proxy`.
- Keeps the initial `per_proxy` slot deferred instead of treating it as a final
  skip.
- Starts `pm-proxy` only when `mdm_helper` is observable and has a positive
  `/dev/esoc-0` fd count.
- Captures six 500 ms `late_per_proxy_poll_%02d` windows after late start.
- Extends PM observer fd snapshots with `per_mgr_subsys_esoc0_count`.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_late_per_proxy_helper_build_v1161.py
git diff --check
python3 scripts/revalidation/native_wifi_late_per_proxy_helper_build_v1161.py run
```

Result:

```text
decision: v1161-late-per-proxy-helper-build-pass
pass: True
reason: helper v216 built sha256=b9518555ef53f8e721f8a057c8145085b3ba91899c34609c59cb1885e8b71241
```

The build output is a static AArch64 binary with no `INTERP` segment and no
dynamic section.

## Safety

- Source/build-only unit; no device command executed.
- No deploy, PM actor, `cnss-daemon`, `mdm_helper`, Wi-Fi HAL, scan/connect,
  credential use, DHCP, route, external ping, partition write, flash, or reboot
  executed.
- Secret scan over the touched helper/build files found no Wi-Fi credentials.

## Next Gate

V1162 should deploy helper `v216`.  V1163 should run the bounded live gate and
classify whether late `pm-proxy` causes `pm-service` to enter `/dev/subsys_esoc0`
or the lower MHI/`ks`/WLFW/service69 path.

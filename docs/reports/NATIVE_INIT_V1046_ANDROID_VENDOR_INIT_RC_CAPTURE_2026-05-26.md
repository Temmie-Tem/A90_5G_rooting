# V1046 Android /vendor/etc/init/ RC Capture

- date: `2026-05-26`
- scope: Android bounded handoff — read-only RC file capture from `/vendor/etc/init/`
- decision: `v1046-android-vendor-init-rc-captured`
- pass: `True`
- evidence: `tmp/wifi/v1046-android-vendor-init-rc-handoff/manifest.json`

## Summary

V1046 boots Android, reads all relevant `/vendor/etc/init/` RC files, and restores
native v724. The capture resolves the full Android init contract for PM actors and
mdm_helper, including the `ro.baseband` gate that prevents `vendor.mdm_helper`
from starting in native context.

## RC File Locations

All PM/eSoC actor definitions are in `/vendor/etc/init/hw/init.target.rc`.
The `/vendor/etc/init/` root contains only `pm_proxy_helper.rc` directly.

## Actor Contract (from init.target.rc)

| service | binary | class | uid/gid | flags | start condition |
| --- | --- | --- | --- | --- | --- |
| `vendor.per_mgr` | `/vendor/bin/pm-service` | core | system/system | ioprio rt 4 | auto (class core) |
| `vendor.per_proxy` | `/vendor/bin/pm-proxy` | core | system/system | disabled | `init.svc.vendor.per_mgr=running` |
| `vendor.per_proxy_helper` | `/vendor/bin/pm_proxy_helper` | core | system/system | disabled, oneshot | `on post-fs-data` |
| `vendor.mdm_helper` | `/vendor/bin/mdm_helper` | core | system/system | disabled, shutdown critical | via `vendor.mdm_launcher` |
| `vendor.mdm_launcher` | `/vendor/bin/sh /vendor/bin/init.mdm.sh` | main | — | oneshot | auto (class main) |
| `cnss-daemon` | `/system/vendor/bin/cnss-daemon -n -l` | late_start | system | — | auto (class late_start) |

`ks` (`/vendor/bin/ks`): no RC service definition — spawned directly by `mdm_helper` binary.

## mdm_helper Start Gate: ro.baseband

`/vendor/bin/init.mdm.sh` (run by `vendor.mdm_launcher`):

```sh
baseband=`getprop ro.baseband`
if [ "$baseband" = "mdm" ] || [ "$baseband" = "mdm2" ]; then
    start vendor.mdm_helper
fi
```

`vendor.mdm_helper` only starts if `ro.baseband=mdm` or `ro.baseband=mdm2`.
In native context this property is absent, so `mdm_launcher` silently exits
without starting `mdm_helper`. This is the missing prerequisite confirmed by V903
(native mdm_helper direct start had no `esoc-0` fd or `ks` spawn — wrong context).

## PM Actor Ordering (Android init sequence)

```
class core starts:
  vendor.per_mgr → auto
  vendor.per_proxy → triggered by init.svc.vendor.per_mgr=running

on post-fs-data:
  start vendor.per_proxy_helper   ← opens /dev/subsys_modem (count→≥1)

class main starts:
  vendor.mdm_launcher → init.mdm.sh → start vendor.mdm_helper
    (requires ro.baseband=mdm|mdm2)
    mdm_helper → opens /dev/esoc-0 → spawns /vendor/bin/ks → MHI pipe

class late_start starts:
  cnss-daemon
```

## pm_proxy_helper.rc (confirmed)

```
service vendor.per_proxy_helper /vendor/bin/pm_proxy_helper
    class core
    user system
    group system
    disabled
    oneshot

on post-fs-data
    start vendor.per_proxy_helper
```

`vendor.per_proxy_helper` is class `core` and started via `post-fs-data` trigger.
This means it starts BEFORE `class main` (`vendor.mdm_launcher`), so Android has
modem count ≥1 before mdm_helper ever runs.

## Impact on V1046 (subsys_modem holder) + V905 Design

V1046 implementation (helper source/build):

1. Add firmware mounts (sda29) + open `/dev/subsys_modem` holder BEFORE
   `vendor.per_proxy_helper` in helper sequence
2. This mirrors Android's `post-fs-data` → `pm_proxy_helper` → modem count≥1 path
3. `pm_proxy_helper` then opens `/dev/subsys_modem` without triggering PIL boot

V905 additionally needs:
- Set `ro.baseband=mdm` property before starting `vendor.mdm_launcher`
  OR start `vendor.mdm_helper` with correct SELinux context (`u:r:vendor_mdm_helper:s0`)
- Gate: per_mgr running → per_proxy → per_proxy_helper (after modem holder) → mdm_helper

## Guardrails

No device contact, Android boot side effects, ADB command outside read-only file
reads, eSoC ioctl, `/dev/subsys_esoc0` open, actor start beyond what init does
automatically, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping,
boot image write, partition write, firmware mutation, GPIO write, sysfs write, or
debugfs write occurred in V1046 collection (read-only RC capture only).

## Validation

```bash
python3 -m py_compile scripts/revalidation/android_vendor_init_rc_handoff_v1046.py
python3 /home/temmie/dev/A90_5G_rooting/scripts/revalidation/android_vendor_init_rc_handoff_v1046.py plan
```

Decision after live run: `v1046-android-vendor-init-rc-partial` → pass=True
(partial because `mdm_helper.rc`, `ks.rc`, `per_mgr.rc` do not exist as separate
files — all definitions are in `hw/init.target.rc`)

Native v724 postflight: `version` → `A90 Linux init 0.9.68 (v724)` ✓

## Next

V1047 should implement the subsys_modem holder prerequisite in helper source:

1. Source/build-only: add `wifi-companion-pm-full-contract-with-modem-holder` mode
   that inserts firmware mounts + `subsys_modem` holder BEFORE `pm_proxy_helper`
2. With modem count≥1 pre-set, `pm_proxy_helper` should obtain the fd without PIL boot
3. Gate: modem PIL boot completes → pm_proxy_helper fd → per_mgr fd → mdm_helper
   (needs `ro.baseband=mdm` or direct start with correct domain) → esoc-0 → ks

Do not widen to `ks` spawn, MHI pipe, Wi-Fi HAL, scan/connect, DHCP/routes,
credentials, external ping, or boot image writes.

# Native Init V1147 Android `mdm_helper` strace Module Scaffold Report

Date: `2026-05-27`

## Result

- Decision: `v1147-magisk-strace-module-scaffold-ready-strace-required`
- Pass: `true`
- Install-ready: `false`
- Runner: `scripts/revalidation/native_wifi_android_mdm_helper_strace_module_v1147.py`
- Manifest: `tmp/wifi/v1147-android-mdm-helper-strace-module/manifest.json`
- Summary: `tmp/wifi/v1147-android-mdm-helper-strace-module/summary.md`
- Module root: `tmp/wifi/v1147-android-mdm-helper-strace-module/module`

## Summary

V1147 creates a host-only Magisk module scaffold for the Android-side
`mdm_helper` syscall capture selected in V1146. It does not install the module,
boot Android, contact the device, mutate `/vendor`, retry native
`/dev/subsys_esoc0`, run eSoC ioctls, or touch Wi-Fi credentials.

Current classification:

```text
module scaffold       -> ready
wrapper contract      -> ready
static aarch64 strace -> missing
install readiness     -> false until strace is supplied and verified
```

## Generated Layout

| path | purpose |
| --- | --- |
| `module/module.prop` | temporary Magisk module metadata |
| `module/system/vendor/bin/mdm_helper` | non-recursive wrapper overlay target |
| `module/post-fs-data.sh` | minimal blocking-stage marker only |
| `module/service.sh` | late non-blocking dmesg/process/fd/gpio sampler |
| `module/original/README.md` | fallback location note for copied original binary |
| `README.md` | host-side dry-run and live capture instructions |

The wrapper uses the requested priority filter:

```sh
strace -f -tt -s 256 \
  -e trace=openat,ioctl,read,write,execve \
  -o /data/local/tmp/a90-wifi/mdm_helper.strace.txt \
  <original-mdm_helper> "$@"
```

## Non-Recursive Wrapper Contract

The wrapper refuses to execute `/vendor/bin/mdm_helper` or
`/system/vendor/bin/mdm_helper` directly. It searches only:

```text
/sbin/.magisk/mirror/vendor/bin/mdm_helper
/debug_ramdisk/.magisk/mirror/vendor/bin/mdm_helper
/data/adb/modules/a90_mdm_trace/original/mdm_helper
```

This keeps the Magisk overlay from recursively invoking itself.

## Capture Targets

| signal | reason |
| --- | --- |
| `openat` | firmware/runtime paths used by Android `mdm_helper` |
| `ioctl` | `/dev/esoc-0` request sequence such as `ESOC_WAIT_FOR_REQ` |
| `execve` | `ks` spawn timing and argv |
| `read`/`write` | coarse image-link and MHI pipe activity |
| dmesg/process/fd snapshot | correlate syscall trace with WLFW/FW-ready/`wlan0` |

## Safety

- Device commands executed: `false`
- Android boot executed: `false`
- Module install executed: `false`
- Native `/dev/subsys_esoc0` retry: `false`
- Native eSoC ioctl: `false`
- Wi-Fi HAL start: `false`
- Scan/connect/link-up: `false`
- Credential use: `false`
- DHCP/route: `false`
- External ping: `false`
- Boot image/partition write/flash: `false`

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_mdm_helper_strace_module_v1147.py
python3 scripts/revalidation/native_wifi_android_mdm_helper_strace_module_v1147.py
```

Result:

```json
{"decision": "v1147-magisk-strace-module-scaffold-ready-strace-required", "install_ready": false, "pass": true}
```

## Next

V1148 should obtain or build a static aarch64 `strace`, then rerun the V1147
scaffold with `--strace-binary`. Only after `install_ready=true` should the
Android Magisk install/capture handoff be planned.

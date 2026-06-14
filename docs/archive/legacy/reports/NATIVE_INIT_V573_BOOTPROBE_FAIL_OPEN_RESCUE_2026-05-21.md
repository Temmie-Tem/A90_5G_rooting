# Native Init V573 Bootprobe Fail-Open Rescue Report

Date: `2026-05-21`

## Goal

Build a safer rescue successor to V572 after the first opt-in bootprobe attempt
blocked before USB ACM returned.

## Result

- Decision: `v573-bootprobe-fail-open-local-build-pass`
- Pass: `True`
- Native build artifact: `A90 Linux init 0.9.63 (v573)`
- Boot image: `stage3/boot_linux_v573.img`
- Device flash: not executed yet because the device is not currently visible on
  USB after the V572 opt-in attempt
- Daemon start: not executed by V573 locally
- Wi-Fi bring-up: not executed

## Why V573 Exists

V572 disabled-flag flash was clean, but creating
`/cache/native-init-wifi-bootprobe` and rebooting left the device unavailable to
host USB:

```text
adb devices: empty
/dev/ttyACM*: absent
lsusb: no Samsung/ACM device
a90ctl version: A90P1 END marker not found before timeout
```

Because V572 starts the opt-in bootprobe before ACM gadget setup, a blocking
precondition or cleanup path can prevent host recovery until physical TWRP
entry.

## Changes

- Bumped native metadata to `0.9.63 (v573)`.
- Added `WIFI_BOOTPROBE_RUN_FLAG_PATH`:
  `/cache/native-init-wifi-bootprobe-run`.
- Made `/cache/native-init-wifi-bootprobe` one-shot: it is consumed at boot.
- Changed V573 so the existing one-shot flag only arms the probe; helper
  execution requires the second run flag.
- Removed automatic SELinuxfs mount from the early bootprobe path. If
  `/sys/fs/selinux/status` is absent, the hook classifies and skips instead of
  mounting inside the pre-ACM path.
- Hardened `a90_run_stop_pid_ex()` so timeout cleanup does not block PID1
  forever on `waitpid(pid, 0)` after SIGKILL.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v573` | `97680c70f754256a9faa711ef389d66608e7f1722d4fd36a74f21c8cd100fa92` |
| `stage3/ramdisk_v573.cpio` | `b07b35fd1553206a6bb48cf629217631524814d98c86fa1f3ebe044001ccdab5` |
| `stage3/boot_linux_v573.img` | `c819e8a5670acb13023fe7b30c706ef944b8e1f85d03d6d61025e62fdaddf962` |

## Static Validation

```text
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra ...
aarch64-linux-gnu-strip stage3/linux_init/init_v573
sha256sum stage3/linux_init/init_v573 stage3/ramdisk_v573.cpio stage3/boot_linux_v573.img
strings stage3/boot_linux_v573.img | rg 'A90 Linux init 0\.9\.63 \(v573\)|A90v573|native-init-wifi-bootprobe|native-init-wifi-bootprobe-run|wifi-bootprobe-v573|SIGKILL wait timeout'
```

Result: PASS.

## Recovery Use

When the device is manually placed into TWRP/recovery, flash either:

1. known-good rollback `stage3/boot_linux_v319.img`, then remove
   `/cache/native-init-wifi-bootprobe`; or
2. safer V573 `stage3/boot_linux_v573.img`, which consumes the existing
   one-shot flag and should return to native serial without running the helper
   because `/cache/native-init-wifi-bootprobe-run` is absent.

Preferred immediate recovery is V573 because it preserves the latest fail-open
fix while neutralizing the stale V572 flag.

## Next Gate

After TWRP is available:

```text
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v573.img \
  --expect-version "A90 Linux init 0.9.63 (v573)" \
  --verify-protocol auto
```

Then verify:

- `version`
- `status`
- `selftest`
- `timeline`
- native log line for `wifi-bootprobe armed-only`
- `/cache/native-init-wifi-bootprobe` absent
- `/cache/native-init-wifi-bootprobe-run` absent

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.


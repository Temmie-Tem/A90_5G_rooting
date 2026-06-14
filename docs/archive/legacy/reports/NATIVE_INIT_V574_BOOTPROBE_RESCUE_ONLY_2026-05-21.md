# Native Init V574 Bootprobe Rescue-only Build

Date: 2026-05-21

## Scope

V574 is a conservative recovery image after the V572 opt-in boot-time Wi-Fi
bootprobe blocked before USB ACM/ADB returned.

The goal is not to advance Wi-Fi bring-up. The goal is to restore a safe native
init control surface even if stale bootprobe flags remain in `/cache`.

## Changes

- Version: `A90 Linux init 0.9.64 (v574)`.
- Boot image: `stage3/boot_linux_v574.img`.
- Keeps V573 `a90_run_stop_pid_ex()` bounded post-SIGKILL wait hardening.
- Consumes `/cache/native-init-wifi-bootprobe` when present.
- Consumes `/cache/native-init-wifi-bootprobe-run` when present.
- Never starts `/cache/bin/a90_android_execns_probe` from PID1.
- Never prepares Android layout or SELinuxfs from the early pre-ACM hook.

## Safety Boundary

V574 intentionally does not perform any live Wi-Fi action:

- no companion helper start;
- no `cnss-daemon`, `cnss_diag`, `rmt_storage`, `tftp_server`, `pd-mapper`, or
  service-manager start;
- no Wi-Fi HAL start;
- no scan/connect/link-up;
- no DHCP/routes/external ping.

## Artifacts

| Artifact | SHA256 |
| --- | --- |
| `stage3/linux_init/init_v574` | `0df694d3884183bd6c840588f39ef07c360a90feb48bdb2ea4dacd5b22092213` |
| `stage3/ramdisk_v574.cpio` | `ce2077272e87fa5ec7602c09f7a03b3a7a6b7fd8656ab2c197c9c7629b0e1033` |
| `stage3/boot_linux_v574.img` | `718c205c1816505a5fafe94d0b31514222bf0a72a82d69e966545221b4e595e9` |

## Static Validation

```text
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra ... -o stage3/linux_init/init_v574
stage3/linux_init/init_v574: ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped
strings stage3/boot_linux_v574.img | grep -E 'A90 Linux init 0\.9\.64 \(v574\)|A90v574|wifi-bootprobe-v574|native-init-wifi-bootprobe-run|SIGKILL wait timeout'
```

Result: PASS.

## Recovery Use

When the device is manually placed into TWRP/recovery, flash V574 first:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v574.img \
  --expect-version "A90 Linux init 0.9.64 (v574)" \
  --verify-protocol auto
```

Rollback fallback remains:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v319.img \
  --expect-version "A90 Linux init 0.9.61 (v319)" \
  --verify-protocol auto
```

## Live Status

Host state at report creation:

```text
adb devices: no device
/dev/ttyACM*: absent
Samsung/Android USB: absent
```

V574 has not been flashed yet. `tmp/wait-flash-v574.sh` is the active recovery
waiter and will flash only when exactly one ADB recovery device is visible.

## Next Gate

After V574 boots and native serial is verified, resume the Wi-Fi path from the
last proven blocker: native lacks Android-boot QRTR/modem readiness markers before
companion/HAL start. Do not retry early bootprobe execution from PID1 until the
pre-ACM block has a stronger timeout/isolation design.

## Recovery Superseded by V319

The device screen showed `0.9.62 v572`, confirming that V574 had not been flashed.
Because the device was in a repeated reboot loop, recovery priority changed from
trying a new V574 image to rolling back to the last live-validated V319 image.

The V319 rollback completed successfully through TWRP/recovery:

```text
boot block prefix sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
cmdv1 verify passed: version/status rc=0 status=ok
A90 Linux init 0.9.61 (v319)
```

V574 remains a local artifact only and has not been live-flashed. Do not treat it
as validated.

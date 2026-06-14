# Native Init v99 BusyBox Userland Report

Date: `2026-05-03`

## Summary

- Version: `A90 Linux init 0.8.30 (v99)`
- Marker: `0.8.30 v99 BUSYBOX USERLAND`
- Goal: evaluate static BusyBox as an optional SD runtime userland without replacing PID 1 shell or recovery-critical paths.
- Result: PASS. BusyBox 1.36.1 runs from `/mnt/sdext/a90/bin/busybox`, toybox remains available as fallback, and boot selftest reports `pass=11 warn=0 fail=0`.

## Source Changes

- Added `stage3/linux_init/a90_userland.c` and `stage3/linux_init/a90_userland.h`.
- Added `stage3/linux_init/init_v99.c` and `stage3/linux_init/v99/*.inc.c`.
- Added shell commands:
  - `userland [status|verbose|test [busybox|toybox|all]]`
  - `busybox <applet> [args...]`
  - `toybox <applet> [args...]`
- Added BusyBox to helper inventory as optional `userland` helper.
- Added userland summary to `status`, `bootstatus`, and `selftest verbose`.
- Added `scripts/revalidation/build_static_busybox.sh` and `scripts/revalidation/busybox_userland.py`.

## BusyBox Build

- BusyBox version: `1.36.1`
- Source tarball SHA256: `b8cc24c9574d809e7279c3be349795c5d5ceb6fdf19ca709f80cde50e47de314`
- Built as static ARM64 using `aarch64-linux-gnu-gcc`.
- Local artifact: `external_tools/userland/bin/busybox-aarch64-static-1.36.1`
- Local symlink: `external_tools/userland/bin/busybox-aarch64-static`
- BusyBox binary SHA256: `95fcbded9318a643e51e15bc5b0f2f5281996e0b82d303ce0af8f9acc9685e7c`
- Build note: BusyBox `TC` applet was disabled because the host kernel headers exposed incompatible `TCA_CBQ_*` symbols for this cross build.

## Runtime Placement

- Runtime root: `/mnt/sdext/a90`
- BusyBox target: `/mnt/sdext/a90/bin/busybox`
- Target mode: `0755`
- Target SHA256: `95fcbded9318a643e51e15bc5b0f2f5281996e0b82d303ce0af8f9acc9685e7c`
- Selected userland paths:
  - BusyBox: `/mnt/sdext/a90/bin/busybox`
  - toybox: `/cache/bin/toybox`

## Artifacts

- `stage3/linux_init/init_v99`
  - SHA256 `fce445e98690773aa8a26d024d9e07a110a703ef28b9cdd933dbdf4bb2b3558a`
- `stage3/ramdisk_v99.cpio`
  - SHA256 `4f8daa03c24c864afd0be76a9bbf6d2c6d849dce7ece51f1d5fdca6e565047d6`
- `stage3/boot_linux_v99.img`
  - SHA256 `8d51b9a8f48e96472be9949e607e5868f5a8f4cad60580f37930e459c8ee4eaf`

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v99.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.30 (v99)" \
  --verify-protocol auto
```

Result:

- Local image SHA256 matched remote `/cache/boot_linux_next.img`.
- Boot partition prefix SHA256 matched `stage3/boot_linux_v99.img`.
- Post-boot `cmdv1 version/status` returned `rc=0`, `status=ok`.

## Device Validation

- `version`: PASS, `A90 Linux init 0.8.30 (v99)`.
- `status`: PASS, `userland: busybox=ready toybox=ready warn=0`.
- `bootstatus`: PASS, `selftest: pass=11 warn=0 fail=0 duration=39ms`.
- `userland`: PASS.
- `userland verbose`: PASS, BusyBox selected from SD and toybox selected from `/cache/bin/toybox`.
- `userland test busybox`: PASS.
- `busybox sh -c 'echo A90_BUSYBOX_OK'`: PASS.
- `busybox ls /proc`: PASS.
- `userland test toybox`: PASS.
- `selftest verbose`: PASS, userland entry reports BusyBox and toybox ready.
- `runtime`: PASS, backend `sd`, root `/mnt/sdext/a90`, writable `yes`.
- `helpers verbose`: PASS, BusyBox helper present and executable.
- `storage`: PASS.
- `mountsd status`: PASS.
- `statushud`: PASS.
- `autohud 2`: PASS.
- `screenmenu`: PASS, returned immediately.
- `hide`: PASS.
- `netservice status`: PASS after hiding menu; menu-visible busy gate also correctly blocked dangerous status path first.

## Host Tool Validation

- `scripts/revalidation/busybox_userland.py local-info`: PASS.
- `scripts/revalidation/busybox_userland.py status`: PASS.
- `scripts/revalidation/busybox_userland.py verify`: PASS.
- `scripts/revalidation/busybox_userland.py smoke busybox`: PASS.

## Recovery Note

During BusyBox deployment, `adb reboot` and `twrp reboot` from recovery repeatedly returned to recovery. `adb shell 'setprop sys.powerctl reboot'` successfully booted back into native init. Keep this as the preferred manual recovery-to-native reboot fallback when TWRP reboot routing is sticky.

## Acceptance

- BusyBox is optional and does not block boot.
- Native PID 1 shell remains independent of BusyBox.
- BusyBox failures flow through `a90_run` command result handling.
- toybox remains available as fallback.
- SD runtime root remains the preferred userland location with `/cache` fallback policy unchanged.
- Recovery-critical serial bridge, HUD/menu, storage, selftest, and netservice status regressions passed.

## Next

The next planned version is v100 `0.9.0 v100 REMOTE SHELL`: prototype an explicit opt-in remote shell path over verified USB NCM while keeping USB ACM serial as the rescue channel.

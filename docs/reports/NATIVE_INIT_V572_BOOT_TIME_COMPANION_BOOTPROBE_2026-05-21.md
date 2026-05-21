# Native Init V572 Boot-Time Companion Bootprobe Report

Date: `2026-05-21`

## Goal

Implement the smallest V572 unit from the boot-time companion timing plan:
a disabled-by-default PID1 bootprobe hook that can run helper v94 in
`wifi-companion-start-only` mode early in native boot when an explicit cache
flag is present.

## Local Result

- Decision: `v572-bootprobe-local-build-pass`
- Pass: `True`
- Native build artifact: `A90 Linux init 0.9.62 (v572)`
- Boot image: `stage3/boot_linux_v572.img`
- Device flash: not executed
- Bootprobe live flag: not created
- Daemon start: not executed
- Wi-Fi bring-up: not executed

## Disabled-Flag Live Smoke

After local artifact validation, `stage3/boot_linux_v572.img` was flashed with
the bootprobe flag absent.

Result: PASS.

Evidence:

```text
remote image sha256: 6ece8862e74fe41c48f6b0739eaaa3036942c7f8bc7b799784fbc24fbbd390b2
boot block prefix sha256: 6ece8862e74fe41c48f6b0739eaaa3036942c7f8bc7b799784fbc24fbbd390b2
A90 Linux init 0.9.62 (v572)
selftest: pass=11 warn=1 fail=0
timeline: shell ready at 4312ms
wifi-bootprobe: disabled flag=/cache/native-init-wifi-bootprobe
```

## Opt-In Live Finding

The first opt-in bootprobe attempt created `/cache/native-init-wifi-bootprobe`
and rebooted.

Result: BLOCKED.

Observed host state:

```text
adb devices: empty
/dev/ttyACM*: absent
lsusb: no Samsung/ACM device
a90ctl version: A90P1 END marker not found before timeout
```

Interpretation:

The opt-in hook runs before ACM gadget setup. If any pre-ACM step blocks,
host-side serial/TWRP automation cannot recover the session. The most likely
local code issue is that the timeout cleanup path can still block PID1 while
waiting for an unreaped or uninterruptible helper child.

Immediate mitigation is V573:

- make the bootprobe flag one-shot;
- require a second run flag before executing the helper;
- avoid automatic SELinuxfs mount in the early bootprobe path;
- make `a90_run_stop_pid_ex()` avoid blocking forever after SIGKILL timeout.

## Scope Confirmation

V572 local implementation only built artifacts. It did not:

- flash boot partition;
- reboot the device;
- create `/cache/native-init-wifi-bootprobe`;
- start companion daemons;
- start Wi-Fi HAL, supplicant, or hostapd;
- scan/connect/link-up;
- read Wi-Fi credentials;
- run DHCP, route changes, or external ping.

## Changes

- Added `stage3/linux_init/init_v572.c` and `stage3/linux_init/v572/` based on
  the verified v319 include tree.
- Bumped native metadata in `stage3/linux_init/a90_config.h` to
  `0.9.62 (v572)`.
- Added V572 changelog entry in `stage3/linux_init/a90_changelog.c`.
- Added disabled-by-default bootprobe constants:
  - `/cache/native-init-wifi-bootprobe`
  - `/cache/bin/a90_android_execns_probe`
  - `/mnt/sdext/a90/private-property-v317/v535/dev/__properties__`
  - `wifi-bootprobe-v572.log`
- Added bounded boot hook in `stage3/linux_init/v572/90_main.inc.c`.

## Bootprobe Contract

The hook runs only if `/cache/native-init-wifi-bootprobe` exists and does not
contain `0`, `off`, `disabled`, or `no`.

When enabled, it:

1. verifies helper executable presence;
2. prepares Android read-only layout;
3. verifies private property root is a directory and not a symlink;
4. mounts or verifies `/sys/fs/selinux/status`;
5. runs helper v94 in `wifi-companion-start-only` mode with:

```text
--allow-cnss-start-only
--allow-wifi-companion-start-only
--allow-qrtr-ns-readback
```

The hook uses a PID1-side hard timeout and process-group kill path, appends
evidence to the private runtime log directory, records timeline/kmsg markers,
and always returns to the normal native boot path.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v572` | `e4ef87cec67a47e88652b021b690dc1bd95132531302a00e4c98bcf6aabda2a2` |
| `stage3/ramdisk_v572.cpio` | `079689ff79167cb816ec8634fc86581f11cebf8c9723f9823c3f9bf984cf7151` |
| `stage3/boot_linux_v572.img` | `6ece8862e74fe41c48f6b0739eaaa3036942c7f8bc7b799784fbc24fbbd390b2` |

## Static Validation

```text
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra ...
aarch64-linux-gnu-strip stage3/linux_init/init_v572
file stage3/linux_init/init_v572
sha256sum stage3/linux_init/init_v572 stage3/ramdisk_v572.cpio stage3/boot_linux_v572.img
strings stage3/boot_linux_v572.img | rg 'A90 Linux init 0\.9\.62 \(v572\)|A90v572|native-init-wifi-bootprobe|wifi-bootprobe-v572|--allow-qrtr-ns-readback'
git diff --check
```

Result: PASS.

## Boot Image Packaging

V572 boot image was created by unpacking verified `stage3/boot_linux_v319.img`
and replacing only the ramdisk:

```text
python3 mkbootimg/unpack_bootimg.py --boot_img stage3/boot_linux_v319.img ...
python3 mkbootimg/mkbootimg.py ... --ramdisk stage3/ramdisk_v572.cpio --output stage3/boot_linux_v572.img
```

Rollback image remains:

```text
stage3/boot_linux_v319.img
```

## Next Gate

Before any live flash:

1. verify current device state with `version`, `status`, and `selftest`;
2. verify helper v94 SHA256 on device or deploy it again;
3. keep `/cache/native-init-wifi-bootprobe` absent for the first disabled-flag
   boot smoke;
4. flash `stage3/boot_linux_v572.img`;
5. verify native serial/NCM returns with `A90 Linux init 0.9.62 (v572)`;
6. only after disabled-flag boot is clean, create the bootprobe flag and reboot
   for the bounded companion-only timing proof.

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.

## Post-incident Recovery Update

After the V572 opt-in reboot, the device showed the A90 loading screen with
`0.9.62 v572` and repeatedly rebooted before USB ACM/ADB returned.

The device was manually placed into TWRP/recovery and rolled back to the known
stable V319 image:

```text
[native-init-flash 23:10:59] local image sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
[native-init-flash 23:11:01] boot block prefix sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
[native-init-flash 23:11:25] cmdv1 verify passed: version/status rc=0 status=ok
A90 Linux init 0.9.61 (v319)
selftest: pass=11 warn=1 fail=0
pid1guard: pass=11 warn=1 fail=0
```

Native verification after rollback:

```text
/cache/native-init-wifi-bootprobe: No such file or directory
/cache/native-init-wifi-bootprobe-run: No such file or directory
A90 Linux init 0.9.61 (v319)
boot: BOOT OK shell 4.1s
```

The preserved logs show repeated V572 starts in `/cache/native-init.log` and
`/cache/native-init.log.1`:

```text
timeline: replay=cache init-start ... detail=A90 Linux init 0.9.62 (v572)
boot: A90 Linux init 0.9.62 (v572) start
```

The SD log only captured the earlier disabled-flag V572 boot and the subsequent
operator-initiated reboot command:

```text
wifi-bootprobe: disabled flag=/cache/native-init-wifi-bootprobe
cmd: start name=reboot argc=1 flags=0x14
```

No `wifi-bootprobe enabled`, helper spawn, timeout, or completion line was
captured for the opt-in loop. Therefore the current evidence does not prove the
helper itself ran; it proves the V572 opt-in boot path created a pre-USB boot
loop/reboot hazard. The boot-time PID1 companion probe path is retired until it
has stronger isolation than a pre-ACM PID1 hook.

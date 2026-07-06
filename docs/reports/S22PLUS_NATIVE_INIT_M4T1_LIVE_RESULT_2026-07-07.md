# S22+ Native-Init M4T1 Live Result - 2026-07-07

## Scope

One attended S22+ M4T1 in-place MagiskBoot native-init live gate using the
SHA-pinned `AGENTS.md` exception and guarded helper. The action touched only
the `boot` partition through Odin AP packages. No recovery, vendor_boot,
vbmeta, dtbo, BL, CP, CSC, userdata, EFS, RPMB, keymaster, modem, or other
partition payload was flashed.

## Candidate

Helper:

```text
workspace/public/src/scripts/revalidation/s22plus_m4t1_inplace_live_gate.py
```

Run directory:

```text
workspace/private/runs/s22plus_m4t1_inplace_live_gate_live_20260707T0520Z
```

Candidate hashes:

```text
AP.tar.md5  9f5b4c48b95b710f742d5ea8c7f16ef4802cf27e78469381073d460361d0451c
boot.img    9ce597e4ba920f1331937dbe4736f923728ff5502b02c02dea8357b3a9d5b9d1
base boot   2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel      bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
```

The AP contained exactly one member:

```text
boot.img.lz4
```

## Live Timeline

Preflight:

```text
agents_exception_missing=[]
current Android: SM-S906N / g0q / S906NKSS7FYG8
boot_completed=1
verifiedbootstate=orange
Magisk root available
```

Transition to download mode:

```text
adb_reboot_download_rc=0
candidate Odin wait: one download-mode device appeared
```

Candidate flash:

```text
candidate_odin_rc=0
boot.img.lz4 reached 100%
post-candidate-disconnect_odin_absent=1
```

M4T1 observation window:

```text
m4t1_self_download_seen=0
ADB rows during candidate window: none
Odin rows during candidate window: none
helper rc=4
```

The operator observed a bootloop and manually entered download mode. The host
then observed one Odin/download-mode device.

Manual rollback:

```text
rollback AP.tar.md5 sha256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
rollback AP members=['boot.img.lz4']
rollback Odin rc=0
boot.img.lz4 reached 100%
```

Post-rollback Android verification:

```text
boot_completed=1
bootanim=stopped
model=SM-S906N
device=g0q
build=S906NKSS7FYG8
su_id=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
boot_sha256=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

Rollback restored the known-good Magisk boot baseline.

## Retained Evidence

After rollback:

```text
/sys/fs/pstore files: none
/proc/last_kmsg bytes: 2097136
S22_NATIVE_INIT_INSTANT_DOWNLOAD_M4T0: false
S22_NATIVE_INIT: false
M4T1: false
```

The collected `last_kmsg` contained normal Android-side `init` service logs
from the restored Magisk boot, not a useful early-failure transcript from the
M4T1 candidate. Retained logs remain a dead or overwritten channel for this
stage.

## Interpretation

M4T1 removed the strongest M4T0 packaging variable:

- known-booting Magisk boot was the base;
- no-change `magiskboot unpack/repack` was byte-identical;
- `SAMSUNG_SEANDROID` and `VBMETA` shape was preserved;
- Magisk-patched kernel was preserved;
- only ramdisk `/init` was replaced.

Even with those variables removed, the candidate did not self-enter download
mode and did not return ADB. Therefore the old `mkbootimg` reconstruction
hypothesis is not sufficient.

The next likely fault domain is the direct native `/init` execution path
itself: exec failure, immediate crash, invalid PID1 userspace ABI expectation,
or a kernel panic such as "Attempted to kill init" before the first-action
download reboot can complete. Without UART or a retained panic log, this live
result cannot distinguish those subcases.

## Stop Condition

Do not retry M4T1. Do not add more marker/dwell/watchdog logic to the same
reboot-first branch. The next bounded unit should be host-only and should
either:

- build a smaller non-returning PID1 probe that avoids glibc startup and
  reboot syscall complexity, preferably raw-syscall static assembly/C with an
  infinite park as the first observable behavior; or
- move to UART or another early-boot observation channel before further live
  native-init flashes.

Any next live boot candidate still requires a fresh SHA-pinned `AGENTS.md`
exception, guarded helper, dry-run, and attended rollback plan.

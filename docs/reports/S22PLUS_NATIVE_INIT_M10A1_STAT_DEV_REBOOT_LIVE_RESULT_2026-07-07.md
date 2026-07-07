# S22+ Native-Init M10A1 Stat-Dev Reboot Live Result - 2026-07-07

## Verdict

M10A1 did not prove automatic download-mode return.

The exact SHA-pinned M10A1 boot-only AP flashed, the original Samsung download
endpoint disconnected, and the helper later observed Samsung download mode and
restored the pinned Magisk boot-only rollback AP. The operator confirmed the
device was bootlooping and manually entered download mode, so the later endpoint
is not an automatic M10A1 self-download proof.

Safety result passed: rollback completed, Android returned to the rooted Magisk
baseline, `sys.boot_completed=1`, `init.svc.bootanim=stopped`, Magisk root was
available, and post-rollback uptime was increasing.

Interpretation: M10A1 is a recovered bootloop/manual-download result. Since
M10A1 removed the M10A `mkdirat` mutation and kept only read-only
`newfstatat("/dev")`, the suspect boundary is now either pathname VFS access
itself or the more general shape of making any non-reboot syscall before the
Samsung `reboot("download")` request.

## Candidate

```text
AP.tar.md5             68a7f1f5b336a32d882e7cdde73f299815d689b6885b724a6b6c7672bdda00bf
boot.img               2fe6b3270f7d493f677f126594061eea33d22de7abe98dc2210fe8050961ecb2
M10A1 /init            477583121c6c29f5eb31866c034352abb2f03c8fe97ec71e2f63ecbddd6f1642
source                 a60b66ec5d07f93bb9e29ac96c342e57621815630c29f31653b104e19f7ff86b
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
runtime                freestanding-c-raw-syscall
```

M10A1 intended runtime:

```text
direct PID1
freestanding C
first side effect = newfstatat(AT_FDCWD, "/dev", stack_statbuf, 0)
then reboot("download")
no mkdirat
no marker
no /dev/kmsg
no mknodat
no mount
no sleep
no modules
no configfs or USB gadget
park if reboot returns
```

## Live Timeline

Private live run log:

```text
workspace/private/runs/s22plus_m10a1_stat_dev_reboot_live_gate_20260707T121731Z/s22plus_m10a1_stat_dev_reboot_live_gate.txt
```

Key helper events:

```text
12:17:31Z  live helper start
12:17:52Z  Samsung download endpoint appeared for candidate flash
candidate_odin_rc=0
12:17:55Z  original Odin endpoint absent; disconnect proof acquired
12:17:55Z  download observation window started
12:19:02Z  Samsung download endpoint observed by helper
m10a1_download_endpoint_seen=1
m10a1_manual_download_ambiguity=operator-confirmation-required
magisk_rollback_odin_rc=0
12:19:47Z  Android returned with boot_completed=1 and Magisk root
```

Operator correction:

```text
The device was bootlooping.
The operator manually entered download mode.
Therefore the 12:19:02Z endpoint is not an automatic M10A1 self-download proof.
```

Approximate elapsed time from original endpoint disconnect to the manually
confirmed download endpoint: 67 seconds.

## Post-Rollback Verification

Helper post-rollback result:

```text
sys.boot_completed       1
Magisk root              available
pstore files             none
/proc/last_kmsg bytes    2097136
M10A1 marker in retained no
```

The retained-marker result is expected: M10A1 intentionally has no marker and
no kmsg write.

Independent host check after helper completion:

```text
ADB state                Android device attached
sys.boot_completed       1
init.svc.bootanim        stopped
boot reason              reboot,download
Magisk root              available
```

## Interpretation

Updated live boundary:

```text
M4T3 raw assembly first-action reboot("download")          in-window PASS, about 44 s
M9A freestanding C first-action reboot("download")         delayed download, about 106 s
M10A1 freestanding C newfstatat("/dev") then reboot        BOOTLOOP, manual-download rollback
M10A freestanding C mkdirat("/dev") then reboot            BOOTLOOP, manual-download rollback
M8A freestanding C minimal-fs setup before reboot          NO SELF-DOWNLOAD in prior run
```

M10A1 narrows the M10A failure: the mkdir mutation is not required to reproduce
the bootloop. The remaining ambiguity is:

```text
path A: pathname VFS access itself is unsafe in this early PID1 state.
path B: any additional non-reboot syscall before reboot changes the timing/state enough to lose automatic download return.
```

Do not proceed to larger VFS/mkdir/mount candidates. The next unit should be
host-only and should split M10A1 with a non-VFS pre-syscall discriminator:

```text
M10A2 getpid-reboot
getpid(), then reboot("download")
no pathname strings except "download"
no VFS
no mkdir/mknod/mount/kmsg/sleep/module/configfs/USB
```

Branch logic:

```text
M10A2 reaches download without manual entry:
  an extra pre-reboot syscall is survivable; M10A1 points at pathname VFS access.

M10A2 bootloops / requires manual download:
  the issue is broader than VFS; inspect freestanding C syscall/timing/state before adding more filesystem work.
```

## Stop Rule

M10A1 is recovered. Do not repeat it unchanged and do not extend to more
filesystem setup until M10A2 or an equivalent non-VFS pre-syscall discriminator
has been built and gated.

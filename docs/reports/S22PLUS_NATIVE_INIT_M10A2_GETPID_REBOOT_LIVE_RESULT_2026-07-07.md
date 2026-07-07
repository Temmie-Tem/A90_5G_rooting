# S22+ Native-Init M10A2 Getpid Reboot Live Result - 2026-07-07

## Verdict

M10A2 did not prove automatic download-mode return.

The exact SHA-pinned M10A2 boot-only AP flashed, the original Samsung download
endpoint disconnected, and the helper later observed Samsung download mode and
restored the pinned Magisk boot-only rollback AP. The operator confirmed the
device was bootlooping and manually entered download mode, so the later endpoint
is not an automatic M10A2 self-download proof.

Safety result passed: rollback completed, Android returned to the rooted Magisk
baseline, `sys.boot_completed=1`, `init.svc.bootanim=stopped`, Magisk root was
available, and the live boot partition SHA256 matched the known-booting Magisk
baseline.

Interpretation: M10A2 is a recovered bootloop/manual-download result. Since
M10A2 removed pathname/VFS access and made only a non-VFS `getpid()` syscall
before `reboot("download")`, the failure is broader than pathname VFS access.
The Samsung download reboot path is only proven when it is effectively the first
runtime action; adding a prior syscall changes the early-PID1 state/timing enough
to lose automatic download-mode return.

## Candidate

```text
AP.tar.md5             108c0a5e2a1fd80efed5ae93ea01b4b98c4990f7d3d8b292ef35ccc0de2fdb60
boot.img               f0238a82cad63a3d8017a0892a3a85bfe79c8c503848a4ac0fa4a21a77a72c94
M10A2 /init            0839562fbef74328abb17646d957516154ae85ab954667782c809249cf8bde99
source                 5b15166dfc405a7ee1297ac1cd0da3bd844779099748cf98ee3aca8e2e665d9a
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
runtime                freestanding-c-raw-syscall
```

M10A2 intended runtime:

```text
direct PID1
freestanding C
first side effect = getpid()
then reboot("download")
no pathname access
no VFS
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
workspace/private/runs/s22plus_m10a2_getpid_reboot_live_gate_20260707T123803Z/s22plus_m10a2_getpid_reboot_live_gate.txt
```

Key helper events:

```text
12:38:03Z  live helper start
12:38:14Z  dry-run/current baseline snapshot complete
12:38:25Z  Samsung download endpoint appeared for candidate flash
candidate_odin_rc=0
12:38:28Z  original Odin endpoint absent; disconnect proof acquired
12:38:28Z  download observation window started
12:39:27Z  Samsung download endpoint observed by helper
m10a2_download_endpoint_seen=1
m10a2_manual_download_ambiguity=operator-confirmation-required
magisk_rollback_odin_rc=0
12:40:13Z  Android returned with boot_completed=1 and Magisk root
```

Operator correction:

```text
The device was bootlooping.
The operator manually entered download mode.
Therefore the 12:39:27Z endpoint is not an automatic M10A2 self-download proof.
```

Approximate elapsed time from original endpoint disconnect to the manually
confirmed download endpoint: 59 seconds.

## Post-Rollback Verification

Helper post-rollback result:

```text
sys.boot_completed       1
Magisk root              available
pstore files             none
/proc/last_kmsg bytes    2097136
M10A2 marker in retained no
```

The retained-marker result is expected: M10A2 intentionally has no marker and
no kmsg write.

Independent host check after helper completion:

```text
ADB state                Android device attached
sys.boot_completed       1
init.svc.bootanim        stopped
boot reason              reboot,download
Magisk root              available
boot partition SHA256    2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

## Interpretation

Updated live boundary:

```text
M4T3 raw assembly first-action reboot("download")          in-window PASS, about 44 s
M9A freestanding C first-action reboot("download")         delayed download, about 106 s
M10A2 freestanding C getpid() then reboot                  BOOTLOOP, manual-download rollback
M10A1 freestanding C newfstatat("/dev") then reboot        BOOTLOOP, manual-download rollback
M10A freestanding C mkdirat("/dev") then reboot            BOOTLOOP, manual-download rollback
M8A freestanding C minimal-fs setup before reboot          NO SELF-DOWNLOAD in prior run
```

M10A2 narrows the failure below VFS. The remaining ambiguity is:

```text
path A: any extra syscall before Samsung reboot("download") makes self-download unreliable in this early PID1 context.
path B: the two-helper freestanding C shape, stack/return sequence, or timing between helper calls is the sensitive factor.
```

Do not proceed to larger VFS/mkdir/mount candidates. The next unit should stay
below filesystem work and either inspect the M9A-versus-M10A2 instruction/timing
delta host-only or build a tighter discriminator that changes only one of:

```text
same two-helper C shape but no getpid before reboot
single inline assembly sequence with getpid immediately followed by reboot
first-action reboot with the M10A2 helper/stack shape but no prior syscall
```

## Stop Rule

M10A2 is recovered. Do not repeat it unchanged and do not extend to filesystem,
module, configfs, or USB work until the M9A-to-M10A2 early-syscall/timing
boundary is split.

# S22+ Native-Init M12 M5-Floor Live Result - 2026-07-07

## Verdict

M12 did not reach the USB-ACM control-channel milestone.

The boot-only M12 candidate AP flashed successfully, but the candidate exposed
no ACM transport and no ADB transport during the observation window. The
operator observed a boot loop and manually entered Samsung download mode. The
rollback-only helper then detected the Odin endpoint and flashed the pinned
Magisk boot-only rollback AP successfully. Android returned with Magisk root
and the expected boot hash.

This is a live NO-GO for M12. Do not repeat M12 unchanged.

## Candidate

```text
AP.tar.md5             deece127aa5c85dbf4937459fc528f2cfcd9926fb3556f26ffc9b10fbfe932cb
boot.img               f211e46c7153df31c458a907f4ac56fe4a3d160d8ded2a13a8e0e31af6f5106c
M12 /init              50ae525230680c495d3c40fc671cb88118e8bd473cef92873266142549a28002
M12 module list        c2e44f6f934542f8f7889ef09245294ee342c5ae03a0f6db9988b58b943ddc16
source                 5b43593a24b3b03a667f5515b8a558e40121b4da091efb56adf383ea50240392
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

The AP contained exactly one member:

```text
boot.img.lz4
```

## Live Timeline

Private candidate run log:

```text
workspace/private/runs/s22plus_m12_m5_floor_live_gate_20260707T135627Z/s22plus_m12_m5_floor_live_gate.txt
```

Private rollback run log:

```text
workspace/private/runs/s22plus_m12_m5_floor_live_gate_20260707T140005Z/s22plus_m12_m5_floor_live_gate.txt
```

Key events:

```text
13:56:27Z  live helper start
13:56:38Z  Android/Magisk preflight passed; current boot hash matched baseline
13:56:38Z  adb reboot download requested for the host-controlled Odin flash
13:56:49Z  Odin/download device appeared for candidate flash
13:56:49Z  M12 candidate AP flash started
13:56:51Z  candidate Odin flash rc=0
13:56:51Z  M12 ACM/ADB/Odin observation started
13:58:50Z  observation ended with no ACM, no ADB, and no Odin endpoint
14:00:05Z  rollback-only helper started after operator manual download-mode entry
14:00:05Z  Magisk boot-only rollback AP flash started
14:00:07Z  rollback Odin flash rc=0
14:00:51Z  Android returned with boot_completed=1
```

Observed during the M12 window:

```text
M12 ACM devices       none
ADB transports       none
Odin transport       absent during the 120 second observation window
```

The live helper exited with rc=4 and requested manual download-mode rollback
because M12 deliberately has no reboot beacon and no ACM command path.

## Rollback

Rollback path:

```text
manual download mode entered after boot loop
Magisk boot-only AP flashed
rollback Odin rc=0
Android returned
boot_completed=1
bootanim=stopped
Magisk root available
pstore_files=[]
```

Post-rollback boot hash:

```text
2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

Independent post-run verification also confirmed:

```text
boot_completed=1
bootanim=stopped
build=S906NKSS7FYG8
current boot hash=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
/sys/fs/pstore empty
```

Retained marker evidence:

```text
post_rollback_pstore_marker_found=0
post_rollback_last_kmsg_marker_found=0
post_rollback_retained_marker_found=0
```

The absence of retained markers means this live run does not prove whether M12
reached its `/dev/kmsg` marker. It proves only the external behavior: candidate
flash succeeded, no ACM appeared, Android did not return, the operator observed
boot looping, and rollback succeeded.

## Interpretation

M12 was intended to distinguish whether the M11 boot loop was caused by the
24 M11-only substrate modules. It kept the M11 freestanding PID1, configfs,
role-force, and park-loop shape, but reduced the runtime module list to the
24 modules common to M5 and M11, loaded from stock vendor_boot `/lib/modules`.
It withheld the 24 M11-only substrate modules and the two M5-only modules:

```text
usb_notifier_qcom.ko
qc_usb_audio.ko
```

The result follows the M12 branch:

```text
still loops, no ACM
```

That falsifies the narrow hypothesis that the M11 loop was solely caused by the
24 M11-only modules. It does not prove a specific module fault, because M12
still changed several things relative to the older non-looping M5 floor: module
source path, freestanding loader/runtime order, configfs timing, role-force
timing, and retained logging behavior.

Because retained markers are absent, do not over-interpret this as a specific
module, VFS, or configfs crash. The strongest current conclusion is narrower:
the current park-based USB runtime cannot yet recover a non-looping floor even
when reduced to the M5/M11 common module subset.

## Next

Next bounded unit should be host-only and should shrink below M12 before any
new live flash:

1. Remove module insertion first while keeping only the freestanding PID1,
   minimal marker path, and bounded park behavior.
2. In a separate candidate, remove configfs/role-force and keep only the marker
   path plus park behavior.
3. Add an independent retained evidence path if available, because pstore and
   last_kmsg did not retain the M11/M12 markers.
4. Only after a non-looping floor is recovered, add USB substrate back in small
   groups.

Keep the same constraints: boot-only AP, no forbidden partitions, no raw host
`dd`, no fastboot, attended live ack, and pinned Magisk boot-only rollback.

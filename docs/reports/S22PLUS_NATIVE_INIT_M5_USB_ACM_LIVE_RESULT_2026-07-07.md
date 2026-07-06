# S22+ Native-Init M5 USB-ACM Live Result - 2026-07-07

## Verdict

M5 v0.4 live gate did not achieve the USB-ACM control-channel milestone.

The boot-only candidate AP flashed successfully, but no M5 ACM gadget, ADB
transport, or Odin/download transport appeared during the bounded observation
window. The phone was then put into download mode manually and the pinned Magisk
boot-only rollback completed successfully. Android returned with Magisk root and
the expected boot hash.

## Candidate

```text
AP.tar.md5             5bce15dede8bcd84b8ead1a7f6db6b09135d38637c983d06965930c40a00159f
boot.img               3f4e9a514549a2cad2475ef7ef745dfc7e832c910cf1cca25ec4654c9c5522a1
M5 /init               596e4198bbdfece9eb1c227acd19cdca1934a440a544fe43cfdf79976a4fc594
module manifest        1c22c93496e03a7df6dd74959511797b6d033b74361d3d3733d7be8269a5fa05
runtime                freestanding-raw-syscall
glibc_static_startup   false
```

The AP contained exactly one member:

```text
boot.img.lz4
```

## Live Timeline

Private run log:

```text
workspace/private/runs/s22plus_m5_usb_acm_live_gate_20260706T214040Z/s22plus_m5_usb_acm_live_gate.txt
```

Key events:

```text
21:40:40Z  live helper start
21:40:41Z  Android preflight passed
21:40:52Z  Android stability preflight passed, samples=4
21:40:52Z  current boot hash matched Magisk baseline
21:40:52Z  adb reboot download requested
21:41:03Z  Odin/download device appeared for candidate flash
21:41:03Z  M5 candidate AP flash started
21:41:04Z  candidate Odin flash rc=0
21:41:05Z  M5 observation started
21:43:05Z  M5 observation ended, m5_acm_seen=0
```

Observed during the M5 window:

```text
M5 ACM devices       none
ADB transports       none
Odin transports      none
host new net links   none recorded
```

The helper exited with rc `4` and required manual download-mode entry for
rollback, as designed for the no-transport case.

## Rollback

Private rollback log:

```text
workspace/private/runs/s22plus_m5_usb_acm_live_gate_20260706T214403Z/s22plus_m5_usb_acm_live_gate.txt
```

Rollback path:

```text
manual download mode entered
Magisk boot-only AP flashed
rollback Odin rc=0
Android returned
boot_completed=1
bootanim=stopped
Magisk root available
```

Post-rollback boot hash:

```text
2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

The rollback helper collected pstore/last_kmsg, but did not find the M5 marker:

```text
post_rollback_retained_marker_found=0
```

## Interpretation

This is a live NO-GO for the M5 USB-ACM control-channel milestone.

The result does not prove where M5 stopped. Because v0.4 removed glibc static
startup, the remaining plausible failure range is now the freestanding C/syscall
harness, early virtual filesystem mounts, module insertion, configfs gadget
setup, UDC binding, or ttyGS0 command loop. No retained marker was found, so the
current evidence cannot prove the candidate reached its kmsg marker or any later
phase.

## Next

Do not tweak the full USB chain blindly. The next bounded unit should split the
front of M5:

1. Build a freestanding C mount/reboot beacon: `_start` plus direct syscalls,
   mount only `/proc`, `/sys`, `/dev`, and `/config`, emit the M5-style marker,
   then request `reboot(..., "download")`.
2. If that self-downloads, the freestanding C harness and VFS mounts are good;
   move to a module/configfs bisect.
3. If it parks/no-transports again, shrink further to freestanding C reboot-only
   versus marker-only to isolate compiler/runtime/stack from mounts.

Keep the same constraints: boot-only AP, SHA-pinned `AGENTS.md` exception,
attended live ack, no forbidden partitions, and pinned Magisk boot rollback.

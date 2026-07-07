# S22+ Native-Init M17 Power-QMP Live Result - 2026-07-08

## Verdict

M17 did not reach the USB-ACM control-channel milestone.

The boot-only M17 candidate AP flashed successfully, but no ACM transport,
ADB transport, or Odin transport appeared during the bounded observation
window. The live helper therefore stopped fail-closed and requested manual
download-mode recovery. The operator observed a boot loop, manually entered
download mode, and the rollback-only helper restored the pinned Magisk
boot-only baseline successfully.

This is a live NO-GO for M17. Do not repeat M17 unchanged.

## Candidate

```text
AP.tar.md5       78b2641788a1517f39bdbd50dc425dbaeab0683aa662bcd8bfe9c925a8a50274
boot.img         090811c8f50aab753ef7f085c3cf5bd73e9d6d43e2ad629e95d2cfe48a0ecac2
M17 /init        34389fc52cd74aa50b2ab2980075183bcde519ffc5d7f9dfb787e1e5b3e2bfe4
M17 module list  1e00da43ae2b22c56855a28967201733b66b65ec4e91086faa67a4d9b3177fb8
source           561099a8401ea6b5d5642614b6f6a73e225b239556de07c11cf2d99e1d0a6d2f
base boot        2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel           bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
```

The AP contained exactly one member:

```text
boot.img.lz4
```

M17 loaded the recovery-order 21-module power/clock substrate plus
`phy-msm-ssusb-qmp.ko`. It intentionally did not load the DWC3 controller,
ACM function, or the complementary EUSB2 PHY module.

## Live Timeline

Private candidate run log:

```text
workspace/private/runs/s22plus_m17_power_qmp_live_gate_20260707T152929Z/s22plus_m17_power_qmp_live_gate.txt
```

Private rollback run log:

```text
workspace/private/runs/s22plus_m17_power_qmp_live_gate_20260707T153918Z/s22plus_m17_power_qmp_live_gate.txt
```

Key events:

```text
15:29:29Z  live helper start
15:29:40Z  Android/Magisk preflight passed; current boot hash matched baseline
15:29:40Z  adb reboot download requested for the host-controlled Odin flash
15:29:50Z  Odin/download device appeared for candidate flash
15:29:52Z  M17 candidate AP flash rc=0
15:29:52Z  M17 ACM/ADB/Odin observation started
15:31:51Z  bounded observation ended with no ACM, no ADB, no Odin
15:39:18Z  rollback-only helper started after operator manual download-mode entry
15:39:19Z  Magisk boot-only rollback AP flash rc=0
15:39:52Z  Android returned with boot_completed=1
```

Observed during the M17 window:

```text
M17 ACM devices       none
ADB transports       none
Odin transport       none during bounded helper observation
operator visual      boot loop
```

The live helper completed with rc=4 because no recovery transport appeared
inside its bounded observation window. Rollback was then performed with the
separate `--rollback-from-download` mode after manual download-mode entry.

## Rollback

Rollback path:

```text
Magisk boot-only AP flashed
rollback Odin rc=0
Android returned
boot_completed=1
bootanim=stopped
verified boot state=orange
boot_reason=reboot,download
Magisk root available
```

Post-rollback boot hash:

```text
2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

Retained marker evidence from the rollback helper:

```text
post_rollback_pstore_marker_found=0
post_rollback_last_kmsg_marker_found=0
post_rollback_retained_marker_found=0
```

The absence of retained markers means this live run does not prove which M17
line or module executed before reset. It proves only the external behavior:
candidate flash succeeded, no ACM appeared, Android did not return before
rollback, the operator observed boot looping, manual download-mode recovery was
needed, and rollback succeeded.

## Interpretation

M15 showed that the two PHY-side modules still looped:

```text
phy-msm-ssusb-qmp.ko
phy-msm-snps-eusb2.ko
```

M17 tested the corrected next hypothesis: `phy-msm-ssusb-qmp.ko` should not be
tested naked because it may require the power, RPMh, regulator, clock, interconnect,
SMEM, and SCM substrate first. M17 therefore loaded that substrate before QMP.

M17 still looped and produced no ACM. This falsifies the simple branch that
M15 failed only because QMP was missing its basic power/clock substrate.

Do not continue blind module-subset permutations from here. The next bounded
unit should be a host-only postmortem and an observation-plan upgrade:

1. Decide whether UART-quality kernel output is reachable for this board.
2. If UART is not practical, design a different retained proof channel that can
   survive this reset class.
3. Only then build another live candidate.

Keep the same constraints: boot-only AP, no forbidden partitions, no raw host
`dd`, no fastboot, attended live ack, and pinned Magisk boot-only rollback.

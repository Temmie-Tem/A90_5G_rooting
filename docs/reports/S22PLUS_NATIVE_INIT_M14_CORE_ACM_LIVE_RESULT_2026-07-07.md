# S22+ Native-Init M14 Core-ACM Live Result - 2026-07-07

## Verdict

M14 did not reach the USB-ACM control-channel milestone.

The boot-only M14 candidate AP flashed successfully, but no ACM transport and
no ADB transport appeared. The operator observed a boot loop and manually
entered Samsung download mode. The live helper detected the Odin endpoint,
flashed the pinned Magisk boot-only rollback AP successfully, and Android
returned with Magisk root and the expected boot hash.

This is a live NO-GO for M14. Do not repeat M14 unchanged.

## Candidate

```text
AP.tar.md5             080fedea35c111020f68b5fb64eb260402dbc45ac4398e282523c94bf9a8922b
boot.img               dee741af20fb3dbcd347c2fa4d45099018f54f577ddf7ae64ac3dca4a357c2e4
M14 /init              0a144b2ddde32d78b4dfe051e009f5275f2e67c8276b0fa2d1a61e3280b7eed4
M14 module list        5b52cd5c1ae26d0bf24e7654b27f254ee478673c9313afdb955a0ec4fcf35f7c
source                 8acc0bfff03ec3adbde160a7ad6975be4154c8a219e8e59ebe1a6d8b1a19b8a7
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

The AP contained exactly one member:

```text
boot.img.lz4
```

M14 reintroduced only this four-module core USB/ACM subset:

```text
phy-msm-ssusb-qmp.ko
phy-msm-snps-eusb2.ko
dwc3-msm.ko
usb_f_ss_acm.ko
```

## Live Timeline

Private candidate run log:

```text
workspace/private/runs/s22plus_m14_core_acm_live_gate_20260707T144816Z/s22plus_m14_core_acm_live_gate.txt
```

Key events:

```text
14:48:16Z  live helper start
14:48:27Z  Android/Magisk preflight passed; current boot hash matched baseline
14:48:27Z  adb reboot download requested for the host-controlled Odin flash
14:48:38Z  Odin/download device appeared for candidate flash
14:48:38Z  M14 candidate AP flash started
14:48:40Z  candidate Odin flash rc=0
14:48:40Z  M14 ACM/ADB/Odin observation started
14:49:37Z  Odin endpoint detected after operator-observed boot loop
14:49:37Z  Magisk boot-only rollback AP flash started
14:49:38Z  rollback Odin flash rc=0
14:50:21Z  Android returned with boot_completed=1
```

Observed during the M14 window:

```text
M14 ACM devices       none
ADB transports       none
Odin transport       returned after manual download-mode entry
operator visual      boot loop
```

The helper completed with rc=0 because it detected the Odin endpoint and
performed rollback in the same live run.

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

The absence of retained markers means this live run does not prove which M14
internal phase executed. It proves only the external behavior: candidate flash
succeeded, no ACM appeared, Android did not return before rollback, the
operator observed boot looping, Odin became available after manual download
mode entry, and rollback succeeded.

## Interpretation

M13 recovered a non-looping no-module/no-transport floor while keeping
configfs, role-force, and `a600000.dwc3` binding attempts. M14 changed only one
major axis from M13: it added the runtime `finit_module` path and a four-module
core USB/ACM list.

The result follows the M14 boot-loop branch:

```text
four-module core USB/ACM add-back loops, no ACM
```

This narrows the M12 boot-loop source below the full 24-module floor. The
fault is now inside the four-module core add-back or the act of entering the
runtime `finit_module` path under this native-init environment. It does not yet
prove which module is reset-causing.

Because retained markers are absent, do not over-interpret the outcome as a
specific module fault. The strongest current conclusion is narrower: the
current M13 configfs/role-force park shape is tolerated with no modules, but
not with this four-module core USB/ACM add-back.

## Next

Next bounded unit should be host-only M15:

1. Bisect inside the M14 core group rather than adding role/PD modules.
2. Preserve the M13/M14 configfs, role-force, `a600000.dwc3` bind policy, and
   no-reboot park model.
3. Use a smaller module-list payload, preferably a two-module split first:
   `phy-msm-ssusb-qmp.ko` + `phy-msm-snps-eusb2.ko`.
4. If that still loops, split to one module at a time and consider a
   `finit_module` open-only/no-finit control to separate loader mechanics from
   module init side effects.

Keep the same constraints: boot-only AP, no forbidden partitions, no raw host
`dd`, no fastboot, attended live ack, and pinned Magisk boot-only rollback.

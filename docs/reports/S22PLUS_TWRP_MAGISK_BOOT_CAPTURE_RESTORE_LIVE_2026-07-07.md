# S22+ TWRP + Magisk Boot-Capture Restore Live - 2026-07-07

## Scope

Live execution of the preflighted S22+ maintenance window:

1. refresh pinned TWRP recovery;
2. prove direct TWRP boot through recovery ADB;
3. flash pinned Magisk boot-only AP;
4. prove rooted Android is back for the next boot-capture measurement unit.

No native-init candidate, kernel rebuild, Magisk module, multidisabler, format
data, vbmeta write, or non-recovery/boot partition payload was flashed.

## Authorization / Gate

Committed gate:

- `78e27e30 Gate S22+ TWRP and Magisk restore window`

Preflight report:

- `docs/reports/S22PLUS_TWRP_MAGISK_BOOT_CAPTURE_RESTORE_PREFLIGHT_2026-07-07.md`

Guard helper:

- `workspace/public/src/scripts/revalidation/s22plus_twrp_magisk_restore_window.py`

Live command:

```text
python3 workspace/public/src/scripts/revalidation/s22plus_twrp_magisk_restore_window.py \
  --live \
  --ack S22PLUS-TWRP-MAGISK-RESTORE-WINDOW
```

Private live log:

```text
workspace/private/runs/s22plus_twrp_magisk_restore_20260706T172017Z/s22plus_twrp_magisk_restore_window.txt
```

## Preflight

The helper re-verified the pinned artifacts before any live write:

```text
twrp_tar_sha256=0914c68a5353c367216805a3a2fdeb4982c6629368dc021c7fefc10d3d3bd034
twrp_tar_members=['recovery.img']
magisk_ap_sha256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
magisk_ap_members=['boot.img.lz4']
stock_recovery_ap_sha256=8d3647313d2e100134f77984d13c7e5dc9946510ab57d8e34dd0cd192ca8586d
stock_recovery_ap_members=['recovery.img.lz4']
stock_boot_ap_sha256=1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
stock_boot_ap_members=['boot.img.lz4']
full_firmware_zip_sha256=f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8
```

Android preflight before download mode:

```text
model=SM-S906N
device=g0q
bootloader=S906NKSS7FYG8
incremental=S906NKSS7FYG8
vbstate=orange
boot_recovery=0
boot_completed=1
su=
```

The serial number and download-mode USB path are intentionally omitted from this
public report.

## TWRP Refresh

The helper rebooted Android to download mode, selected one Odin device, and
flashed only the pinned TWRP recovery tar without auto-reboot:

```text
odin4 -a <pinned-twrp-recovery-tar> -d <redacted-download-device>
```

Odin result:

```text
twrp_odin_rc=0
Upload Binaries
recovery.img
Close Connection
```

The operator then manually booted directly into recovery. Recovery ADB appeared
and the helper proved TWRP:

```text
twrp=3.7.0_12-1_afaneh92
model=SM-S906E
device=g0q
vbstate=orange
twrp_proof=1
```

The TWRP ramdisk reports model `SM-S906E`, consistent with the earlier g0q
TWRP live report; the Android preflight target was `SM-S906N` and the recovery
device codename was `g0q`.

## Magisk Boot-Only Restore

After TWRP proof, the helper rebooted recovery to download mode and flashed
only the pinned Magisk boot-only AP:

```text
odin4 --reboot -a <pinned-magisk-boot-only-AP> -d <redacted-download-device>
```

Odin result:

```text
magisk_odin_rc=0
Reboot into normal mode
Upload Binaries
boot.img.lz4
Close Connection
```

Android returned:

```text
boot_completed=1
model=SM-S906N
device=g0q
bootloader=S906NKSS7FYG8
incremental=S906NKSS7FYG8
vbstate=orange
boot_recovery=0
su=/product/bin/su
su_v=30.7:MAGISKSU
```

Root proof passed:

```text
su -c id
uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

Independent post-run check repeated the same result:

```text
boot_completed=1
model=SM-S906N
device=g0q
bootloader=S906NKSS7FYG8
incremental=S906NKSS7FYG8
vbstate=orange
boot_recovery=0
su=/product/bin/su
su_v=30.7:MAGISKSU
uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

## Result

PASS:

- TWRP recovery refresh transferred successfully.
- The device booted directly into TWRP recovery and exposed TWRP ADB.
- TWRP version proof passed: `3.7.0_12-1_afaneh92`.
- Magisk boot-only AP transferred successfully.
- Android booted normally afterward.
- MagiskSU is present and `su -c id` returns root.

TWRP persistence after the final Android boot is not claimed by this unit. The
unit proves TWRP was reachable in the maintenance window and restores rooted
Android for the next measurement step.

## Next

Proceed to the `GOAL.md`-directed Magisk boot-capture measurement unit on the
now-rooted Android system:

- collect `dmesg` and boot timestamps;
- collect module inventory and module dependency/load-order evidence;
- collect USB gadget/configfs state;
- collect display/panel/DRM/KGSL bring-up evidence;
- keep raw logs private and commit only a redacted public summary.

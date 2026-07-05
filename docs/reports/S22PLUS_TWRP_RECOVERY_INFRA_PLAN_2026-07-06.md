# S22+ TWRP Recovery Infrastructure Gate - 2026-07-06

## Scope

Host-side recovery-infrastructure preparation for the Samsung Galaxy S22+
`SM-S906N` / `g0q`. No live S22+ partition write, reboot, Odin transfer, TWRP
install, or vbmeta change was performed in this unit.

The conclusion is intentionally split:

- Artifact and rollback preparation: ready enough for review.
- Live TWRP flash: blocked under the current repo contract because `AGENTS.md`
  only authorizes boot-partition writes. Recovery/vbmeta writes need a narrow
  S22-specific exception before I can perform them from this repo.

## Current Device State

ADB-observed state after the stock boot rollback:

- Model: `SM-S906N`
- Device: `g0q`
- Product name: `g0qksx`
- Android release: `15`
- PDA / bootloader: `S906NKSS7FYG8`
- Bootloader lock: `ro.boot.flash.locked=0`
- Verified boot state: `orange`
- Warranty bit: `1`
- Verity mode: `enforcing`

The serial number is intentionally omitted from this public report.

## Upstream References Checked

- Unofficial `g0q` TWRP device tree and guide:
  `https://github.com/afaneh92/android_device_samsung_g0q`
- Raw guide:
  `https://raw.githubusercontent.com/afaneh92/android_device_samsung_g0q/github.io/README.md`
- AndroidFileHost `g0q` folder:
  `https://androidfilehost.com/?flid=334575&w=files`
- AndroidFileHost file ID for the TWRP tar:
  `https://androidfilehost.com/?fid=4279422670115701877`
- Official TeamWin Samsung device list:
  `https://twrp.me/Devices/Samsung/`

Important reference facts:

- The afaneh92 guide lists Galaxy S22 Plus Snapdragon `S906E`, `S906N`, and
  `S9060` as supported by the `g0q` build.
- The same guide instructs flashing TWRP in AP and `vbmeta_disabled.tar` in the
  Odin USERDATA slot, then booting directly to TWRP before Android can restore
  stock recovery.
- The guide also says encryption is not fully working and requires
  `multidisabler`, format data, and a recovery reboot for the old documented
  workflow.
- The official TeamWin Samsung list did not provide an official S22+ `g0q`
  entry during this check, so this is treated as an unofficial recovery.

## Pinned Local Artifacts

Full stock firmware:

- Path:
  `workspace/private/inputs/firmware/SAMFW.COM_SM-S906N_SKC_S906NKSS7FYG8_fac.zip`
- Size: `9.1G`
- SHA256:
  `f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8`

Stock boot-only rollback package, already live-tested during the chainload
rollback:

- Path:
  `workspace/private/outputs/s22plus_native_init/odin4_stock_rollback_short/AP.tar.md5`
- Size: `27M`
- SHA256:
  `1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e`

TWRP `g0q` tar:

- Path:
  `workspace/private/inputs/s22plus_twrp/g0q/twrp-3.7.0_12-1_afaneh92-g0q.tar`
- Size: `53M`
- SHA256:
  `0914c68a5353c367216805a3a2fdeb4982c6629368dc021c7fefc10d3d3bd034`
- MD5:
  `3e51917670648caf9135c9b6ef1bce0d`
- Tar contents:
  `recovery.img` (`55435280` bytes)

Extracted TWRP recovery image:

- Path:
  `workspace/private/inputs/s22plus_twrp/g0q/twrp-3.7.0_12-1_afaneh92-g0q.extract/recovery.img`
- Size: `53M`
- SHA256:
  `e4e1861760298da756d1d649029c33b4c953f12272ebda1705214da56245e036`
- MD5:
  `a0bdff72b49de2e010ce6b80b53e1125`
- `file`: Android boot image / recovery image
- Header:
  - boot magic: `ANDROID!`
  - header version: `2`
  - kernel size: `18881335`
  - ramdisk size: `31358693`
  - recovery dtbo size: `3465249`
  - dtb size: `1717704`
  - os version: `12.0.0`
  - os patch level: `2025-12`
  - product name: `SRPUI14B002`
  - cmdline includes `androidboot.selinux=permissive` and
    `buildvariant=eng`

`vbmeta_disabled.tar`:

- Path:
  `workspace/private/inputs/s22plus_twrp/g0q/vbmeta_disabled.tar`
- Size: `12K`
- SHA256:
  `0b347193ab3f822b423b2641001781e35fba0c932fcfb85d090b282d0fc6471b`
- Tar contents:
  `vbmeta.img` (`9936` bytes)

Stock recovery image:

- Path:
  `workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/extracted-images/raw/recovery.img`
- Size: `100M`
- SHA256:
  `93fac06ca79bf4b365b25a8d49902bc41aba112ea253c30880c90e314d7895d4`
- Header:
  - boot magic: `ANDROID!`
  - header version: `2`
  - kernel size: `41490944`
  - ramdisk size: `43597711`
  - recovery dtbo size: `7777237`
  - dtb size: `1721428`
  - os patch level: `2025-08`
  - product name: `SRPUJ22A007`

Stock vbmeta image:

- Path:
  `workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/extracted-images/raw/vbmeta.img`
- Size: `10K`
- SHA256:
  `1031323af6c69c6894bb00ca5895463ea3f00066ec4d5eacc2bb58b0b2c6047b`

Generated stock recovery-only rollback package:

- Path:
  `workspace/private/outputs/s22plus_twrp/stock_recovery_rollback/AP.tar.md5`
- SHA256:
  `8d3647313d2e100134f77984d13c7e5dc9946510ab57d8e34dd0cd192ca8586d`
- Contents:
  stock `recovery.img.lz4` from `S906NKSS7FYG8`
- Purpose:
  recovery-only rollback if a TWRP recovery flash is bad but download mode
  remains available.

## Odin4 Parse Gates

Linux Odin4 version:

`odin4 version 1.2.1-dc05e3ea`

The TWRP plus vbmeta-disabled inputs passed Odin4 package parsing when pointed
at an invalid USB device path:

```text
Check file : workspace/private/inputs/s22plus_twrp/g0q/twrp-3.7.0_12-1_afaneh92-g0q.tar
Check file : workspace/private/inputs/s22plus_twrp/g0q/vbmeta_disabled.tar
/dev/bus/usb/999/999
No such file or directory
usb device Fail
```

The stock recovery-only rollback package also passed Odin4 package parsing
against the same invalid USB device path:

```text
Check file : workspace/private/outputs/s22plus_twrp/stock_recovery_rollback/AP.tar.md5
/dev/bus/usb/999/999
No such file or directory
usb device Fail
```

Interpretation: package parsing reached the intentionally invalid transport
path. This is not a flash proof.

## Live Flash Gate

Live TWRP installation is not authorized under the current repo contract. The
current `AGENTS.md` safety invariant says device changes touch boot only and
forbids non-boot partition writes. TWRP setup would write at least recovery,
and the documented afaneh92 flow also writes vbmeta through the Odin USERDATA
slot.

Before any live TWRP setup from this repo, add an explicit narrow S22+ exception
that names:

1. Exact target device: `SM-S906N` / `g0q` / `S906NKSS7FYG8`.
2. Exact TWRP tar SHA256:
   `0914c68a5353c367216805a3a2fdeb4982c6629368dc021c7fefc10d3d3bd034`.
3. Exact `vbmeta_disabled.tar` SHA256:
   `0b347193ab3f822b423b2641001781e35fba0c932fcfb85d090b282d0fc6471b`.
4. Exact stock recovery rollback AP SHA256:
   `8d3647313d2e100134f77984d13c7e5dc9946510ab57d8e34dd0cd192ca8586d`.
5. Exact stock boot-only rollback AP SHA256:
   `1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e`.
6. Full stock firmware availability:
   `f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8`.
7. Linux Odin4 slot mapping review for `-u`, because the local Odin4 help
   calls it `UMS`, while the upstream guide describes the Windows Odin
   `USERDATA` slot.
8. Manual post-flash boot path: no auto reboot; after transfer, force reboot
   directly into recovery using the key combo.

## Proposed S22+ TWRP Install Unit After Exception

The first live unit should be recovery-infrastructure only, not mixed with any
native-init boot candidate.

Preconditions:

- ADB confirms the live device is still `SM-S906N`, `g0q`, `S906NKSS7FYG8`,
  unlocked, and orange.
- Download mode is reachable.
- Full stock firmware and both rollback AP packages above are present.
- Operator is ready for manual key combo immediately after Odin transfer.
- Operator accepts data/encryption impact. The guide may require format data.

Live sequence:

1. Reboot to download mode.
2. Flash TWRP tar and `vbmeta_disabled.tar` with auto-reboot disabled.
3. Manually force reboot directly into recovery.
4. Confirm TWRP screen and recovery ADB.
5. Run read-only checks first: `adb devices`, `adb shell uname -a`,
   `adb shell ls -l /dev/block/by-name`.
6. Stop before `multidisabler` or format data unless explicitly authorized as a
   second live step.
7. If TWRP fails and download mode is available, flash stock recovery-only AP.
8. If system boot is affected, use stock boot-only AP or the full stock
   firmware package as the deeper fallback.

## Result

Recovery infrastructure is materially closer:

- Exact unofficial `g0q` TWRP artifact is downloaded and pinned.
- Exact disabled vbmeta tar is pinned.
- Exact stock recovery rollback package is generated and Odin4-parse checked.
- Current device identity matches the intended model/build.
- The next unsafe action is clearly fenced: live recovery/vbmeta flashing waits
  for a repo-contract exception.


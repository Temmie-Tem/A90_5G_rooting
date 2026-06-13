# TWRP Recovery Teardown — A90 Device Reference (2026-06-13)

Device ground-truth mined host-only from the project's TWRP recovery image, for
reuse as **reference** by the native-init project. This is a metadata-only
summary (partition names, `/dev` node paths/perms, configfs recipe, hardware
bring-up sequence) — **no firmware, no ramdisk, no binaries, no secrets** are
committed.

## Provenance & scope

- Source: `workspace/private/inputs/firmware/twrp/recovery.img` (Android bootimg,
  82.8 MB; confirmed TWRP via `system/etc/twrp.flags`), unpacked host-side with
  `workspace/public/src/third_party/mkbootimg/unpack_bootimg.py` into the private
  scratch dir `tmp/twrp-unpack/` (not committed).
- Kernel cmdline (from header): `console=null androidboot.hardware=qcom
  androidboot.console=ttyMSM0 androidboot.memcg=1 lpm_levels.sleep_disabled=1
  video=vfb:64`.
- Platform: `ro.board.platform=msmnile` → **Snapdragon 855 / SM8150**.
- **Use as reference, reimplement in our C — do not lift.** TWRP is GPL/Apache and
  uses Android `init.rc` syntax + the property system + `qseecomd`; our PID1 native
  init has none of those, so these are *recipes to reimplement*, not copy-paste.

## 1. USB gadget configfs recipe (feeds the BadUSB / mass-storage breadth track)

From `init.recovery.usb.rc` + `init.recovery.qcom.rc`. Native init already drives a
NCM gadget, so adding HID (BadUSB) or mass_storage is mirroring this pattern.

- configfs mounted at `/config`; gadget root `/config/usb_gadget/g1`.
- Identity: `idVendor=0x04E8` (Samsung), `idProduct=0x6860`, `bcdDevice=0x0223`,
  `bcdUSB=0x0200`; strings under `strings/0x409` (`serialnumber=${ro.serialno}`, etc.).
- Functions created in recovery: `mass_storage.0`, `acm.0`, `ffs.adb`, `ffs.mtp`,
  `ffs.ptp` (each `mkdir functions/<name>`).
- Config: `configs/b.1`; a function is activated by `symlink functions/<fn>
  configs/b.1/fN` then writing the controller to `UDC`.
- Enable sequence: `setprop sys.usb.configfs 1`; `write
  /sys/class/udc/${ro.boot.usbcontroller}/device/../mode peripheral`; bind with
  `write /config/usb_gadget/g1/UDC ${ro.boot.usbcontroller}` (unbind = write
  `"none"` first).
- For **BadUSB**: add `functions/hid.0` (report desc + length), symlink into
  `configs/b.1`, bind UDC; write reports to the resulting `/dev/hidgN`. (HID gadget
  is compiled in: `CONFIG_USB_F_HID=y`, `CONFIG_USB_CONFIGFS_F_HID=y`.)

## 2. Partition map (safe-flash ground truth) — from `twrp.flags`

Discovery path: `wait /dev/block/platform/soc/${ro.boot.bootdevice}` then
`symlink … /dev/block/bootdevice`; partitions are
`/dev/block/bootdevice/by-name/<name>`.

| by-name | mount | fstype | note |
| --- | --- | --- | --- |
| boot | /boot | emmc | flashable (our target) |
| recovery | /recovery | emmc | TWRP lives here |
| dtbo | /dtbo | emmc | |
| system / vendor / product | … | ext4 | |
| userdata | /data | f2fs | **FBE encrypted** (see §4) |
| omr | /metadata | ext4 | vold metadata |
| cache | /cache | ext4 | |
| **efs / sec_efs** | … | ext4 | TWRP mounts **ro**; **NEVER WRITE** |
| **dsp** | /dsp | ext4 | DSP firmware; do not write |
| **keydata / keyrefuge** | … | ext4 | key material; do not write |
| **vbmeta_samsung / vbmeta_system** | … | emmc | verified boot; **NEVER WRITE** |
| **apnhlos** | /firmware | vfat | modem/HLOS firmware; do not write |
| misc | /misc | emmc | |
| external_sd / usb-otg | … | auto | `mmcblk0p1` / `sde1`, removable |

**Safety cross-reference:** this confirms the forbidden-partition set by exact
by-name (`efs`, `sec_efs`, `vbmeta_samsung`, `vbmeta_system`, `apnhlos`, `dsp`,
`keydata`, `keyrefuge`). These are **not** TWRP/download-mode recoverable =
permanent brick. Only `boot` is in scope for native-init flashing.

## 3. `/dev` node map (answers the "node absent under native init" problem)

From `system/etc/ueventd.rc` — canonical node paths + perms + subsystem→dir
mapping. Native init has no `ueventd`, so this is the reference for what to
`mknod`/where and the expected ownership.

- subsystem dirs: `graphics`→`/dev/graphics`, `drm`→`/dev/dri`, `input`→
  `/dev/input`, `sound`→`/dev/snd`, `dma_heap`→`/dev/dma_heap`.
- Arduino-ish primitives: `/dev/uhid` `0660 uhid uhid`, `/dev/uinput` `0660 uhid
  uhid`, `/dev/tun` `0660 system vpn`.
- Others: `/dev/binder` `0666`, `/dev/dri/*` `0666 root graphics`, `/dev/input/*`
  `0660 root input`, `/dev/snd/*` `0660 system audio`, `/dev/rtc0` `0640`,
  `/dev/pmsg0` `0222 root log`, `/dev/dma_heap/system` `0444`.
- Sysfs perms of note: `/sys/devices/system/cpu/cpu*/cpufreq/scaling_{max,min}_freq`
  `0664`, `/sys/devices/virtual/misc/uhid/*/leds/*` brightness `0664`.

## 4. Misc reusable facts

- **Backlight:** `/sys/class/backlight/panel0-backlight/brightness` (recovery writes
  `200` at init) — display brightness control path.
- **FBE on /data:** `fileencryption=aes-256-xts:aes-256-cts:v2+inlinecrypt_optimized+wrappedkey_v0`,
  `metadata_encryption=aes-256-xts:wrappedkey_v0`,
  `keydirectory=/metadata/vold/metadata_encryption`. `wrappedkey_v0` = **hardware-
  wrapped keys (Qualcomm ICE/TEE)** → reading /data needs KeyMaster/TEE cooperation
  (`/dev/qseecom`, `qseecomd`, `prepdecrypt`). This is a **hard wall + bumps the
  "never touch keymaster" safety line** → reference only, not a cheap win.
- **Filesystem tools TWRP bundles** (reference for capability, not lifted):
  `sgdisk`, `e2fsck`, `resize2fs`, `fsck.f2fs`, `fsck.exfat`, `fsck.ntfs`,
  `mkfs.fat`, `mkfs.ntfs`, `dd`.

## 5. Vein status / next dig

The **recovery ramdisk is fully mined.** Peripheral-specific configs (audio
`mixer_paths*`, sensor reg maps, haptics calibration, thermal-engine config) are
**not** in the recovery image — `vendor/etc` and `odm/etc` in the ramdisk are stubs
populated at runtime from the real partitions. To get those, the next dig is the
**stock firmware vendor/odm images** under
`workspace/private/inputs/firmware/SAMFW.COM_SM-A908N_…_fac` (separate, larger
artifact). That is where the haptics/flash-LED/sensor node specifics for the
peripheral breadth track live.

## Relation to current plan

This teardown is **reference for the peripheral/USB-gadget breadth track**, not a
queued work item. The active queued epic remains E1/E2 (WLAN nl80211 / rtnetlink
events) per `GOAL.md`. Strongest immediate reuse: §1 (USB gadget recipe → BadUSB),
§3 (node map → materialize peripheral nodes), §2 (safety partition map).

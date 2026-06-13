# Native Init V2322 USB Named LUN Identity Live Validation

## Summary

- Cycle: `V2322`
- Track: named multi-LUN mass-storage identity, unit U-A single named LUN.
- Type: rollbackable boot-only native-init live validation.
- Decision: `v2322-usb-named-lun-identity-live-pass-stop-for-u-b`
- Result: PASS
- Resident init after validation: `A90 Linux init 0.9.286 (v2322-usb-named-lun-identity)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2322_usb_named_lun_identity.img`
- Boot SHA256: `81355888b6b19407c76463ee8d5ca045fd0f17294c3329ceda0afc1ab2a36f53`
- Rollback checkpoint retained: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Deeper Wi-Fi-proven fallback retained: `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
- Deeper fallback SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`

## Patch Under Test

- Parent USB descriptor identity is unchanged from V2321: host descriptor remains `A90-LNX` / `A90 Linux ARM64` / `A90NATIVE001`.
- `mass_storage.0/lun.0/inquiry_string`: exact 28-byte SCSI INQUIRY identity `A90-LNX A90-INTERNAL    0001`.
- Host-visible SCSI vendor: `A90-LNX`.
- Host-visible SCSI model/product: `A90-INTERNAL`.
- Host-visible SCSI revision: `0001`.
- Backing file: `/cache/a90-usb-mass-storage-v2322-internal.img`.
- Backing format: file-backed read-only FAT16 superfloppy image.
- FAT volume label: `A90INTERNAL`.
- Backing size: `8388608` bytes.
- U-B multi-LUN and U-C real SD/internal exposure are not included.

## Flash Gate

- Pre-flash resident baseline: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`.
- Pre-flash rollback image check: V2321 image present with expected SHA256.
- Deeper fallback check: V2237 image present with expected SHA256; `boot_linux_v48.img` present.
- Pre-flash health: `version/status/selftest` reachable over the serial bridge; `selftest fail=0`.
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Pinned candidate SHA256: `81355888b6b19407c76463ee8d5ca045fd0f17294c3329ceda0afc1ab2a36f53`.
- Local image SHA256: matched pinned SHA256.
- Remote pushed image SHA256: matched pinned SHA256.
- Boot partition readback prefix SHA256: matched pinned SHA256.
- Post-flash native-init verification: `version/status` passed.
- No rollback was needed.

## Health Check

- `version`: `A90 Linux init 0.9.286 (v2322-usb-named-lun-identity)`.
- `status`: boot OK, transport ready, storage ready, `selftest fail=0`.
- `selftest verbose`: `pass=11 warn=1 fail=0`.
- One immediate serial read during early post-boot selftest was truncated before the protocol END marker; a retry returned a valid `fail=0` result. This was treated as a transient serial framing issue, not a device health failure.

## Device-Side USB Validation

Initial `usb status` after boot:

- `gadget.bound=1`.
- `idVendor=0x04e8`.
- `idProduct=0x6861`.
- `ncm.usb0` linked as control NCM.
- `acm.usb0` linked as control ACM.
- `control.ok=1`.
- No mass-storage link active before `expose`.

`usb mass-storage expose`:

- Command accepted and scheduled the expected USB disconnect/re-enumeration window.
- Persona: `readonly-backing`.
- Backing file reported: `/cache/a90-usb-mass-storage-v2322-internal.img`.
- Backing bytes reported: `8388608`.
- After re-enumeration, `usb status` returned over the serial bridge with `mass_storage.0` linked alongside `ncm.usb0` and `acm.usb0`.
- Device-side status reported `mass_storage.inquiry.vendor=A90-LNX`, `mass_storage.inquiry.product=A90-INTERNAL`, `mass_storage.inquiry.revision=0001`, and `mass_storage.volume_label=A90INTERNAL`.

`usb mass-storage remove`:

- Command accepted and scheduled the expected USB disconnect/re-enumeration window.
- One status read during re-enumeration was truncated; a retry after settle returned a complete protocol response.
- Final `usb status` showed `mass_storage.0 linked=0`, `file.present=0`, and `control.ok=1` with NCM+ACM still linked.
- Final host block-device listing no longer showed the 8 MiB USB disk.
- Final `selftest verbose`: `pass=11 warn=1 fail=0`.

## Host-Side Identity Validation

Host validation was run on the attached Linux host after `usb mass-storage expose`.

`lsblk -S` showed:

- USB disk transport: `usb`.
- SCSI vendor: `A90-LNX`.
- SCSI model: `A90-INTERNAL`.
- Placeholder serial: `A90NATIVE001`.
- Size: `8M`.
- State: `running`.

`lsblk` block view showed:

- Model: `A90-INTERNAL`.
- Label: `A90INTERNAL`.
- Filesystem: `vfat`.
- Size: `8M`.
- Read-only flag: `1`.

Interpretation: U-A proves both required naming layers live on the host: per-LUN SCSI INQUIRY model `A90-INTERNAL` and FAT volume label `A90INTERNAL`.

## Safety Scope

- Boot partition only.
- Flash path was only `native_init_flash.py` with pinned SHA and readback verification.
- V2321 rollback checkpoint retained; V2237/v48 fallbacks retained.
- Backing storage is a generated `/cache` file-backed read-only FAT image only.
- No real `/data`, internal partition, SD raw block, forbidden partition, Wi-Fi scan/connect/DHCP/ping, adb-over-ffs, HID, BadUSB, modem, PMIC, GPIO, GDSC, PCIe, or eSoC work.
- No credentials, raw logs, or unredacted hardware identifiers are committed.

## Next Unit

Stop after U-A as required. The next named-LUN unit is U-B: add `lun.1` as another file-backed read-only image with SCSI model `A90-SD` and FAT label `A90SD`, while preserving the already-validated parent descriptor and U-A `A90-INTERNAL` behavior.

## Conclusion

V2322 completes U-A. The device boots, health checks pass, the control channel survives expose/remove, and the host sees the single read-only file-backed LUN as `A90-INTERNAL` with FAT label `A90INTERNAL`. V2321 remains the rollback checkpoint until an explicit baseline promotion decision.

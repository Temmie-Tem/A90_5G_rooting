# Native Init V2318 USB Full Identity Rodata Live Validation

## Summary

- Cycle: `V2318`
- Track: USB identity follow-up after V2317 product rodata validation.
- Type: rollbackable boot-only native-init live validation.
- Decision: `v2318-usb-full-identity-rodata-live-pass`
- Result: PASS
- Resident init after validation: `A90 Linux init 0.9.282 (v2318-usb-full-identity-rodata)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2318_usb_full_identity_rodata.img`
- Boot SHA256: `d3b22893763482f554abdb2bdab03d8e7a15d9186a15dd7b56482646c23a05b3`
- Rollback target retained: `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
- Rollback target SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`

## Patch Under Test

- Source kernel SHA256: `9f4fc72c15ce9f96694023cf8f3f0340651d073acd584853941764cf9756b85a`
- Patched kernel SHA256: `b8c9181a134d419a35935cd7ec601769bd45416c284f5b2de5c4a293210793e2`
- Product patch: `SAMSUNG_Android` -> `A90 Linux ARM` at offset `0x233c11e`
- Manufacturer patch: `SAMSUNG` -> `A90-LNX` at offset `0x2346d6c`
- Constraint: fixed-length rodata replacement only; no section-size, branch, code-flow, VID/PID, or command-behavior change.
- Known collateral accepted for this test: the merged rodata suffix `Gamepad for SAMSUNG` becomes `Gamepad for A90-LNX`.

## Flash Gate

- Pre-flash resident baseline: `A90 Linux init 0.9.281 (v2317-usb-product-rodata)`.
- Pre-flash `selftest`: `pass=11 warn=1 fail=0`.
- Rollback image check: v2237 image present with expected SHA256.
- Deeper fallback: `workspace/private/inputs/boot_images/boot_linux_v48.img` present.
- Recovery path: TWRP recovery path confirmed from the repository flash guide and used by the checked flash helper.
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Local image SHA256: matched expected `d3b22893763482f554abdb2bdab03d8e7a15d9186a15dd7b56482646c23a05b3`.
- Remote pushed image SHA256: matched expected SHA256.
- Boot partition readback prefix SHA256: matched expected SHA256.
- Post-flash native-init verification: `version/status` passed.

## Health Check

- `version`: `A90 Linux init 0.9.282 (v2318-usb-full-identity-rodata)`.
- `status`: boot OK, transport ready, storage ready, `selftest fail=0`.
- Final `selftest verbose`: `pass=11 warn=1 fail=0`.
- No rollback was needed.

## USB Identity Result

Host-visible descriptor after boot:

- `iManufacturer`: `A90-LNX`
- `iProduct`: `A90 Linux ARM`
- `iSerial`: `A90NATIVE001`

Device-side configfs strings remain the V2316 userspace values:

- `strings.manufacturer=A90 NativeInit`
- `strings.product=A90 Linux (ARM)`
- `strings.serialnumber.redacted=1`

Interpretation: V2317 proved the product literal was live; V2318 proves the fixed-length manufacturer literal is also live and host-visible.

## USB Control Surface Smoke

Initial `usb status` after boot:

- `gadget.bound=1`
- `idVendor=0x04e8`
- `idProduct=0x6861`
- `config.0.link_count=2`
- `ncm.usb0` linked as control NCM.
- `acm.usb0` linked as control ACM.
- `control.ok=1`

Mass-storage expose:

- Command accepted and scheduled as read-only persona.
- `usb status` after settle showed `mass_storage.0` linked as aux `f3` while `ncm.usb0` and `acm.usb0` remained present.
- Host observed an 8 MiB read-only USB disk with model `File-Stor Gadget` and vendor string reflecting the new manufacturer identity.
- `control.ok=1` after expose.

Mass-storage remove:

- Command accepted and scheduled.
- Final `usb status` after settle showed `mass_storage.0 linked=0`, `file.present=0`, and `control.ok=1`.
- Host block-device listing no longer showed the 8 MiB USB disk.
- Host descriptor remained `A90-LNX` / `A90 Linux ARM` / `A90NATIVE001`.

Observed transient: one `usb status` query immediately after USB re-enumeration had a truncated protocol response / serial text corruption. Retrying after the control channel settled returned a complete valid status. This matches the expected USB re-enumeration window and did not leave the device without control.

## Scope Guard

- Boot partition only.
- No forbidden partition writes.
- No adb-over-ffs, HID, BadUSB, Wi-Fi scan/connect/DHCP/ping, modem, PMIC, GPIO, GDSC, PCIe, or eSoC work.
- No credentials or raw logs committed.
- Generated boot image and build products remain under `workspace/private/`.

## Conclusion

V2318 validates the next fixed-length USB kernel identity patch. The host-visible USB identity is now fully controlled for the tested strings (`iManufacturer=A90-LNX`, `iProduct=A90 Linux ARM`, redacted serial preserved), while the V2313-V2315 USB runtime control surface and mass-storage persona still return to a safe NCM+ACM control topology.

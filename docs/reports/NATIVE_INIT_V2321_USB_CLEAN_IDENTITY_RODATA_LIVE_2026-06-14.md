# Native Init V2321 USB Clean Identity Rodata Live Validation

## Summary

- Cycle: `V2321`
- Track: USB identity checkpoint after V2319/V2320 bounded-overrun experiments.
- Type: rollbackable boot-only native-init live validation and checkpoint promotion.
- Decision: `v2321-usb-clean-identity-rodata-live-pass-promote-rollback`
- Result: PASS
- Resident init after validation: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Boot SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- New rollback/checkpoint target: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Deeper Wi-Fi-proven fallback retained: `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
- Deeper fallback SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`

## Patch Under Test

- Source kernel SHA256: `9f4fc72c15ce9f96694023cf8f3f0340651d073acd584853941764cf9756b85a`
- Patched kernel SHA256: `d97eb6c7291477000299fae1c4272105e95fe77df09631ae13099303510b5263`
- Product patch: `SAMSUNG_Android\0` -> `A90 Linux ARM64\0` at offset `0x233c11e`.
- Product old length: `16` bytes including NUL.
- Product new length: `16` bytes including NUL.
- Adjacent bytes after product slot: `0x01 0x33` retained; the USB configfs `KERN_ERR` log prefix damaged by V2320 is restored.
- Manufacturer patch retained from V2318: `SAMSUNG` -> `A90-LNX` at offset `0x2346d6c`.
- Known manufacturer collateral retained: the merged rodata suffix `Gamepad for SAMSUNG` becomes `Gamepad for A90-LNX`.
- Constraint: byte overwrite only; no section-size, branch, code-flow, VID/PID, command-behavior, adb-over-ffs, HID, BadUSB, Wi-Fi, modem, PMIC, GPIO, GDSC, PCIe, or eSoC change.

## Flash Gate

- Pre-flash resident baseline: `A90 Linux init 0.9.284 (v2320-usb-product-overrun2-rodata)`.
- Pre-flash `status`: boot OK, transport ready, storage ready, `selftest fail=0`.
- Rollback image check before flash: v2237 image present with expected SHA256.
- Deeper fallback: `workspace/private/inputs/boot_images/boot_linux_v48.img` present.
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Local image SHA256: matched expected `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Remote pushed image SHA256: matched expected SHA256.
- Boot partition readback prefix SHA256: matched expected SHA256.
- Post-flash native-init verification: `version/status` passed.

## Health Check

- `version`: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`.
- `status`: boot OK, transport ready, storage ready, `selftest fail=0`.
- Final `selftest verbose`: `pass=11 warn=1 fail=0`.
- No rollback was needed.

## USB Identity Result

Host-visible descriptor after boot:

- `iManufacturer`: `A90-LNX`
- `iProduct`: `A90 Linux ARM64`
- `iSerial`: `A90NATIVE001`

Device-side configfs strings remain userspace-controlled and unchanged from V2316:

- `strings.manufacturer=A90 NativeInit`
- `strings.product=A90 Linux (ARM)`
- `strings.serialnumber.redacted=1`

Interpretation: V2321 restores the product patch to a fixed-length replacement while preserving the desired host-visible identity.

## USB Control Surface Smoke

Initial `usb status` after boot:

- `gadget.bound=1`
- `idVendor=0x04e8`
- `idProduct=0x6861`
- `ncm.usb0` linked as control NCM.
- `acm.usb0` linked as control ACM.
- `control.ok=1`

Mass-storage expose:

- Command accepted and scheduled as read-only persona.
- Host observed an 8 MiB read-only USB disk with model `File-Stor Gadget` and vendor string `A90-LNX`.
- Host descriptor remained `A90-LNX` / `A90 Linux ARM64` / `A90NATIVE001` after re-enumeration.

Mass-storage remove:

- Command accepted and scheduled; one immediate serial response was partially truncated during the expected re-enumeration window.
- Host block-device listing no longer showed the 8 MiB USB disk after removal.
- Final settled `usb status` showed `mass_storage.0 linked=0`, `file.present=0`, and `control.ok=1`.
- Final host descriptor remained `A90-LNX` / `A90 Linux ARM64` / `A90NATIVE001`.

## Promotion Decision

V2321 is promoted as the current clean USB-identity baseline and rollback/checkpoint target because it preserves the desired host-visible identity without product-slot overrun or adjacent configfs log-string damage. V2237 remains documented as the deeper Wi-Fi-proven fallback.

## Scope Guard

- Boot partition only.
- No forbidden partition writes.
- No adb-over-ffs, HID, BadUSB, Wi-Fi scan/connect/DHCP/ping, modem, PMIC, GPIO, GDSC, PCIe, or eSoC work.
- No credentials or raw logs committed.
- Generated boot image and build products remain under `workspace/private/`.

## Conclusion

V2321 validates and promotes the clean fixed-length USB identity checkpoint. The device boots, health checks pass, host-visible identity is `A90-LNX` / `A90 Linux ARM64` / `A90NATIVE001`, and the existing USB control/mass-storage path still returns to a safe NCM+ACM topology after re-enumeration. This is the new current rollback/checkpoint target; v2237 remains the deeper fallback.

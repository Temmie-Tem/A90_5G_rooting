# Native Init V2319 USB Product Overrun+1 Rodata Live Validation

## Summary

- Cycle: `V2319`
- Track: USB identity boundary follow-up after V2318 full fixed-length identity validation.
- Type: rollbackable boot-only native-init live validation.
- Decision: `v2319-usb-product-overrun1-rodata-live-pass`
- Result: PASS
- Resident init after validation: `A90 Linux init 0.9.283 (v2319-usb-product-overrun1-rodata)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2319_usb_product_overrun1_rodata.img`
- Boot SHA256: `24f5a99e1c3f0d362f4b49cbc72ded9b12e10aa44d69133c9088091866c9b723`
- Rollback target retained: `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
- Rollback target SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`

## Patch Under Test

- Source kernel SHA256: `9f4fc72c15ce9f96694023cf8f3f0340651d073acd584853941764cf9756b85a`
- Patched kernel SHA256: `57970cce25cda972303d5efdb6f2d41b19dc2938dc5b354beb37eda53a33986c`
- Product patch: `SAMSUNG_Android\0` -> `A90 Linux ARM64X\0` at offset `0x233c11e`
- Product old length: `16` bytes including NUL.
- Product new length: `17` bytes including NUL.
- Bounded adjacent overwrite: one byte after the old slot changed from `0x01` to `0x00`.
- Manufacturer patch retained from V2318: `SAMSUNG` -> `A90-LNX` at offset `0x2346d6c`.
- Known manufacturer collateral retained: the merged rodata suffix `Gamepad for SAMSUNG` becomes `Gamepad for A90-LNX`.
- Constraint: byte overwrite only; no section-size, branch, code-flow, VID/PID, or command-behavior change.

## Flash Gate

- Pre-flash resident baseline: `A90 Linux init 0.9.282 (v2318-usb-full-identity-rodata)`.
- Pre-flash `selftest`: `pass=11 warn=1 fail=0`.
- Rollback image check: v2237 image present with expected SHA256.
- Deeper fallback: `workspace/private/inputs/boot_images/boot_linux_v48.img` present.
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Local image SHA256: matched expected `24f5a99e1c3f0d362f4b49cbc72ded9b12e10aa44d69133c9088091866c9b723`.
- Remote pushed image SHA256: matched expected SHA256.
- Boot partition readback prefix SHA256: matched expected SHA256.
- Post-flash native-init verification: `version/status` passed.

## Health Check

- `version`: `A90 Linux init 0.9.283 (v2319-usb-product-overrun1-rodata)`.
- `status`: boot OK, transport ready, storage ready, `selftest fail=0`.
- Final `selftest verbose`: `pass=11 warn=1 fail=0`.
- No rollback was needed.

## USB Identity Result

Host-visible descriptor after boot:

- `iManufacturer`: `A90-LNX`
- `iProduct`: `A90 Linux ARM64X`
- `iSerial`: `A90NATIVE001`

Device-side configfs strings remain userspace-controlled and unchanged from V2316:

- `strings.manufacturer=A90 NativeInit`
- `strings.product=A90 Linux (ARM)`
- `strings.serialnumber.redacted=1`

Interpretation: the USB product descriptor path accepts a 16-character product string even though that requires a one-byte NUL terminator overwrite past the original 16-byte stock product literal slot.

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
- The expected USB re-enumeration window produced one truncated serial protocol response, but the control channel recovered without manual intervention.

Mass-storage remove:

- Command accepted and scheduled.
- Host block-device listing no longer showed the 8 MiB USB disk.
- Final settled `usb status` showed `mass_storage.0 linked=0`, `file.present=0`, and `control.ok=1`.
- Final host descriptor remained `A90-LNX` / `A90 Linux ARM64X` / `A90NATIVE001`.

## Scope Guard

- Boot partition only.
- No forbidden partition writes.
- No adb-over-ffs, HID, BadUSB, Wi-Fi scan/connect/DHCP/ping, modem, PMIC, GPIO, GDSC, PCIe, or eSoC work.
- No credentials or raw logs committed.
- Generated boot image and build products remain under `workspace/private/`.

## Conclusion

V2319 validates the smallest product-string overrun boundary. The device boots, health checks pass, host-visible `iProduct` becomes `A90 Linux ARM64X`, and the existing USB control/mass-storage path still returns to a safe NCM+ACM topology after re-enumeration.

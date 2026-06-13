# Native Init V2319 USB Product Overrun+1 Rodata Source Build

## Summary

- Cycle: `V2319`
- Track: USB identity follow-up after V2318 proved full fixed-length identity patching works.
- Type: source/build-only rollbackable native-init test boot.
- Decision: `v2319-usb-product-overrun1-rodata-source-build-pass`
- Result: PASS
- Reason: live-test the smallest product-string rodata overrun while the operator is present for manual TWRP recovery if needed.
- Manifest: `workspace/private/builds/native-init/v2319-usb-product-overrun1-rodata/manifest.json`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2319_usb_product_overrun1_rodata.img`
- Boot SHA256: `24f5a99e1c3f0d362f4b49cbc72ded9b12e10aa44d69133c9088091866c9b723`
- Init: `A90 Linux init 0.9.283 (v2319-usb-product-overrun1-rodata)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Product Overrun+1 Rodata Patch

- Source kernel SHA256: `9f4fc72c15ce9f96694023cf8f3f0340651d073acd584853941764cf9756b85a`
- Patched kernel SHA256: `57970cce25cda972303d5efdb6f2d41b19dc2938dc5b354beb37eda53a33986c`
- Product offset: `0x233c11e`
- Old product: `SAMSUNG_Android`.
- New product: `A90 Linux ARM64X`.
- Product replacement length delta: `1` byte.
- Bounded adjacent overwrite: `0x01 -> 0x00`.
- Manufacturer offset: `0x2346d6c`
- Old manufacturer: `SAMSUNG`.
- New manufacturer: `A90-LNX`.
- Known collateral: `Gamepad for SAMSUNG suffix becomes Gamepad for A90-LNX`.
- Constraint: byte overwrite only; no section-size, code-layout, branch, VID/PID, or command-behavior change.

## Why Product Overrun+1 Next

- The product literal is unique in the extracted V2316 kernel blob.
- V2317 proved the product rodata patch is live and rollbackable.
- V2318 proved the manufacturer fixed-length patch is also live and rollbackable.
- The next smallest boundary test is a product string one byte longer than the original 16-byte slot.
- The only intentionally overwritten adjacent byte is the next rodata byte after the product slot (`0x01` to `0x00`).
- Expected host descriptor after live boot: `iManufacturer=A90-LNX`, `iProduct=A90 Linux ARM64X`, `iSerial=A90NATIVE001`.

## Command Scope

- No USB control-surface behavior change. Inherits V2313-V2315 (`usb status`, `usb mass-storage add/remove/expose`) and V2316 serial redaction/userspace configfs identity.
- Keeps `idVendor=0x04e8` and `idProduct=0x6861` for host transport compatibility.

## Helper Flags

- `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1`
- `-DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1`
- `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`

## Safety Scope

This source build performed host-side build work only. It changes the product rodata identity string with a bounded one-byte overrun, keeps the V2318 fixed-length manufacturer replacement, and bumps the native-init run/build identity. It does not change command behavior, USB VID/PID, partitions, adb-over-ffs, HID, BadUSB, Wi-Fi, kernel code flow, or any forbidden subsystem.

## Required Device Step

- Boot-only flash through `native_init_flash.py`, pinned SHA, auto-rollback to `v2237` on any failure.
- `version` / `status` / `selftest fail=0`.
- `usb status`: `control.ok=1`, configfs strings still show V2316 userspace identity.
- Host descriptor validation: `iManufacturer=A90-LNX`, `iProduct=A90 Linux ARM64X`, `iSerial=A90NATIVE001`.
- USB persona smoke: `usb mass-storage expose` then `remove`; confirm serial control returns and NCM+ACM remain present.

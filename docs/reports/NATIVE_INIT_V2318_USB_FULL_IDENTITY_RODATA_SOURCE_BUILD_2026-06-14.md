# Native Init V2318 USB Full Identity Rodata Source Build

## Summary

- Cycle: `V2318`
- Track: USB identity follow-up after V2317 proved product rodata patching works.
- Type: source/build-only rollbackable native-init test boot.
- Decision: `v2318-usb-full-identity-rodata-source-build-pass`
- Result: PASS
- Reason: live-test the next fixed-length identity string, accepting the known manufacturer collateral suffix risk explicitly.
- Manifest: `workspace/private/builds/native-init/v2318-usb-full-identity-rodata/manifest.json`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2318_usb_full_identity_rodata.img`
- Boot SHA256: `d3b22893763482f554abdb2bdab03d8e7a15d9186a15dd7b56482646c23a05b3`
- Init: `A90 Linux init 0.9.282 (v2318-usb-full-identity-rodata)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Full Identity Rodata Patch

- Source kernel SHA256: `9f4fc72c15ce9f96694023cf8f3f0340651d073acd584853941764cf9756b85a`
- Patched kernel SHA256: `b8c9181a134d419a35935cd7ec601769bd45416c284f5b2de5c4a293210793e2`
- Product offset: `0x233c11e`
- Old product: `SAMSUNG_Android`.
- New product: `A90 Linux ARM`.
- Manufacturer offset: `0x2346d6c`
- Old manufacturer: `SAMSUNG`.
- New manufacturer: `A90-LNX`.
- Known collateral: `Gamepad for SAMSUNG suffix becomes Gamepad for A90-LNX`.
- Constraint: fixed-length replacement only; no section-size or code-layout change.

## Why Fixed-Length Manufacturer Next

- The product literal is unique in the extracted V2316 kernel blob.
- V2317 proved the product rodata patch is live and rollbackable.
- V2318 patches the manufacturer literal with the same fixed-length method to test the remaining simple identity string.
- The manufacturer literal is known to be merged with an unrelated rodata suffix, so this build intentionally documents that collateral instead of treating it as a surprise.
- Expected host descriptor after live boot: `iManufacturer=A90-LNX`, `iProduct=A90 Linux ARM`, `iSerial=A90NATIVE001`.

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

This source build performed host-side build work only. It changes only two fixed-length kernel rodata identity literals and the native-init run/build identity. It does not change command behavior, USB VID/PID, partitions, adb-over-ffs, HID, BadUSB, Wi-Fi, kernel code flow, or any forbidden subsystem.

## Required Device Step

- Boot-only flash through `native_init_flash.py`, pinned SHA, auto-rollback to `v2237` on any failure.
- `version` / `status` / `selftest fail=0`.
- `usb status`: `control.ok=1`, configfs strings still show V2316 userspace identity.
- Host descriptor validation: `iManufacturer=A90-LNX`, `iProduct=A90 Linux ARM`, `iSerial=A90NATIVE001`.
- USB persona smoke: `usb mass-storage expose` then `remove`; confirm serial control returns and NCM+ACM remain present.

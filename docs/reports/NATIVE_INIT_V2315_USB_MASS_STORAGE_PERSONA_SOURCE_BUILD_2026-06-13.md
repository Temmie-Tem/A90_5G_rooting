# Native Init V2315 USB Mass Storage Persona Source Build

## Summary

- Cycle: `V2315`
- Track: active USB gadget runtime-control epic layer 1, U3 first persona end-to-end.
- Type: source/build-only rollbackable native-init test boot.
- Decision: `v2315-usb-ms-persona-source-build-pass`
- Result: PASS
- Reason: U3 needs a bounded mass-storage persona with an explicit read-only backing file and control-return validation.
- Manifest: `workspace/private/builds/native-init/v2315-usb-ms-persona/manifest.json`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2315_usb_ms_persona.img`
- Boot SHA256: `49d21d98dc75d73277d2c690ed389e75ac2c4d18ae14ae42cda7c38bd92ac0cf`
- Init: `A90 Linux init 0.9.279 (v2315-usb-ms-persona)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Command Scope

- Keeps `usb status`, `usb mass-storage add`, and `usb mass-storage remove`.
- Adds `usb mass-storage expose`, which creates a bounded read-only backing image under `/cache` and exposes it through `mass_storage.0`.
- The backing image is 8 MiB, contains a visible V2315 marker at offset 0, and is configured read-only before the LUN file is opened.
- `usb mass-storage remove` now also clears the LUN file attribute while the gadget is unbound, returning the function to no-medium state.
- Reconfigure still uses the V2314 detached worker, NCM+ACM preservation, watchdog, and known-good restore path.

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Parent test artifact: `v2314-usb-ms-reconfigure`.
- Rollback checkpoint remains: `v2237-supplicant-terminate-poll`.

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

This source build performed host-side build work only. Runtime mutation is limited to the U3 mass-storage persona command and the existing guarded add/remove path. The persona uses a generated read-only `/cache` file only; it does not touch partitions, credentials, Wi-Fi scan/connect/DHCP/ping, adb-over-ffs, HID, or BadUSB.

## Required Device Step

- Boot-only flash through `native_init_flash.py`.
- `version` / `status` / `selftest fail=0`.
- Run `usb status` over the serial bridge and verify `control.ok=1` before mutation.
- Run `usb mass-storage expose`; reconnect through the serial bridge after the expected USB drop and verify `mass_storage.0` is linked, `mass_storage.file.present=1`, the backing path is `/cache/a90-usb-mass-storage-v2315.img`, `ro=1`, and `control.ok=1`.
- Host-side enumeration is required for full U3 persona validation and remains an operator parked checkpoint if not available in the automated run.
- Run `usb mass-storage remove`; reconnect and verify `control.ok=1`, no active mass-storage config link, and `mass_storage.file.present=0`.

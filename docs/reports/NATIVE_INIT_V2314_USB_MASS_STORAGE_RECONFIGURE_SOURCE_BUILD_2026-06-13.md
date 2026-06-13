# Native Init V2314 USB Mass Storage Reconfigure Source Build

## Summary

- Cycle: `V2314`
- Track: active USB gadget runtime-control epic layer 1, U2 atomic auxiliary-function add/remove.
- Type: source/build-only rollbackable native-init test boot.
- Decision: `v2314-usb-ms-reconfigure-source-build-pass`
- Result: PASS
- Reason: U2 must add/remove an auxiliary `mass_storage.0` function without ever shipping a config that lacks NCM plus control ACM.
- Manifest: `workspace/private/builds/native-init/v2314-usb-ms-reconfigure/manifest.json`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2314_usb_ms_reconfigure.img`
- Boot SHA256: `0ad0c5eb29e8ddf8a34a906d4a0107104f51880eb1d4d736866e78bb0f289022`
- Init: `A90 Linux init 0.9.278 (v2314-usb-ms-reconfigure)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Command Scope

- Keeps `usb [status]` and adds `usb mass-storage add` / `usb mass-storage remove`.
- The mass-storage commands preflight that the live gadget is already bound with `acm.usb0` on `f1` and `ncm.usb0` on `f2`.
- They schedule a detached device-side worker so the command can return before the expected USB disconnect.
- The worker performs one atomic unbind -> reconfigure -> rebind cycle and always preserves `acm.usb0` plus `ncm.usb0`.
- A separate watchdog process restores the known-good control-only gadget if the worker does not mark completion within the bounded window.
- `mass_storage.0` is configured as a removable no-media LUN; no backing file is exposed in U2.

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Parent test artifact: `v2313-usb-status-inventory`.
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

This source build performed host-side build work only. Runtime mutation is limited to the new U2 commands and is guarded by preflight, detached worker, watchdog restore, and mandatory NCM+ACM preservation. It does not expose a backing file, run Wi-Fi scan/connect/DHCP/ping, touch forbidden partitions, or start adb-over-ffs/HID/BadUSB work.

## Required Device Step

- Boot-only flash through `native_init_flash.py`.
- `version` / `status` / `selftest fail=0`.
- Run `usb status` over the serial bridge and verify `control.ok=1` before mutation.
- Run `usb mass-storage add`; reconnect through the serial bridge after the expected USB drop and verify `usb status` shows `mass_storage.0` linked as an aux function while `control.ok=1` remains true.
- Run `usb mass-storage remove`; reconnect again and verify `control.ok=1` and no active mass-storage config link.
- Host-side enumeration is parked as an operator checkpoint for U2/U3; the automated pass criterion is serial control return plus topology state.

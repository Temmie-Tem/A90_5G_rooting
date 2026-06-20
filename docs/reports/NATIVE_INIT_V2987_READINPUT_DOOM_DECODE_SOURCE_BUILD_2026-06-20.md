# Native Init V2987 Readinput DOOM Decode Source Build

## Summary

- Cycle: `V2987`
- Track: active Video playback / DOOM input prerequisite.
- Decision: `v2987-readinput-doom-decode-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2987_readinput_doom_decode.img`
- Boot SHA256: `fc5d680be0b6575ea4650a4e84a2ee7f0620cc02693e77b5f4453f44f9ffad21`
- Init: `A90 Linux init 0.10.64 (v2987-readinput-doom-decode)`
- Parent candidate: `v2985-doom-keyboard-caps`.

## Branch Evidence

- V2984 proved the touch nodes expose MT capability bits and are not runtime-PM suspended.
- V2985 added DOOM keyboard fallback capability bits, and V2986 staged the exact live keyboard handoff.
- A USB keyboard is not currently enumerated on v2321, so this source unit improves the shared `readinput` evidence surface without flashing.

## Included Delta

- Keeps the existing numeric `event N: type=0x.... code=0x.... value=...` line unchanged for host parser compatibility.
- Adds a second `event.decode N: type=... code=... role=... value=...` line for each captured evdev event.
- Decodes multitouch protocol-B landmarks: `ABS_MT_SLOT`, `ABS_MT_TRACKING_ID`, `ABS_MT_POSITION_X`, `ABS_MT_POSITION_Y`, `BTN_TOUCH`, and `SYN_REPORT`.
- Decodes DOOM fallback keyboard roles for WASD, arrow keys, Enter/Space, Ctrl, Shift, and Esc.
- Adds no input injection, evdev grabs, keymap changes, touch configuration, or sysfs writes.

## Marker Check

- `A90 Linux init 0.10.64 (v2987-readinput-doom-decode)`
- `readinput <eventX> [count] [timeout_ms]`
- `event.decode %d: type=%s code=%s role=%s value=%d`
- `ABS_MT_SLOT`
- `ABS_MT_TRACKING_ID`
- `ABS_MT_POSITION_X`
- `ABS_MT_POSITION_Y`
- `BTN_TOUCH`
- `SYN_REPORT`
- `doom_forward`
- `doom_back`
- `doom_left`
- `doom_right`
- `doom_use`
- `doom_fire`
- `doom_menu`
- `doom_run`
- `touch_x`
- `touch_y`
- `touch_tracking`

## Static Validation

- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains the V2987 identity plus touch/keyboard decode strings.

## Safety

- Host-side source build only; no device action in V2987.
- Runtime behavior remains read-only: `readinput` opens `/dev/input/event*` `O_RDONLY|O_NONBLOCK` and prints decoded labels for events it already reads.
- No PMIC/backlight/GPIO/regulator/GDSC, Wi-Fi, audio route, video playback, or forbidden partition path is touched.
- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `readinput-doom-decode-candidate`.

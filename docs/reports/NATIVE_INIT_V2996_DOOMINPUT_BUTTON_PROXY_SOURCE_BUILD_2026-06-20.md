# Native Init V2996 DOOM Input Button Proxy Source Build

## Summary

- Cycle: `V2996`
- Track: active Video playback / DOOM input prerequisite.
- Decision: `v2996-doominput-button-proxy-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2996_doominput_button_proxy.img`
- Boot SHA256: `1509ce74701f2f8d30e7a5ee924b108ca9bb60debed8afab5f9352643e2a4a75`
- Init: `A90 Linux init 0.10.66 (v2996-doominput-button-proxy)`
- Parent candidate: `v2989-doominput-state`.

## Branch Evidence

- V2993 gated repeated built-in touch sampling until a new touch hypothesis exists.
- V2994 gated V2992 USB-keyboard live validation until A90 exposes a keyboard-class evdev node.
- V2995 found two existing physical-button input nodes, but the previous `doominput` source did not map POWER/VOLUME keys to DOOM state bits.

## Included Delta

- Keeps the V2989 `doominput <eventX> [count] [timeout_ms]` read-only sampler.
- Adds a diagnostic physical-button proxy mapping for known live A90 buttons:
  - `KEY_VOLUMEUP` -> `forward` with event role `doom_button_forward`.
  - `KEY_VOLUMEDOWN` -> `back` with event role `doom_button_back`.
  - `KEY_POWER` -> `fire` with event role `doom_button_fire`.
- This is a diagnostic proxy to prove evdev-to-`doominput.state` liveness through event0/event3; it is not promoted as the final DOOM control scheme.
- Adds no input injection, evdev grabs, keymap changes, touch configuration, or sysfs writes.
- No PMIC/backlight/GPIO/regulator/GDSC writes, audio playback, video playback, or forbidden partition path is touched.

## Marker Check

- `A90 Linux init 0.10.66 (v2996-doominput-button-proxy)`
- `doominput <eventX> [count] [timeout_ms]`
- `doominput.event %d: type=%s code=%s role=%s value=%d`
- `doominput.state %d: forward=%d back=%d left=%d right=%d fire=%d use=%d menu=%d run=%d touch=%d`
- `doom_button_forward`
- `doom_button_back`
- `doom_button_fire`

## Static Validation

- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains the V2996 identity, `doominput` command surface, state markers, and physical-button proxy role strings.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v2996_doominput_button_proxy.py tests/test_native_doominput_button_proxy_source_v2996.py`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doominput_button_proxy_source_v2996`: PASS (`4` tests)
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/build_native_init_boot_v2996_doominput_button_proxy.py`: PASS (source build and marker check)
- `file workspace/private/builds/native-init/v2996-doominput-button-proxy/init_v2996_doominput_button_proxy workspace/private/builds/native-init/v2996-doominput-button-proxy/a90_android_execns_probe_v504_doominput_button_proxy`: PASS (both AArch64 static ELF)
- `sha256sum workspace/private/inputs/boot_images/boot_linux_v2996_doominput_button_proxy.img`: PASS (`1509ce74701f2f8d30e7a5ee924b108ca9bb60debed8afab5f9352643e2a4a75`)
- `git diff --check`: PASS

## Safety

- Host-side source build only; no device action in V2996.
- Runtime behavior remains read-only: `doominput` opens `/dev/input/event*` `O_RDONLY|O_NONBLOCK`, polls, reads, and prints state.
- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `doominput-button-proxy-candidate`.

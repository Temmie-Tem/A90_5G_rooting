# Native Init V2989 DOOM Input State Source Build

## Summary

- Cycle: `V2989`
- Track: active Video playback / DOOM input prerequisite.
- Decision: `v2989-doominput-state-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2989_doominput_state.img`
- Boot SHA256: `30e37c64196e7ff2649291c1398c67e96efea9313b25c51dade39d1c62c9ccc2`
- Init: `A90 Linux init 0.10.65 (v2989-doominput-state)`
- Parent candidate: `v2987-readinput-doom-decode`.

## Branch Evidence

- V2984 proved `event6` and `event8` expose touch/MT capability bits and are not sysfs runtime-PM suspended.
- V2988 proved the V2987 decoded `readinput` candidate boots cleanly, but the bounded touch sample still produced `0` decoded events before rollback.
- Repeating the same no-event live sample without fresh operator input or a USB keyboard would be low-information; this source unit prepares the DOOM state surface for the next successful event sample.

## Included Delta

- Adds `doominput <eventX> [count] [timeout_ms]` as a read-only evdev sampler.
- Reuses the V2987 decoded event names and prints `doominput.event` plus `doominput.state` for every captured event.
- Tracks DOOM keyboard roles: forward/back/left/right, fire, use, menu, and run.
- Tracks touch state without inventing controls: contact, x/y, slot, tracking id, pressure, active, and SYN frame count.
- Adds no input injection, evdev grabs, keymap changes, touch configuration, or sysfs writes.
- No PMIC/backlight/GPIO/regulator/GDSC writes, audio playback, video playback, or forbidden partition path is touched.

## Marker Check

- `A90 Linux init 0.10.65 (v2989-doominput-state)`
- `doominput <eventX> [count] [timeout_ms]`
- `doominput.event %d: type=%s code=%s role=%s value=%d`
- `doominput.state %d: forward=%d back=%d left=%d right=%d fire=%d use=%d menu=%d run=%d touch=%d`
- `has_x=%d has_y=%d tracking=%d slot=%d pressure=%d has_pressure=%d active=%d frame=%u`
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
- Marker check: generated boot image contains the V2989 identity, `doominput` command surface, state markers, and retained V2987 decode role strings.
- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v2989_doominput_state.py tests/test_native_doominput_state_source_v2989.py`: PASS.
- `python3 -m unittest tests.test_native_doominput_state_source_v2989`: PASS (`4` tests).
- `python3 -m unittest discover -s tests -p 'test_*.py'`: FAIL with existing unrelated audio/chime expectation failures (`25` failures, `5` errors out of `2556` tests); no V2989/doominput test failed.

## Safety

- Host-side source build only; no device action in V2989.
- Runtime behavior remains read-only: `doominput` opens `/dev/input/event*` `O_RDONLY|O_NONBLOCK`, polls, reads, and prints state.
- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `doominput-state-candidate`.

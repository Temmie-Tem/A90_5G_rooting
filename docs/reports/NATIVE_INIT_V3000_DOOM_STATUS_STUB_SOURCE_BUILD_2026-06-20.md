# Native Init V3000 DOOM Status Stub Source Build

## Summary

- Cycle: `V3000`
- Track: active Video playback / DOOM input prerequisite.
- Decision: `v3000-doom-status-stub-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3000_doom_status_stub.img`
- Boot SHA256: `bca4afa1300dac66499c71a45774547eb9625fdf07e7be09f76259c08e1e8e2d`
- Init: `A90 Linux init 0.10.68 (v3000-doom-status-stub)`
- Parent live handoff: `v2999-doominput-mux-live`.

## Branch Evidence

- Bad Apple and Nyan Cat already cover the KMS/audio demo surface.
- DOOM remains blocked on input liveness: touch events are not proven, and the current live handoff is the V2999 `doominputmux event3,event0` operator-button sample.
- The device menu should expose that status without claiming that DOOM is playable.

## Included Delta

- Adds a `DOOM` entry under the DEMO menu with the subtitle `INPUT PREREQ STATUS`.
- Extends `video status` and `video demo doom status` to report the DOOM blocker and exact V2999 live handoff command.
- Routes `SCREEN_MENU_DEMO_DOOM` to `video demo doom status` only.
- Records the current DOOM input state as `not-proven` rather than silently falling through to a playback path.
- `video demo doom verify` and `video demo doom play` remain blocked with `-EAGAIN` until input is proven.
- Adds no DOOM WAD, no gameplay loop, no input injection, no video/audio playback, and no sysfs writes.
- No PMIC/backlight/GPIO/regulator/GDSC writes, Wi-Fi, or forbidden partition path is touched.

## Marker Check

- `A90 Linux init 0.10.68 (v3000-doom-status-stub)`
- `video.status.doom_stub=1`
- `video.status.doom_input=not-proven`
- `video.demo.status=blocked-input-prerequisite`
- `video.demo.input.button_mux=v2999-doominput-mux-live`
- `video.demo.input.next=doominputmux event3,event0 24 45000`
- `menu.demo.doom.action=status-only`
- `menu.demo.doom.input.live_handoff=v2999-doominput-mux-live`
- `menu.demo.doom.input.command=doominputmux event3,event0 24 45000`

## Static Validation

- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains the V3000 identity, status-only DOOM menu strings, and V2999 live handoff pointers.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v3000_doom_status_stub.py tests/test_native_doom_status_stub_source_v3000.py`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doom_status_stub_source_v3000`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/build_native_init_boot_v3000_doom_status_stub.py`: PASS (source build and marker check)
- `file workspace/private/builds/native-init/v3000-doom-status-stub/init_v3000_doom_status_stub workspace/private/builds/native-init/v3000-doom-status-stub/a90_android_execns_probe_v506_doom_status_stub`: PASS (both AArch64 static ELF)
- `sha256sum workspace/private/inputs/boot_images/boot_linux_v3000_doom_status_stub.img`: PASS (`bca4afa1300dac66499c71a45774547eb9625fdf07e7be09f76259c08e1e8e2d`)
- `git diff --check`: PASS

## Safety

- Host-side source build only; no device action in V3000.
- The new DOOM surface is status-only and does not start playback or sample input.
- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.

## Next

- Run the V2999 live handoff only when an operator can press VOLUMEUP/VOLUMEDOWN/POWER during the single bounded mux window.
- If that proves button liveness, the next DOOM branch can map a minimal menu-driven control path; if it times out, keep the blocker visible and pursue the USB-keyboard fallback explicitly.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `doom-status-stub-candidate`.

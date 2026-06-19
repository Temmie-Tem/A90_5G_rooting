# Native Init V2847 Audio Stop Execute Source Build

## Summary

- Cycle: `V2847`
- Track: post-promotion audio productization / cleanup command surface.
- Decision: `v2847-audio-stop-execute-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2847_audio_stop_execute.img`
- Boot SHA256: `23b54b37bc3451697d218ddbd3d162ec3b167427b460bc0f31d40f17c55abd6e`
- Init: `A90 Linux init 0.10.14 (v2847-audio-stop-execute)`
- Parent candidate: `v2845-audio-boot-chime`

## Included Delta

- Keeps the bundled SET-cal manifest/payload package under `/a90/audio` from V2843/V2845.
- Keeps the compile-time best-effort boot chime hook enabled for candidate continuity.
- Promotes `audio stop --execute` from a refusal to a bounded cleanup command.
- Stop execute reuses the existing `audio route <profile> --reset --layer core` writer.
- Stop execute explicitly avoids fake PCM-handle stop and avoids ACDB deallocate without an active session.

## Stop Execute Contract

- Execute supported: `1`
- Route reset layer: `core`
- Playback stop mode: `no-active-pcm-handle`
- SET-cal deallocate mode: `no-active-setcal-session`
- Live validation state: `pending`

## Bundled Runtime Metadata

- Bundled artifact count: `15`
- Replay entry count: `11`
- Native manifest SHA256: `b29d72ad5b844a2749279d78259e79c731db4d5f12cd546bfd3c3bd122ed6864`
- Boot chime enabled: `1`
- Boot chime best-effort: `1`
- Boot chime blocks boot: `0`
- Raw SET-cal bytes remain private; this report records only counts and hashes.

## Validation

- `py_compile`: builder and focused tests.
- `unittest`: stop-execute source contract and build wrapper tests.
- Build: AArch64 static native-init compile, helper compile, ramdisk pack with bundled private files, boot image pack, SHA256 capture.
- Next live unit should flash this exact image, run `audio stop internal-speaker-safe --execute`, verify route-reset markers, and rollback to `v2321`.

## Safety

- No device action was performed by this builder.
- Stop execute is bounded to the already-validated core route reset path.
- No blind smart-amp boost, SP-bypass, or ACDB deallocate without a live session is introduced.
- Private raw payloads are not committed; they are only copied into the private generated boot image.
- Rollback target remains `v2321-usb-clean-identity-rodata`.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `audio-productization-stop-execute-candidate`.

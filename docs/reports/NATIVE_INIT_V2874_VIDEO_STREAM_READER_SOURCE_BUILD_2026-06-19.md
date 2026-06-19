# Native Init V2874 Video Stream Reader Source Build

## Summary

- Cycle: `V2874`
- Track: active Video playback pipeline on the existing KMS display.
- Decision: `v2874-video-stream-reader-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2874_video_stream_reader.img`
- Boot SHA256: `da69a7e1402b5eb5a84e4a62560f291af5373c2d63aca817263f7a841bbcbfa7`
- Init: `A90 Linux init 0.10.23 (v2874-video-stream-reader)`
- Parent candidate: `v2871-video-blitbench` source plus the current audio/productization baseline builder lineage.

## Included Delta

- Keeps the V2871 `video blitbench` full-frame KMS copy primitive and metadata surface.
- Adds strict `video stream --manifest PATH --video-only [--frames N]` command parsing.
- Adds a bounded manifest parser for the V2873 `video` object and rejects absolute paths, `..`, unknown format, invalid geometry, invalid SHA-256, and excessive frame counts.
- Adds the V1 `A90VSTR1` raw-stride stream reader with header and per-frame record validation.
- Verifies the stream SHA-256 before playback using the existing native `a90_helper_sha256_file()` helper.
- Presents frames through the existing KMS dumb-buffer path and reports `video.stream.*` metrics: frames, bytes, elapsed ns, fps_milli, mbps_milli, late frames, max late ns, geometry, stride, frame bytes, and pixel format.
- Adds `prepare_video_stream_v2874.py` to generate private synthetic `A90VSTR1` fixtures for later live validation; generated payloads remain private and uncommitted.

## Video Metadata

- Version: `3`
- Source unit: `V2874`
- Commands: `video, video status, video frame, video demo, video anim, video blitbench, video stream`
- Stream format: `A90VSTR1 xbgr8888-raw-stride`
- Stream frame bound: `frames<=600`
- Safety boundary: `no-venus-no-kgsl-no-raw-dsi-no-power-writes`

## Bundled Runtime Metadata

- Bundled audio artifact count: `15`
- Replay entry count: `11`
- Native manifest SHA256: `b29d72ad5b844a2749279d78259e79c731db4d5f12cd546bfd3c3bd122ed6864`
- Raw SET-cal bytes remain private; this report records only counts and hashes.

## Static Validation

- `py_compile`: V2874 builder and V2874 synthetic stream generator.
- Build: AArch64 static native-init compile, helper compile, ramdisk pack with bundled private files, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V2874 `video.status.next_stream`, `video.stream.*`, `A90VSTR1`, and `videostream` markers.
- `video.status.kms.stride=`
- `video.status.kms.map_size=`
- `video.status.kms.pixel_format=xbgr8888`
- `video.status.next_blitbench=video blitbench [frames<=240]`
- `video.status.next_stream=video stream --manifest PATH --video-only [--frames N]`
- `video.stream.presented=`
- `video.stream.sha256_checked=1`
- `video.stream.pixel_format=xbgr8888`
- `video stream --manifest PATH --video-only`
- `A90VSTR1`
- `videostream`
- `file`: native-init and helper are AArch64 statically linked executables.
- Private fixture generation: synthetic `A90VSTR1` writer is available for the next live unit; no generated frame payload is committed.
- `python3 -m unittest discover -s tests`: attempted; repository-wide suite still fails in pre-existing historical audio tests (`19` failures, `2` errors) unrelated to the V2874 video stream reader.

## Safety

- No device action was performed by this builder.
- This unit adds no Venus, GPU/KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path.
- The stream reader only opens regular private files and writes to the already-proven KMS dumb-buffer path.
- Rollback target remains `v2321-usb-clean-identity-rodata`.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `video-stream-reader-candidate`.

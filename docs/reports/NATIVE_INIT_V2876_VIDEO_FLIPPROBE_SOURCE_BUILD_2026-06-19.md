# Native Init V2876 Video Page-Flip Probe Source Build

## Summary

- Cycle: `V2876`
- Track: active Video playback pipeline on the existing KMS display.
- Decision: `v2876-video-flipprobe-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2876_video_flipprobe.img`
- Boot SHA256: `2431eac000e5591709d6203130ab57e44d27d8597686aa8775dfc1b471fe759a`
- Init: `A90 Linux init 0.10.24 (v2876-video-flipprobe)`
- Parent candidate: latest audio/productization builder lineage plus V2874 video stream source state.

## Included Delta

- Keeps the V2874 `video stream --manifest ... --video-only` raw-stride reader unchanged.
- Adds `a90_kms_present_pageflip()` as a separate KMS helper that calls `DRM_IOCTL_MODE_PAGE_FLIP` with `DRM_MODE_PAGE_FLIP_EVENT` and waits for a `DRM_EVENT_FLIP_COMPLETE` event on the DRM fd.
- Adds bounded `video flipprobe [frames<=120]`, which primes the CRTC with the existing SETCRTC path, then copies a synthetic full-frame source into the back buffer and presents through page-flip/event waits.
- Reports `video.flipprobe.*` metrics including presented frames, flip event count, last sequence/CRTC/timestamp, fps, MB/s, geometry, stride, and `path=kms-dumb-buffer-pageflip`.
- Leaves `video stream` on the proven SETCRTC present path until a separate live flipprobe validation proves page-flip support on-device.

## Source / Web Grounding

- Linux KMS documentation describes page flipping as replacing the scanned-out framebuffer during vertical blanking and optionally returning a completion event: `https://docs.kernel.org/gpu/drm-kms.html`.
- DRM UAPI documents `DRM_EVENT_FLIP_COMPLETE` as the event returned for legacy page flips submitted with `DRM_MODE_PAGE_FLIP_EVENT`: `https://dri.freedesktop.org/docs/drm/gpu/drm-uapi.html`.
- The dvdhrm double-buffered/vsync examples show the expected userspace pattern: draw into the unused buffer, issue page flip, then wait on the DRM fd before reusing buffers: `https://github.com/dvdhrm/docs/blob/master/drm-howto/modeset-vsync.c`.

## Video Metadata

- Version: `4`
- Source unit: `V2876`
- Commands: `video, video status, video frame, video demo, video anim, video blitbench, video flipprobe, video stream`
- Flipprobe bound: `frames<=120`
- Safety boundary: `no-venus-no-kgsl-no-raw-dsi-no-power-writes`

## Bundled Runtime Metadata

- Bundled audio artifact count: `15`
- Replay entry count: `11`
- Native manifest SHA256: `b29d72ad5b844a2749279d78259e79c731db4d5f12cd546bfd3c3bd122ed6864`
- Raw SET-cal bytes remain private; this report records only counts and hashes.

## Static Validation

- `py_compile`: V2876 builder.
- Build: AArch64 static native-init compile, helper compile, ramdisk pack with bundled private files, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V2876 page-flip command/report markers.
- `video.status.next_flipprobe=video flipprobe [frames<=120]`
- `video.flipprobe.presented=`
- `video.flipprobe.flip_events=`
- `video.flipprobe.path=kms-dumb-buffer-pageflip`
- `DRM_IOCTL_MODE_PAGE_FLIP`
- `videoflipprobe`
- `file`: native-init and helper are AArch64 statically linked executables.
- Next live unit should flash this exact image, run `video status`, `hide`, and bounded `video flipprobe`, then rollback to `v2321`.

## Safety

- No device action was performed by this builder.
- This unit adds no Venus, GPU/KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path.
- The probe uses the already-opened DRM/KMS card0 dumb-buffer path and does not alter panel power or DSI init.
- Rollback target remains `v2321-usb-clean-identity-rodata`.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `video-flipprobe-candidate`.

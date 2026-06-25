# Native Init V3174 GPU G0 Bounded Probe Source Build

## Summary

- Cycle: `V3174`
- Track: GPU G0 KGSL open-hang diagnosis.
- Decision: `v3174-gpu-g0-bounded-probe-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3174_gpu_g0_bounded_probe.img`
- Boot SHA256: `94aaa52ff359b18b8e5a55d565733b08f52ce52a4dd0aeedba418edabd442ffa`
- Init: `A90 Linux init 0.11.17 (v3174-gpu-g0-bounded-probe)`

## Included Delta

- Adds `gpu g0-status` for read-only KGSL sysfs/devnode/firmware visibility.
- Adds `gpu g0-open-probe` where only a forked child calls `open("/dev/kgsl-3d0")`; the parent enforces a timeout and reports timeout/return metadata.
- The probe does not issue KGSL ioctl, mmap, read/write, or any power/GDSC/regulator/PMIC/GPIO write.
- Optional `--materialize-devnode` only creates `/dev/kgsl-3d0` from the read-only sysfs major/minor.
- Preserves V3173 Bad Apple/Nyan PCM-duration fix and DOOM demo chain.

## Safety

- Boot partition only through `native_init_flash.py` in any future live step.
- No PMIC, regulator, GDSC, GPIO, power-rail writes, forbidden partition path, proprietary Adreno blob/EGL/Bionic path, or exploit work.
- G0 open is strictly timeout-guarded; parent never enters the blocking KGSL open.

## Host-Side Diagnosis

- Kernel-source reading shows first KGSL open is not a passive file open: it synchronously runs Adreno init/start, firmware request, GMU/GDSC/clock/IRQ/RPMh/HFI startup, and OOB GPU handoff.
- Therefore the historical unbounded native-init open hang is consistent with first-open GPU/GMU cold-start blocking, not devnode creation itself.
- The bounded probe is the next live-safe evidence point to separate missing firmware/path readiness from a GMU/power-domain transition that would require forbidden writes.

## Validation

- `py_compile`: V3174 builder and focused tests.
- `unittest`: V3174 GPU G0 bounded probe source contract.
- Build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3174 identity and G0 bounded-probe markers.
- `git diff --check`: PASS.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1, -DA90_DOOMGENERIC_BRIDGE_CANDIDATE="v3174-gpu-g0-bounded-probe", -DA90_DOOMGENERIC_BRIDGE_ENGINE="doomgeneric-private-link-v3174-gpu-g0-bounded-probe", -DA90_DOOMGENERIC_BRIDGE_HELPER_PATH="/bin/a90_doomgeneric_private_engine_v3174", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_ROOT="/mnt/sdext/a90/runtime/doom/v3028/", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_PATH="/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD", -DA90_DOOMGENERIC_BRIDGE_EXPECTED_WAD_SHA256="1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771", -DA90_DOOMGENERIC_BRIDGE_FRAME_PATH="/tmp/a90-doomgeneric-v3174-raw-fallback-frame.xbgr8888", -DA90_DOOMGENERIC_BRIDGE_INPUT_STATE_PATH="/tmp/a90-doomgeneric-v3174-input.state", -DA90_DOOMGENERIC_BRIDGE_INPUT="udp-ncm-to-DG_GetKey-with-serial-doompad-fallback", -DA90_DOOMGENERIC_BRIDGE_SOUND="native-doom-sfx-gpu-g0-bounded-probe-v3174", -DA90_DOOMGENERIC_AUDIO_CORUN_MODE="native-doom-sfx-gpu-g0-bounded-probe-v3174", -DA90_DOOMGENERIC_AUDIO_PCM_STREAM_PATH="/cache/a90-runtime/a90-doomgeneric-v3174-sfx.pcmstream", -DA90_DOOMGENERIC_BRIDGE_MAX_WAD_BYTES=67108864, -DA90_DOOMGENERIC_BRIDGE_MAX_PLAY_FRAMES=300, -DA90_DOOMGENERIC_BRIDGE_FRAME_WIDTH=960, -DA90_DOOMGENERIC_BRIDGE_FRAME_HEIGHT=600, -DA90_DOOMGENERIC_BRIDGE_FRAME_STRIDE=3840, -DA90_DOOMGENERIC_BRIDGE_FRAME_BYTES=2304000, -DA90_DOOMGENERIC_BRIDGE_LOOP_FRAME_MS=28, -DVIDEO_DEMO_DOOMGENERIC_PRESENTER_POLL_MS=4, -DA90_DOOMGENERIC_AUDIO_CORUN=1, -DA90_DOOMGENERIC_AUDIO_CORUN_STREAM=1, -DA90_DOOMGENERIC_AUDIO_CORUN_DURATION_MS=240000, -DA90_DOOMGENERIC_AUDIO_CORUN_REFRESH_MS=0, -DA90_DOOMGENERIC_AUDIO_CORUN_AMPLITUDE_MILLI=150, -DA90_DOOMGENERIC_PHYSICAL_BUTTON_EXIT=1, -DVIDEO_DEMO_DOOMGENERIC_REUSE_FRAME_BUFFER=1, -DVIDEO_DEMO_DOOMGENERIC_DIRECT_SHARED_BLIT=1, -DVIDEO_DEMO_DOOMGENERIC_FOREGROUND_FRAME_LOG=0, -DVIDEO_DEMO_DOOMGENERIC_DASHBOARD_METRICS_INTERVAL_FRAMES=1800, -DVIDEO_DEMO_DOOMGENERIC_DASHBOARD_STATUS_INTERVAL_FRAMES=300, -DVIDEO_DEMO_DOOMGENERIC_FRAME_TIMING_PROBE=1, -DVIDEO_DEMO_DOOMGENERIC_SEQ_TELEMETRY=1, -DA90_DOOMGENERIC_NATIVE_DASHBOARD=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_FAST=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_READABLE=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_SECTIONED=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_LARGE_GROUPS=1, -DVIDEO_DEMO_DOOMGENERIC_NO_FULL_CLEAR=1, -DVIDEO_DEMO_DOOMGENERIC_PRESENT_PAGEFLIP=1, -DA90_DOOMGENERIC_BRIDGE_INPUT_SOCKET_PATH="/tmp/a90-doomgeneric-v3174-input.sock", -DA90_DOOMGENERIC_BRIDGE_SHARED_FRAME_PATH="/tmp/a90-doomgeneric-v3174-shared-frame.bin", -DA90_DOOMGENERIC_BRIDGE_PACE_SOCKET_PATH="/tmp/a90-doomgeneric-v3174-pace.sock", -DA90_DOOMGENERIC_BRIDGE_TICK_TELEMETRY_PATH="/tmp/a90-doomgeneric-v3174-tick-telemetry.txt", -DVIDEO_DEMO_DOOMGENERIC_TICK_TELEMETRY_SUMMARY=1, -DA90_DOOMGENERIC_BRIDGE_INPUT_UDP_PORT=30570`
- Candidate type: `gpu-g0-bounded-probe-candidate`.

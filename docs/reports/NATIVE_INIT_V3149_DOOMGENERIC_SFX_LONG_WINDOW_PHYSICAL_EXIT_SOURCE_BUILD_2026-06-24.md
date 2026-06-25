# Native Init V3149 DOOMGENERIC SFX Long Window Physical Exit Source Build

## Summary

- Cycle: `V3149`
- Track: DOOM native demo audio/input polish over the V3148 SFX stream stack.
- Decision: `v3149-doomgeneric-sfx-long-window-physical-exit-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3149_doomgeneric_sfx_long_window_physical_exit.img`
- Boot SHA256: `348dd806f20d2f2ea971f152a516a0aa5a2fcae0ed1098eb631b9abe2fae3b9b`
- Init: `A90 Linux init 0.10.131 (v3149-doomgeneric-sfx-long-window-physical-exit)`

## Included Delta

- Replaces the 10s SFX worker plus 13s refresh cadence with one 240s bounded PCM stream window.
- Leaves audio refresh disabled (`A90_DOOMGENERIC_AUDIO_CORUN_REFRESH_MS=0`) so route/setcal/PCM open churn no longer runs during gameplay.
- Enables DOOM physical-button exit by polling `event3,event0` nonblocking inside the presenter loop.
- Extends `audio stop` so a loop child can stop the current worker from `/cache/a90-audio-play/status.txt` even when the PID is not tracked in that process.

## Runtime Contract

- Runtime WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Expected WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Audio stream path: `/cache/a90-runtime/a90-doomgeneric-v3149-sfx.pcmstream`
- Sound mode: `native-doom-sfx-pcm-stream-long-window-v3149`
- Audio co-run enabled: `1`
- Audio duration ms: `240000`
- Audio refresh ms: `0`
- Audio amplitude milli: `150`
- Physical exit: `POWER`, `VOLUP`, or `VOLDOWN` down event exits the loop.
- Frame IPC: `shared-mmap-direct-blit-demo-hud-large-groups-sfx-long-window-physical-exit`

## Safety

- Boot partition only through `native_init_flash.py` in the live step.
- No PMIC, regulator, GDSC, GPIO writes, Wi-Fi connect/dhcp/ping, or forbidden partition path.
- Physical input handling opens `/dev/input/event0` and `/dev/input/event3` read-only/nonblocking.
- Audio remains bounded by `AUDIO_DOOM_SFX_STREAM_DURATION_CAP_MS`; no persistent unbounded worker is introduced.

## Validation

- `py_compile`: V3149 builder and focused tests.
- `unittest`: V3149 source contract.
- Build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3149 identity, long-window SFX stream markers, physical-exit markers, and inherited HUD/input markers.
- `git diff --check`: PASS.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1, -DA90_DOOMGENERIC_BRIDGE_CANDIDATE="v3149-doomgeneric-sfx-long-window-physical-exit", -DA90_DOOMGENERIC_BRIDGE_ENGINE="doomgeneric-private-link-v3149-sfx-long-window-physical-exit", -DA90_DOOMGENERIC_BRIDGE_HELPER_PATH="/bin/a90_doomgeneric_private_engine_v3149", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_ROOT="/mnt/sdext/a90/runtime/doom/v3028/", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_PATH="/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD", -DA90_DOOMGENERIC_BRIDGE_EXPECTED_WAD_SHA256="1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771", -DA90_DOOMGENERIC_BRIDGE_FRAME_PATH="/tmp/a90-doomgeneric-v3149-raw-fallback-frame.xbgr8888", -DA90_DOOMGENERIC_BRIDGE_INPUT_STATE_PATH="/tmp/a90-doomgeneric-v3149-input.state", -DA90_DOOMGENERIC_BRIDGE_INPUT="udp-ncm-to-DG_GetKey-with-serial-doompad-fallback", -DA90_DOOMGENERIC_BRIDGE_SOUND="native-doom-sfx-pcm-stream-long-window-v3149", -DA90_DOOMGENERIC_AUDIO_CORUN_MODE="native-doom-sfx-pcm-stream-long-window-v3149", -DA90_DOOMGENERIC_AUDIO_PCM_STREAM_PATH="/cache/a90-runtime/a90-doomgeneric-v3149-sfx.pcmstream", -DA90_DOOMGENERIC_BRIDGE_MAX_WAD_BYTES=67108864, -DA90_DOOMGENERIC_BRIDGE_MAX_PLAY_FRAMES=300, -DA90_DOOMGENERIC_BRIDGE_FRAME_WIDTH=960, -DA90_DOOMGENERIC_BRIDGE_FRAME_HEIGHT=600, -DA90_DOOMGENERIC_BRIDGE_FRAME_STRIDE=3840, -DA90_DOOMGENERIC_BRIDGE_FRAME_BYTES=2304000, -DA90_DOOMGENERIC_BRIDGE_LOOP_FRAME_MS=28, -DVIDEO_DEMO_DOOMGENERIC_PRESENTER_POLL_MS=4, -DA90_DOOMGENERIC_AUDIO_CORUN=1, -DA90_DOOMGENERIC_AUDIO_CORUN_STREAM=1, -DA90_DOOMGENERIC_AUDIO_CORUN_DURATION_MS=240000, -DA90_DOOMGENERIC_AUDIO_CORUN_REFRESH_MS=0, -DA90_DOOMGENERIC_AUDIO_CORUN_AMPLITUDE_MILLI=150, -DA90_DOOMGENERIC_PHYSICAL_BUTTON_EXIT=1, -DVIDEO_DEMO_DOOMGENERIC_REUSE_FRAME_BUFFER=1, -DVIDEO_DEMO_DOOMGENERIC_DIRECT_SHARED_BLIT=1, -DVIDEO_DEMO_DOOMGENERIC_FOREGROUND_FRAME_LOG=0, -DVIDEO_DEMO_DOOMGENERIC_DASHBOARD_METRICS_INTERVAL_FRAMES=1800, -DVIDEO_DEMO_DOOMGENERIC_DASHBOARD_STATUS_INTERVAL_FRAMES=300, -DVIDEO_DEMO_DOOMGENERIC_FRAME_TIMING_PROBE=1, -DVIDEO_DEMO_DOOMGENERIC_SEQ_TELEMETRY=1, -DA90_DOOMGENERIC_NATIVE_DASHBOARD=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_FAST=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_READABLE=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_SECTIONED=1, -DA90_DOOMGENERIC_NATIVE_DEMO_HUD_LARGE_GROUPS=1, -DVIDEO_DEMO_DOOMGENERIC_NO_FULL_CLEAR=1, -DVIDEO_DEMO_DOOMGENERIC_PRESENT_PAGEFLIP=1, -DA90_DOOMGENERIC_BRIDGE_INPUT_SOCKET_PATH="/tmp/a90-doomgeneric-v3149-input.sock", -DA90_DOOMGENERIC_BRIDGE_SHARED_FRAME_PATH="/tmp/a90-doomgeneric-v3149-shared-frame.bin", -DA90_DOOMGENERIC_BRIDGE_PACE_SOCKET_PATH="/tmp/a90-doomgeneric-v3149-pace.sock", -DA90_DOOMGENERIC_BRIDGE_TICK_TELEMETRY_PATH="/tmp/a90-doomgeneric-v3149-tick-telemetry.txt", -DVIDEO_DEMO_DOOMGENERIC_TICK_TELEMETRY_SUMMARY=1, -DA90_DOOMGENERIC_BRIDGE_INPUT_UDP_PORT=30570`
- Candidate type: `doomgeneric-sfx-long-window-physical-exit-candidate`.

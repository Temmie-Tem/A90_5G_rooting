# Native Init V3079 DOOMGENERIC Pace Socket Source Build

## Summary

- Cycle: `V3079`
- Track: active Video playback / DOOM capstone frame pacing.
- Decision: `v3079-doomgeneric-pace-socket-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3079_doomgeneric_pace_socket.img`
- Boot SHA256: `beb44467df47e5ac69506920d8bbcfeeb0e88f2f80311eb029a27c622b90f102`
- Init: `A90 Linux init 0.10.96 (v3079-doomgeneric-pace-socket)`

## Included Delta

- Keeps V3077 pageflip presenter, V3074 minimal dashboard, V3071 timing probe, reader reuse, frame_ms=28, and UDP/NCM input.
- Adds a helper-owned Unix datagram pace socket that blocks each helper tick until the presenter sends a token.
- Changes pacing ownership from helper sleep plus presenter pageflip wait to presenter pageflip tokens as the single loop gate.
- Adds a small pageflip submit guard so a fast helper frame cannot immediately re-submit into the same 16.6 ms cadence slot.

## Pacing Contract

- Baseline pacing: `helper-frame-mtime`
- Candidate pacing: `presenter-pageflip-pace-socket`
- Pace socket: `/tmp/a90-doomgeneric-v3079-pace.sock`
- Pageflip min submit interval ms: `18`
- Helper frame ms fallback: `28`
- Presenter poll ms: `4`
- Token contract: presenter sends one token to permit one helper `doomgeneric_Tick()` and frame dump.
- Fallback contract: if no pace socket path is compiled, helper keeps its legacy `usleep(frame_ms)` path.

## Runtime Contract

- Runtime WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Expected WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Helper loop command: `/bin/a90_doomgeneric_private_engine_v3079 --wad-frame-loop /mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD --frames 300 --output /tmp/a90-doomgeneric-v3079-pace-socket-frame.xbgr8888 --input-state /tmp/a90-doomgeneric-v3079-input.state --frame-ms 28 --input-socket /tmp/a90-doomgeneric-v3079-input.sock --pace-socket /tmp/a90-doomgeneric-v3079-pace.sock --input-udp 30570`

## Marker Check

- `A90 Linux init 0.10.96 (v3079-doomgeneric-pace-socket)`
- `v3079-doomgeneric-pace-socket`
- `doomgeneric-private-link-v3079-pace-socket`
- `/bin/a90_doomgeneric_private_engine_v3079`
- `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- `/tmp/a90-doomgeneric-v3079-pace-socket-frame.xbgr8888`
- `/tmp/a90-doomgeneric-v3079-input.state`
- `/tmp/a90-doomgeneric-v3079-input.sock`
- `/tmp/a90-doomgeneric-v3079-pace.sock`
- `a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback`
- `a90.doomgeneric.v3079.pace=presenter-pageflip-token`
- `--input-udp`
- `--pace-socket`
- `udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`
- `video.demo.doom.presenter.pacing=presenter-pageflip-pace-socket`
- `video.demo.doom.presenter.pace_socket_path=`
- `video.demo.doom.presenter.pageflip_min_submit_interval_ms=`
- `video.demo.doom.presenter.present_mode=pageflip`
- `video.demo.doom.presenter.present_path=kms-dumb-buffer-pageflip`
- `video.demo.doom.loop.presenter.pacing=`
- `pace_socket.tokens_sent=`
- `video.demo.doom.loop.pace_socket.wait_timeouts=`
- `video.demo.doom.loop.flip_telemetry=pageflip-event-delta-us`
- `video.demo.doom.loop.timing_probe=1`
- `video.demo.doom.dashboard.profile=minimal-fastdraw`
- `video.demo.input.udp_port=`
- `native-audio-corun-tone-v3053`

## Validation

- `py_compile`: V3079 builder and focused tests.
- `unittest`: V3079 source contract plus V3077/V3074/V3071/V3069 lineage regressions.
- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3079 identity, pace socket helper markers, presenter pace markers, pageflip telemetry, minimal-dashboard markers, and UDP input markers.
- `git diff --check`: PASS.

## Next Unit

- Run ID: `V3080`
- Type: rollback-gated live validation of V3079 pace-socket candidate.
- Scope: flash exact V3079 boot image via `native_init_flash.py`, health-check, require pace-socket markers, run bounded foreground timing loop, compare flip delta distribution with V3078, then start continuous loop and verify UDP input still works.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1, -DA90_DOOMGENERIC_BRIDGE_CANDIDATE="v3079-doomgeneric-pace-socket", -DA90_DOOMGENERIC_BRIDGE_ENGINE="doomgeneric-private-link-v3079-pace-socket", -DA90_DOOMGENERIC_BRIDGE_HELPER_PATH="/bin/a90_doomgeneric_private_engine_v3079", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_ROOT="/mnt/sdext/a90/runtime/doom/v3028/", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_PATH="/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD", -DA90_DOOMGENERIC_BRIDGE_EXPECTED_WAD_SHA256="1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771", -DA90_DOOMGENERIC_BRIDGE_FRAME_PATH="/tmp/a90-doomgeneric-v3079-pace-socket-frame.xbgr8888", -DA90_DOOMGENERIC_BRIDGE_INPUT_STATE_PATH="/tmp/a90-doomgeneric-v3079-input.state", -DA90_DOOMGENERIC_BRIDGE_INPUT="udp-ncm-to-DG_GetKey-with-serial-doompad-fallback", -DA90_DOOMGENERIC_BRIDGE_SOUND="native-audio-corun-tone-v3053", -DA90_DOOMGENERIC_AUDIO_CORUN_MODE="native-audio-corun-tone-v3053", -DA90_DOOMGENERIC_BRIDGE_MAX_WAD_BYTES=67108864, -DA90_DOOMGENERIC_BRIDGE_MAX_PLAY_FRAMES=300, -DA90_DOOMGENERIC_BRIDGE_FRAME_WIDTH=640, -DA90_DOOMGENERIC_BRIDGE_FRAME_HEIGHT=400, -DA90_DOOMGENERIC_BRIDGE_FRAME_STRIDE=2560, -DA90_DOOMGENERIC_BRIDGE_FRAME_BYTES=1024000, -DA90_DOOMGENERIC_BRIDGE_LOOP_FRAME_MS=28, -DVIDEO_DEMO_DOOMGENERIC_PRESENTER_POLL_MS=4, -DA90_DOOMGENERIC_AUDIO_CORUN=1, -DA90_DOOMGENERIC_AUDIO_CORUN_DURATION_MS=10000, -DA90_DOOMGENERIC_AUDIO_CORUN_AMPLITUDE_MILLI=80, -DVIDEO_DEMO_DOOMGENERIC_REUSE_FRAME_BUFFER=1, -DVIDEO_DEMO_DOOMGENERIC_DASHBOARD_METRICS_INTERVAL_FRAMES=30, -DVIDEO_DEMO_DOOMGENERIC_FRAME_TIMING_PROBE=1, -DA90_DOOMGENERIC_NATIVE_DASHBOARD=1, -DA90_DOOMGENERIC_NATIVE_DASHBOARD_MINIMAL=1, -DVIDEO_DEMO_DOOMGENERIC_PRESENT_PAGEFLIP=1, -DVIDEO_DEMO_DOOMGENERIC_PAGEFLIP_MIN_SUBMIT_INTERVAL_MS=18, -DA90_DOOMGENERIC_BRIDGE_INPUT_SOCKET_PATH="/tmp/a90-doomgeneric-v3079-input.sock", -DA90_DOOMGENERIC_BRIDGE_PACE_SOCKET_PATH="/tmp/a90-doomgeneric-v3079-pace.sock", -DA90_DOOMGENERIC_BRIDGE_INPUT_UDP_PORT=30570`
- Candidate type: `doomgeneric-pace-socket-candidate`.

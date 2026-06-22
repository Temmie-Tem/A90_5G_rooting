# Native Init V3057 DOOMGENERIC Input Socket Source Build

## Summary

- Cycle: `V3057`
- Track: active Video playback / DOOM capstone input responsiveness.
- Decision: `v3057-doomgeneric-input-socket-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3057_doomgeneric_input_socket.img`
- Boot SHA256: `27a6e03e8af7005078be184b2d722f25ebbebf990ea21ab73573cea73d64458a`
- Init: `A90 Linux init 0.10.86 (v3057-doomgeneric-input-socket)`

## Included Delta

- Keeps V3053 DOOM autostart and bounded native audio co-run behavior.
- Adds a helper-owned non-blocking Unix datagram input socket for compact latest-state packets.
- Native `doompad state/key/reset` mirrors each input state to both the existing text state file and the socket.
- The helper drains socket packets once per DOOM frame and feeds the latest mask directly into `DG_GetKey` edges.
- The text state file remains as dashboard/fallback state so the existing demo UI continues to show input logs.
- Host input remains serial doompad for this unit; UDP/NCM is still the next transport-separation unit.

## Input Contract

- Input active marker: `serial-doompad-to-DG_GetKey-via-unix-dgram`
- Input socket path: `/tmp/a90-doomgeneric-v3057-input.sock`
- Input state fallback path: `/tmp/a90-doomgeneric-v3057-input.state`
- Packet format: fixed native-endian `{magic, version, seq, mask, active}` datagram.
- Mask bits remain V3047-compatible: `forward:0 back:1 left:2 right:3 fire:4 use:5 menu:6 run:7`.

## Runtime Contract

- Runtime WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Expected WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Helper loop command: `/bin/a90_doomgeneric_private_engine_v3057 --wad-frame-loop /mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD --frames 300 --output /tmp/a90-doomgeneric-v3057-input-socket-frame.xbgr8888 --input-state /tmp/a90-doomgeneric-v3057-input.state --frame-ms 33 --input-socket /tmp/a90-doomgeneric-v3057-input.sock`
- Frame path: `/tmp/a90-doomgeneric-v3057-input-socket-frame.xbgr8888`
- Audio co-run mode: `native-audio-corun-tone-v3053`

## Marker Check

- `A90 Linux init 0.10.86 (v3057-doomgeneric-input-socket)`
- `v3057-doomgeneric-input-socket`
- `doomgeneric-private-link-v3057-input-socket`
- `/bin/a90_doomgeneric_private_engine_v3057`
- `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- `/tmp/a90-doomgeneric-v3057-input-socket-frame.xbgr8888`
- `/tmp/a90-doomgeneric-v3057-input.state`
- `/tmp/a90-doomgeneric-v3057-input.sock`
- `a90.doomgeneric.v3057.input=unix-dgram-state-with-file-fallback`
- `--input-socket`
- `serial-doompad-to-DG_GetKey-via-unix-dgram`
- `video.demo.input.socket_path=`
- `doompad.input_socket.rc=`
- `doompad.input_socket.sent=`
- `doompad.batch=state-mask-v3047`
- `video.demo.doom.loop_start.continuous`
- `video.demo.doom.dashboard.native=1`
- `native-audio-corun-tone-v3053`
- `host_doompad_dashboard_v3035.py`
- `host_doompad_keyboard_v3033.py`
- `video.demo.input.otg_required=0`

## Validation

- `py_compile`: V3057 builder and focused tests.
- `unittest`: V3057 source contract plus V3053/V3047 regressions.
- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3057 input socket, V3053 audio co-run, V3047 batch input, and continuous-loop markers.
- `git diff --check`: PASS.

## Next Unit

- Run ID: `V3058`
- Type: rollback-gated live validation of V3057 input socket candidate.
- Scope: flash exact V3057 boot image, health-check, start DOOM loop, require `video.demo.input.socket_path`, and confirm `doompad state` reports `doompad.input_socket.sent=1` while gameplay remains visible.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1, -DA90_DOOMGENERIC_BRIDGE_CANDIDATE="v3057-doomgeneric-input-socket", -DA90_DOOMGENERIC_BRIDGE_ENGINE="doomgeneric-private-link-v3057-input-socket", -DA90_DOOMGENERIC_BRIDGE_HELPER_PATH="/bin/a90_doomgeneric_private_engine_v3057", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_ROOT="/mnt/sdext/a90/runtime/doom/v3028/", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_PATH="/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD", -DA90_DOOMGENERIC_BRIDGE_EXPECTED_WAD_SHA256="1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771", -DA90_DOOMGENERIC_BRIDGE_FRAME_PATH="/tmp/a90-doomgeneric-v3057-input-socket-frame.xbgr8888", -DA90_DOOMGENERIC_BRIDGE_INPUT_STATE_PATH="/tmp/a90-doomgeneric-v3057-input.state", -DA90_DOOMGENERIC_BRIDGE_INPUT="serial-doompad-to-DG_GetKey-via-unix-dgram", -DA90_DOOMGENERIC_BRIDGE_SOUND="native-audio-corun-tone-v3053", -DA90_DOOMGENERIC_AUDIO_CORUN_MODE="native-audio-corun-tone-v3053", -DA90_DOOMGENERIC_BRIDGE_MAX_WAD_BYTES=67108864, -DA90_DOOMGENERIC_BRIDGE_MAX_PLAY_FRAMES=300, -DA90_DOOMGENERIC_BRIDGE_FRAME_WIDTH=640, -DA90_DOOMGENERIC_BRIDGE_FRAME_HEIGHT=400, -DA90_DOOMGENERIC_BRIDGE_FRAME_STRIDE=2560, -DA90_DOOMGENERIC_BRIDGE_FRAME_BYTES=1024000, -DA90_DOOMGENERIC_BRIDGE_LOOP_FRAME_MS=33, -DA90_DOOMGENERIC_AUDIO_CORUN=1, -DA90_DOOMGENERIC_AUDIO_CORUN_DURATION_MS=10000, -DA90_DOOMGENERIC_AUDIO_CORUN_AMPLITUDE_MILLI=80, -DA90_DOOMGENERIC_NATIVE_DASHBOARD=1, -DA90_DOOMGENERIC_NATIVE_DASHBOARD_LARGE_FRAME=1, -DA90_DOOMGENERIC_BRIDGE_INPUT_SOCKET_PATH="/tmp/a90-doomgeneric-v3057-input.sock"`
- Candidate type: `doomgeneric-input-socket-candidate`.

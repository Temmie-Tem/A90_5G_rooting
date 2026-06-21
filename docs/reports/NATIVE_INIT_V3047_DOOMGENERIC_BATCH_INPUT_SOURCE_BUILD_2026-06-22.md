# Native Init V3047 DOOMGENERIC Batch Input Source Build

## Summary

- Cycle: `V3047`
- Track: active Video playback / DOOM capstone.
- Decision: `v3047-doomgeneric-batch-input-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Device action: `none` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3047_doomgeneric_batch_input.img`
- Boot SHA256: `93ad90ddeb83a5100ed5a690cb059a5476ce5f47f049af661b38bb7c9dc86b12`
- Init: `A90 Linux init 0.10.82 (v3047-doomgeneric-batch-input)`

## Included Delta

- Keeps V3045 continuous DOOM loop behavior and V3042 33ms/color/dashboard improvements.
- Adds `doompad state <seq> <mask>` as a batch input command.
- Defines mask bits as `forward:0 back:1 left:2 right:3 fire:4 use:5 menu:6 run:7`.
- Updates host keyboard/dashboard tooling to prefer batch state commands while leaving `--legacy-key-events` for old residents.
- Lowers host defaults to `hold-ms=110` and `poll-ms=10` for tighter release timing.
- Host input remains serial-only; no OTG keyboard, evdev injection, uinput, or host USB HID injection is introduced.

## Batch Input Contract

- Native command: `doompad state <seq> <mask>`
- Status marker: `doompad.batch=state-mask-v3047`
- Output marker: `doompad.state_batch seq=<seq> mask=0xXX active=<0|1>`
- Host key down/up transport: `doompad state`, not one command per role edge.
- Legacy fallback: `--legacy-key-events` keeps `doompad key <role> <0|1>`.

## Runtime WAD / Loop Contract

- Runtime WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Expected WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- WAD files in ramdisk: `0`
- WAD bytes embedded in boot image: `0`
- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Helper loop frame ms: `33`
- Frame path: `/tmp/a90-doomgeneric-v3047-batch-input-frame.xbgr8888`
- Input state path: `/tmp/a90-doomgeneric-v3047-input.state`

## Host Tooling

- Host keyboard bridge: `workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py`
- Host dashboard: `workspace/public/src/scripts/revalidation/host_doompad_dashboard_v3035.py`
- Default hold ms: `110`
- Default poll ms: `10`

## Private Engine Helper

- Bundled helper path: `/bin/a90_doomgeneric_private_engine_v3047`
- V3047 engine binary: `workspace/private/builds/native-init/v3047-doomgeneric-batch-input/a90_doomgeneric_private_engine_v3047`
- V3047 engine SHA256: `f5dd8db2e94c8303ea6a1339fb1cc67e6b9825d6d51950a506bfc700ae0245a7`
- V3047 engine bytes: `1070008`
- Helper bundled in ramdisk: `1`

## Marker Check

- `A90 Linux init 0.10.82 (v3047-doomgeneric-batch-input)`
- `v3047-doomgeneric-batch-input`
- `doomgeneric-private-link-v3047-batch-input`
- `/bin/a90_doomgeneric_private_engine_v3047`
- `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- `/tmp/a90-doomgeneric-v3047-batch-input-frame.xbgr8888`
- `/tmp/a90-doomgeneric-v3047-input.state`
- `--wad-frame-loop`
- `--input-state`
- `--frame-ms`
- `a90.doomgeneric.v3045.continuous_loop=33ms-loop-start-zero-continuous`
- `a90.doomgeneric.v3045.loop=input-state-file-to-DG_GetKey-33ms-continuous`
- `a90.doomgeneric.v3045.frame_color=rb-swap-to-xbgr8888`
- `a90.doomgeneric.v3045.loop_frames_zero=continuous`
- `doompad.batch=state-mask-v3047`
- `doompad.mask.bits=forward:0 back:1 left:2 right:3 fire:4 use:5 menu:6 run:7`
- `doompad.state_batch seq=`
- `doompad state <seq> <mask>`
- `video.demo.doom.loop_start.continuous`
- `video.demo.doom.loop_status.continuous`
- `video.demo.doom.dashboard.native=1`
- `video.demo.doom.dashboard.presenter_log=quiet-per-frame`
- `host_doompad_dashboard_v3035.py`
- `host_doompad_keyboard_v3033.py`
- `video.demo.input.otg_required=0`

## Safety

- No device action was performed by this builder.
- No flash, serial live command, Wi-Fi action, sysfs write, evdev injection, uinput, PMIC, regulator, backlight, GPIO, GDSC, or forbidden partition path is touched.
- WAD/IWAD bytes remain only on the runtime SD path and are not copied into public, ramdisk, boot image, reports, or generated source.
- The generated boot image and helper are private/untracked. Public output is limited to source, tests, host tooling, and this metadata-only report.
- Rollback target remains `v2321-usb-clean-identity-rodata` for the next live unit.

## Host Validation

- `py_compile`: builder, dependent host scripts, and focused tests.
- `unittest`: V3047 batch-input tests plus host keyboard/dashboard regressions.
- Build: AArch64 static private doomgeneric helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3047 batch-input markers, helper path, input-state path, SD WAD path/hash, and continuous-loop markers.
- Ramdisk inventory: helper path present and WAD file count is zero.
- `git diff --check`: PASS.

## Next Unit

- Run ID: `V3048`
- Type: rollback-gated live validation of V3047 batch-input candidate.
- Scope: flash only the exact V3047 boot image through `native_init_flash.py`, health-check, run `doompad state` masks for single and multi-key states, then validate host keyboard/dashboard batch input against a continuous DOOM loop.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1, -DA90_DOOMGENERIC_BRIDGE_CANDIDATE="v3047-doomgeneric-batch-input", -DA90_DOOMGENERIC_BRIDGE_ENGINE="doomgeneric-private-link-v3047-batch-input", -DA90_DOOMGENERIC_BRIDGE_HELPER_PATH="/bin/a90_doomgeneric_private_engine_v3047", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_ROOT="/mnt/sdext/a90/runtime/doom/v3028/", -DA90_DOOMGENERIC_BRIDGE_RUNTIME_WAD_PATH="/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD", -DA90_DOOMGENERIC_BRIDGE_EXPECTED_WAD_SHA256="1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771", -DA90_DOOMGENERIC_BRIDGE_FRAME_PATH="/tmp/a90-doomgeneric-v3047-batch-input-frame.xbgr8888", -DA90_DOOMGENERIC_BRIDGE_INPUT_STATE_PATH="/tmp/a90-doomgeneric-v3047-input.state", -DA90_DOOMGENERIC_BRIDGE_MAX_WAD_BYTES=67108864, -DA90_DOOMGENERIC_BRIDGE_MAX_PLAY_FRAMES=300, -DA90_DOOMGENERIC_BRIDGE_FRAME_WIDTH=640, -DA90_DOOMGENERIC_BRIDGE_FRAME_HEIGHT=400, -DA90_DOOMGENERIC_BRIDGE_FRAME_STRIDE=2560, -DA90_DOOMGENERIC_BRIDGE_FRAME_BYTES=1024000, -DA90_DOOMGENERIC_BRIDGE_LOOP_FRAME_MS=33, -DA90_DOOMGENERIC_NATIVE_DASHBOARD=1, -DA90_DOOMGENERIC_NATIVE_DASHBOARD_LARGE_FRAME=1`
- Candidate type: `doomgeneric-batch-input-candidate`.

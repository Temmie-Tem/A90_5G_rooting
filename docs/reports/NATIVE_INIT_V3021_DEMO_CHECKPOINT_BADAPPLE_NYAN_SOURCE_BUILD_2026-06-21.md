# Native Init V3021 Demo Checkpoint Bad Apple + Nyan Source Build

## Summary

- Cycle: `V3021`
- Track: active Video playback / kept demo checkpoint before further DOOM integration.
- Decision: `v3021-demo-checkpoint-badapple-nyan-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3021_demo_checkpoint_badapple_nyan.img`
- Boot SHA256: `c860d604e3c906abf61fdd2c9bd9cd12d1aef2c88c05be57677b472ad36ef0f7`
- Init: `A90 Linux init 0.10.72 (v3021-demo-checkpoint-badapple-nyan)`

## Included Delta

- Bumps the current accumulated native-init video/demo surface to patch version `0.10.72`.
- Keeps the validated Bad Apple Player HUD full-song path: `setcrtc`, incremental HUD panel, beat flash, low-amplitude PCM, and SHA-addressed SD cache.
- Keeps the validated Nyan Cat `A90VSTR2 pal8-rle` Player HUD preview path with bounded low-amplitude PCM.
- Keeps the DOOM serial `doompad`/`doomplay` status surface present but does not claim WAD-backed `doomgeneric` yet.
- Does not bundle media frames or PCM into the boot image; the image carries player code, menu entries, and content-addressed path/SHA contracts.

## Demo Contracts

- Bad Apple asset ID: `badapple-480x360-full-v2903`
- Bad Apple stream SHA256: `9e938aa83ef40aa692d0f42080821dc21a627f1dddd90cc9c2696aafe6ac6eb0`
- Bad Apple audio SHA256: `b96d2e0bc4bb6b0ada0da6e63e40168115e3818d72c386dd8764162e85238a75`
- Bad Apple audio runtime path: `/cache/a90-runtime/pkg/av/v2920/audio/badapple.s16le`
- Nyan asset ID: `nyancat-v2973-pal8-rle-preview`
- Nyan stream SHA256: `9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573`
- Nyan audio SHA256: `4c3774553195c04166a3a83de793253696a5bee60afe83a04219419fc28e43de`
- Nyan audio runtime path: `/cache/a90-runtime/pkg/av/v2973/audio/nyancat.s16le`

## Marker Check

- `A90 Linux init 0.10.72 (v3021-demo-checkpoint-badapple-nyan)`
- `video.status.version=9`
- `video.status.player_hud_incremental_panel=1`
- `video.status.nyan_pal8_rle=1`
- `video.status.doom_input=serial-doompad-staged`
- `video cache preset [badapple|badapple-scale|nyan]`
- `video demo [badapple|badapple-scale|nyan|doom]`
- `badapple-480x360-full-v2903`
- `9e938aa83ef40aa692d0f42080821dc21a627f1dddd90cc9c2696aafe6ac6eb0`
- `b96d2e0bc4bb6b0ada0da6e63e40168115e3818d72c386dd8764162e85238a75`
- `menu.demo.badapple.action=play-av-fullsong`
- `menu.demo.badapple.frames=6962`
- `menu.demo.badapple.audio_pcm=/cache/a90-runtime/pkg/av/v2920/audio/badapple.s16le`
- `menu.demo.badapple.video_present=setcrtc`
- `menu.demo.badapple.audio_sync_start_offset_ms=450`
- `nyancat-v2973-pal8-rle-preview`
- `9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573`
- `DEMO / NYAN CAT`
- `menu.demo.nyan.action=play-av-preview`
- `menu.demo.nyan.frames=300`
- `menu.demo.nyan.audio_pcm=/cache/a90-runtime/pkg/av/v2973/audio/nyancat.s16le`
- `menu.demo.nyan.video_present=setcrtc`
- `pal8-rle`
- `A90VSTR2`
- `doompad [status|reset|key <role> <0|1>|tap <role>]`
- `video.demo.status=doompad-frame-loop-ready`
- `video.demo.engine=doompad-loop-not-doomgeneric`
- `video.demo.input=serial-doompad-consumed`
- `video.demo.play.command=video demo doom play [frames]`

## Static Validation

- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.
- Marker check: generated boot image contains the V3021 identity, Bad Apple full-song Player HUD markers, Nyan pal8-rle preview markers, and retained serial DOOMPAD status markers.
- Device validation is deferred to V3022: flash this exact image, validate Bad Apple and Nyan in the same resident image, health-check, and rollback to V2321.

## Bundled Runtime Metadata

- Bundled audio artifact count: `15`
- Replay entry count: `11`
- Native manifest SHA256: `b29d72ad5b844a2749279d78259e79c731db4d5f12cd546bfd3c3bd122ed6864`

## Safety

- No device action was performed by this builder.
- Generated streams, PCM, boot images, and private caches remain private/untracked.
- This is a patch-level kept demo checkpoint candidate, not a 0.11.0 video-epic closeout.
- Rollback target remains `v2321-usb-clean-identity-rodata`.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v3021_demo_checkpoint_badapple_nyan.py workspace/public/src/scripts/revalidation/native_init_frontier_select.py tests/test_native_demo_checkpoint_badapple_nyan_source_v3021.py tests/test_native_init_frontier_select.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_demo_checkpoint_badapple_nyan_source_v3021 tests.test_native_init_frontier_select`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_init_frontier_select.py --json`: PASS (`demo-checkpoint-live-validation-ready`).
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/build_native_init_boot_v3021_demo_checkpoint_badapple_nyan.py`: PASS
- `file workspace/private/builds/native-init/v3021-demo-checkpoint-badapple-nyan/init_v3021_demo_checkpoint_badapple_nyan workspace/private/builds/native-init/v3021-demo-checkpoint-badapple-nyan/a90_android_execns_probe_v510_demo_checkpoint_badapple_nyan`: PASS (both AArch64 static ELF)
- `sha256sum workspace/private/inputs/boot_images/boot_linux_v3021_demo_checkpoint_badapple_nyan.img`: PASS (`c860d604e3c906abf61fdd2c9bd9cd12d1aef2c88c05be57677b472ad36ef0f7`)
- `git diff --check`: PASS

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1, -DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1, -DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1, -DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1, -DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1, -DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1, -DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1, -DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1, -DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1, -DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1, -DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1, -DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1, -DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1, -DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1, -DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1, -DNETSERVICE_USB_HELPER="/bin/a90_usbnet", -DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl", -DNETSERVICE_TOYBOX="/bin/toybox", -DA90_BUSYBOX_HELPER="/bin/busybox", -DA90_WIFI_LIFECYCLE_MODEM_OWNER=1, -DA90_TRANSPORT_STATUS_CONTRACT=1, -UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH, -DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0, -DAUDIO_SETCAL_BUNDLED_PREFIX="/a90/audio", -DAUDIO_SETCAL_DEFAULT_MANIFEST_PATH="/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest", -DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1`
- Candidate type: `demo-checkpoint-badapple-nyan-candidate`.
- Adoption state: `pending-badapple-nyan-same-image-live-validation`.

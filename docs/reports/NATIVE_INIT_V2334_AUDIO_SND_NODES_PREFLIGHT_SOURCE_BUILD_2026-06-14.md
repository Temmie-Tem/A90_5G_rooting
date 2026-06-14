# Native Init V2334 Audio `/dev/snd` Nodes Preflight Source Build

## Summary

- Cycle: `V2334`
- Track: audio AUD-3 preflight, source/build-only.
- Decision: `v2334-audio-snd-nodes-preflight-source-build-pass`
- Result: PASS
- Device flash: `no`.
- Device action: `none`.
- Manifest: `workspace/private/builds/native-init/v2334-audio-snd-nodes-preflight/manifest.json`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2334_audio_snd_nodes_preflight.img`
- Boot SHA256: `53b1130cd912ca4019a3d76835eb721804bae0460b920eb7fdfad5509a2dfcac`
- Init: `A90 Linux init 0.9.292 (v2334-audio-snd-nodes-preflight)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Change

- Keeps V2331's `firmware_class.path=/vendor/firmware_mnt/image` behavior for ADSP firmware loading.
- Adds `audio snd-status`, a read-only `/sys/class/sound` inventory that reports allowed ALSA node names, sysfs `major:minor`, and matching `/dev/snd/*` state.
- Adds `audio snd-materialize-once AUD3_DEV_SND_MATERIALIZE_ONLY`, a token-gated materialization-only command.
- The materializer creates only `/dev/snd/<allowed>` char nodes from `/sys/class/sound/<allowed>/dev`; it never accepts arbitrary paths or inferred major/minor values.
- Allowed names are `controlC[0-9]+`, `pcmC[0-9]+D[0-9]+p`, `pcmC[0-9]+D[0-9]+c`, `timer`, and `seq`.
- Existing nodes are accepted only when they are char devices with matching `st_rdev`; mismatches are refused and not unlinked.
- No ALSA node open, ioctl, mixer, tinyalsa, PCM, HAL, adsprpc invoke/ioctl, `/dev/subsys_adsp` open, or playback path is added.

## Command Surface

- `audio adsp-status` / `audio status`: retained AUD-2 status surface, now also emits the bounded `audio.snd_status.*` summary when sysfs can be scanned.
- `audio snd-status`: read-only and menu/power safe.
- `audio snd-materialize-once AUD3_DEV_SND_MATERIALIZE_ONLY`: blocked from menu/power contexts; future live use needs the V2333 explicit AUD-3-preflight operator phrase.
- `audio adsp-boot-once AUD2_ONE_SHOT_ADSP_BOOT`: unchanged and still AUD-2 liveness-only.

## Safety Boundary

- This is not AUD-3 playback. It only builds the node-inventory/materialization preflight needed before playback can be evaluated.
- No flash was performed by this source-build unit.
- Future live materialization remains a separate operator-gated step and must rollback to V2321 after validation.
- Future playback remains a later, separate operator-gated AUD-3 step.

## USB Baseline Retained

- Parent descriptor remains V2321: `A90-LNX` / `A90 Linux ARM64` / `A90NATIVE001`.
- V2323 named multi-LUN behavior is retained:
- `lun.0` model `A90-INTERNAL`, FAT label `A90INTERNAL`, backing `/cache/a90-usb-mass-storage-v2323-internal.img`.
- `lun.1` model `A90-SD`, FAT label `A90SD`, backing `/cache/a90-usb-mass-storage-v2323-sd.img`.

## Helper Flags

- `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1`
- `-DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1`
- `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`

## Init Extra Flags

- `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=1`
- `-DNETSERVICE_USB_HELPER="/bin/a90_usbnet"`
- `-DNETSERVICE_TCPCTL_HELPER="/bin/a90_tcpctl"`
- `-DNETSERVICE_TOYBOX="/bin/toybox"`
- `-DA90_BUSYBOX_HELPER="/bin/busybox"`
- `-DA90_WIFI_LIFECYCLE_MODEM_OWNER=1`
- `-DA90_TRANSPORT_STATUS_CONTRACT=1`
- `-UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH`
- `-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0`

## Static Validation

- Source build: PASS.
- `file` on init binary: recorded by builder output.
- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v2334_audio_snd_nodes_preflight.py`: PASS.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: PASS.
- `git diff --check`: PASS.

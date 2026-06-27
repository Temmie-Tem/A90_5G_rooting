# Native Init V3341 SoftAP S3 IfType Probe Source Build

- Cycle: `V3341`
- Decision: `v3341-softap-s3-iftype-probe-source-build-pass`
- Init: `A90 Linux init 0.11.105 (v3341-softap-s3-iftype-probe)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3341_softap_s3_iftype_probe.img`
- Boot SHA256: `a0fe07b1f347a2212d375067c442b163b7e6cd68cb7a605ab5dce4c87082c7af`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `wifi softap iftype-probe [timeout_ms]` as the S3 lower-gate proof command.
- The probe waits for `wlan0`, stops a stale station `wpa_supplicant` if present, creates a temporary AP-type nl80211 interface, and deletes it before returning.
- Carries forward the V2237 post-FW_READY firmware_class bridge helper route so the current SoftAP baseline can surface `wlan0` before the probe.
- Keeps AP service below start: no generated SSID/PSK config, no `wpa_supplicant mode=2`, no `udhcpd`, no listener, no AP address, no route/NAT.

## Validation Contract

- Commands: `wifi softap status`, `wifi softap plan`, `wifi softap prepare`, `wifi softap iftype-probe`.
- PASS requires post-flash `selftest fail=0`, helper-window `wlan0_present=1`, `decision=softap-iftype-probe-pass`, `ap_iftype_add_rc=0`, `ap_iftype_iface_created=1`, and `ap_iftype_cleanup_ok=1`.
- Public output remains metadata-only and must not contain SSID, PSK, BSSID, MAC, client identifiers, concrete peer addresses, DHCP leases, or transfer payloads.

## Static Validation

- `py_compile`: V3341 builder and focused source tests.
- Unit tests: V3341 iftype-probe source/build contract plus retained V3338/V3339 SoftAP contract updates.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3341 identity, SoftAP v2, iftype-probe decision markers, and no-start fields.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `softap-s3-iftype-probe-candidate`.

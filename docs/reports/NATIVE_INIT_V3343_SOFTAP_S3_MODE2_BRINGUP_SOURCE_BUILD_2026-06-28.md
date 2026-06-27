# Native Init V3343 SoftAP S3 Mode2 Bringup Source Build

- Cycle: `V3343`
- Decision: `v3343-softap-s3-mode2-bringup-source-build-pass`
- Init: `A90 Linux init 0.11.107 (v3343-softap-s3-mode2-bringup)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3343_softap_s3_mode2_bringup.img`
- Boot SHA256: `601e27287a1b695c326a99e27522e36bb5afde629da5b30b024f7f59ec5068e7`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `wifi softap start [channel]` for the first bounded AP bring-up after the V3342 lower gate pass.
- Starts a private generated WPA2 SoftAP through `wpa_supplicant mode=2` on 2.4GHz channel 1, 6, or 11; `hostapd` remains unused.
- Starts BusyBox `udhcpd` for the private AP subnet without WAN/NAT/default-route export and without a server listener.
- Makes `wifi softap cleanup` real: stop AP supplicant, stop `udhcpd`, delete the AP interface, and remove private runtime config.

## Validation Contract

- PASS requires post-flash `selftest fail=0`, `decision=softap-start-pass`, `wpa_supplicant_mode2_start_attempted=1`, `dhcp_server_start_attempted=1`, `dhcp_server_alive=1`, and `decision=softap-cleanup-pass`.
- Public output remains metadata-only and must not contain SSID, PSK, BSSID, MAC, client identifiers, concrete peer addresses, DHCP leases, or transfer payloads.

## Static Validation

- `py_compile`: V3343 builder and focused source tests.
- Unit tests: V3343 source/build contract plus retained V3341/V3342 SoftAP lower-gate contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3343 identity, SoftAP start/cleanup decisions, mode=2, `udhcpd`, and no-route/NAT fields.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `softap-s3-mode2-bringup-candidate`.

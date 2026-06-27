# Native Init V3344 SoftAP S4 Transfer Server Source Build

- Cycle: `V3344`
- Decision: `v3344-softap-s4-transfer-server-source-build-pass`
- Init: `A90 Linux init 0.11.108 (v3344-softap-s4-transfer-server)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3344_softap_s4_transfer_server.img`
- Boot SHA256: `d24fe3fded67d83a1bd87b13f3459bdaec6d588cb947a5231cc08d6c397515a8`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `wifi softap transfer-start [channel]` for the S4 private transfer proof on top of the V3343 AP/DHCP bring-up.
- Starts BusyBox `httpd` bound only to the private AP address and serves a bounded deterministic download payload with a printed SHA256.
- Starts a native single-connection raw upload receiver bound only to the private AP address, writes a bounded upload file, and reports upload SHA256 through `wifi softap transfer-status`.
- Extends `wifi softap cleanup` to stop HTTP/upload workers and remove transfer runtime files before tearing down AP/DHCP.

## Validation Contract

- PASS requires post-flash `selftest fail=0`, `decision=softap-transfer-start-pass`, a client joined to the private AP, HTTP download SHA match, raw upload SHA match, `decision=softap-cleanup-pass`, and post-cleanup `selftest fail=0`.
- Public output remains metadata-only and must not contain SSID, PSK, BSSID, MAC, client identifiers, concrete peer addresses, DHCP leases, or transfer payload bytes.

## Static Validation

- `py_compile`: V3344 builder and focused source tests.
- Unit tests: V3344 source/build contract plus retained V3341-V3343 SoftAP contracts.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3344 identity, transfer-start/status decisions, private AP bind marker, SHA fields, and cleanup markers.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `softap-s4-transfer-server-candidate`.

# Native Init V3344 SoftAP S4 Transfer Server Live

- Cycle: `V3344`
- Decision: `v3344-softap-s4-transfer-server-live-pass`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3344_softap_s4_transfer_server.img`
- Boot SHA256: `d24fe3fded67d83a1bd87b13f3459bdaec6d588cb947a5231cc08d6c397515a8`
- Init: `A90 Linux init 0.11.108 (v3344-softap-s4-transfer-server)`

## Flash And Health

- Rollback gates were present before flash: v2321 SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`, v2237 SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`, v48 present, and TWRP recovery present.
- Flashed only through `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Local, pushed, and boot-block readback SHA256 all matched `d24fe3fded67d83a1bd87b13f3459bdaec6d588cb947a5231cc08d6c397515a8`.
- Post-flash `version`/`status` passed; initial health was `selftest pass=12 warn=1 fail=0`.

## S4 Transfer Proof

- `wifi softap transfer-start 6` returned rc `0` and `decision=softap-transfer-start-pass`.
- AP/DHCP lower path passed inside the command: `wlan0_present=1`, `sta_supplicant.stoppable=1`, `ap_iftype_add_rc=0`, `softap.ctrl_status.field.mode=AP`, `softap.ctrl_status.field.wpa_state=COMPLETED`, `dhcp_server_alive=1`, and `decision=softap-start-pass`.
- S4 server path passed: `server_bind_private_ap_only=1`, `httpd_alive=1`, `upload_receiver_alive=1`, `download_payload_bytes=1048576`, and download payload SHA256 `0fb3f6622678efe11f84f3bf032031802a8745d9c8a1f834aece10fe6d1bbd62`.
- A host client joined the private AP using private runtime credentials. SSID, PSK, client identifier, peer address, concrete local address, and DHCP lease details were not recorded in this public report.
- Host HTTP download read `1048576` bytes and matched SHA256 `0fb3f6622678efe11f84f3bf032031802a8745d9c8a1f834aece10fe6d1bbd62`.
- Host raw upload sent `1048576` bytes with SHA256 `3cd6eccfa373a28f7a411ef5cbdc3c407ada3eaf2263ef5879531989d9dc4348`.
- `wifi softap transfer-status` returned rc `0` and `decision=softap-transfer-status-pass`; device-side `upload_result=pass`, `upload_result.bytes=1048576`, `upload_result.truncated=0`, `upload_result.sha256=3cd6eccfa373a28f7a411ef5cbdc3c407ada3eaf2263ef5879531989d9dc4348`, and `upload_file.sha256=3cd6eccfa373a28f7a411ef5cbdc3c407ada3eaf2263ef5879531989d9dc4348`.

## Cleanup

- `wifi softap cleanup` returned rc `0` and `decision=softap-cleanup-pass`.
- Cleanup stopped S4/S3 workers and removed runtime files: `cleanup.final_httpd_count=0`, `cleanup.final_supplicant_count=0`, `cleanup.final_udhcpd_count=0`, `cleanup.final_iface_present=0`, `cleanup.transfer_runtime_removed=1`, and `cleanup.private_config_removed=1`.
- Follow-up `selftest` stayed `pass=12 warn=1 fail=0`.
- The host temporary Wi-Fi connection was removed after the proof.

## Redaction

Public artifacts intentionally omit SSID, PSK, BSSID, MAC, client identifiers, concrete peer/local network addresses, DHCP leases, and payload bytes. Private live-transfer artifacts remain under `workspace/private/builds/native-init/v3344-softap-s4-transfer-server/`.

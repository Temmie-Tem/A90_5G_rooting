# Native Init V3343 SoftAP S3 Mode2 Bringup Live

- Cycle: `V3343`
- Init: `A90 Linux init 0.11.107 (v3343-softap-s3-mode2-bringup)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3343_softap_s3_mode2_bringup.img`
- Boot SHA256: `601e27287a1b695c326a99e27522e36bb5afde629da5b30b024f7f59ec5068e7`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Rollback baseline: `v2321-usb-clean-identity-rodata`
- Decision: `v3343-softap-s3-mode2-bringup-live-pass`

## Flash Gate

- Rollback images and TWRP recovery were present with expected SHA256 values before flash.
- Flashed only through `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Boot partition readback SHA256 matched the final candidate SHA.
- Post-flash resident version/status passed for `0.11.107`.
- Health stayed clean before and after functional validation: `selftest pass=12 warn=1 fail=0`.

## Functional Evidence

- Command: `wifi softap start 6`.
- `wlan0_wait_rc=0`, `wlan0_present=1`.
- `sta_supplicant.stoppable=1`, `sta_supplicant.stop_rc=0`.
- `ap_iftype_add_rc=0`, `ap_iftype_iface_created=1`.
- `address_assign_rc=0`, with `address_value_logged=0`.
- `wpa_supplicant_mode2_start_attempted=1`, `wpa_supplicant_mode2_spawn_rc=0`.
- `softap_ctrl_reply_category=pong`.
- `softap.ctrl_status.field.mode=AP`.
- `softap.ctrl_status.field.wpa_state=COMPLETED`.
- `softap.ctrl_status.field.key_mgmt=WPA2-PSK`.
- `dhcp_server_start_attempted=1`, `dhcp_server_spawn_rc=0`, `dhcp_server_alive=1`.
- `decision=softap-start-pass`.

## Safety Evidence

- `hostapd_start_attempted=0`.
- `listener_start_attempted=0`.
- `server_exposure_attempted=0`.
- `wan_nat_attempted=0`.
- `ip_forward_write_attempted=0`.
- `nat_attempted=0`.
- `default_route_export_attempted=0`.
- `dhcp_router_option_exported=0`.
- `dhcp_dns_option_exported=0`.
- `ssid_psk_logged=0`.
- No SSID, PSK, BSSID, MAC, client identifier, concrete peer address, DHCP lease, or transfer payload is recorded in this report.

## Cleanup Evidence

- Command: `wifi softap cleanup`.
- AP supplicant control terminate returned OK.
- AP supplicant pid stop: `stop_rc=0`.
- DHCP pid stop: `stop_rc=0`.
- AP interface delete: `delete_rc=0`, `iface_present_after=0`.
- `private_config_removed=1`.
- `final_supplicant_count=0`.
- `final_udhcpd_count=0`.
- `final_iface_present=0`.
- `cleanup.rc=0`.
- `decision=softap-cleanup-pass`.

## Notes

- An earlier V3343 live attempt proved AP start and cleanup but exposed two telemetry format omissions in cleanup labels. The source was fixed, rebuilt, reflashed under the final SHA above, and the final live run verified clean labels plus the same AP/DHCP/cleanup behavior.
- S3 is now closed. The next bounded unit is S4: start the local transfer server on the private AP, have a client join, prove HTTP download and raw upload SHA integrity, then stop server/AP and keep `selftest fail=0`.

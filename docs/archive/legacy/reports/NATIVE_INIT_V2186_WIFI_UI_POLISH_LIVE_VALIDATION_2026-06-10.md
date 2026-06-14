# Native Init V2186 Wi-Fi UI Polish Live Validation

## Summary

- Candidate tag: `v2186-wifi-ui-polish`.
- Device-visible init during test: `A90 Linux init 0.9.258 (v2186-wifi-ui-polish)`.
- Type: live flash plus Wi-Fi UI/status metric validation.
- Decision: `v2186-wifi-ui-polish-live-pass`.
- Result: PASS.
- Reason: V2186 flashed, booted, connected, acquired DHCP, exposed redacted
  runtime WPA/RSSI/link/frequency fields through `wifi status`, passed a bounded
  gateway ping, accepted `screenmenu`, and was rolled back to V2185.
- Evidence directories:
  - initial run with serial/protocol-noise connect attempt:
    `workspace/private/runs/wifi/v2186-wifi-ui-polish-live-20260610-081826`;
  - passing retry:
    `workspace/private/runs/wifi/v2186-wifi-ui-polish-live-retry-20260610-082311`.
- Test boot image:
  `workspace/private/inputs/boot_images/boot_linux_v2186_wifi_ui_polish.img`.
- Test boot SHA256:
  `7a0db3bb76232f778869d3bf0788268f3a1942b230b094158dddf7a7d500fd32`.
- Rollback image:
  `workspace/private/inputs/boot_images/boot_linux_v2185_network_ping_test.img`.
- Rollback boot SHA256:
  `3ab13707c4ad93cb0b23c26174407be9a0ca30460fce879131ba6bea0df253b7`.

## Live Results

- V2186 flash/readback: boot partition prefix SHA matched local V2186 image.
- V2186 boot verify: `version` and `status` passed with selftest `fail=0`.
- Retry cleanup: `wifi-cleanup-done`.
- Connect: `wifi connect` reached `wifi-connect-carrier-up`.
- DHCP: `wifi dhcp` reached `wifi-dhcp-pass`.
- Runtime status after DHCP:
  - `operstate=up`;
  - `carrier=1`;
  - `runtime.ssid_label=connected`;
  - `runtime.wpa_state=COMPLETED`;
  - `runtime.rssi_dbm` populated;
  - `runtime.linkspeed_mbps` populated;
  - `runtime.freq_mhz` populated;
  - `secret_values_logged=0`.
- Gateway ping: `wifi ping gateway` reached `wifi-ping-pass` with `3/3`
  packets and `0%` loss.
- Menu smoke: `screenmenu` accepted the updated menu.
- V2185 rollback: boot partition prefix SHA matched local V2185 image and
  post-rollback `version`/`status` verified
  `A90 Linux init 0.9.257 (v2185-network-ping-test)`.

## Notes

- The first `wifi connect` command was affected by serial/protocol noise
  (`A90P1 END marker not found`) before a valid result could be parsed. It was
  not used as the validation gate.
- A cleanup plus retry completed the same connect/DHCP/status path successfully.
- Physical button selection of `NETWORK > WIFI STATUS` was not captured; this
  remains UI polish evidence, not a Wi-Fi functionality blocker.

## Safety Scope

- Public report omits raw SSID, BSSID, PSK, private IP, gateway, and MAC-derived
  peer details.
- `wifi status` exposes only redacted connection label plus WPA/RSSI/link/freq
  metrics.
- Gateway ping was explicit and bounded; no unbounded external network test was
  run.
- No PMIC/GPIO/GDSC/regulator writes, eSoC notify/BOOT_DONE, PCI rescan,
  platform bind/unbind, or `/dev/subsys_esoc0` path was used.

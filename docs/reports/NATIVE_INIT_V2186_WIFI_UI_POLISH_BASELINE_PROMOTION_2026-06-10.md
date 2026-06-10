# Native Init V2186 Wi-Fi UI Polish Baseline Promotion

## Summary

- Promoted baseline: `A90 Linux init 0.9.258 (v2186-wifi-ui-polish)`.
- Run/build identity: `V2186`.
- Decision: `v2186-wifi-ui-polish-baseline-promotion-pass`.
- Result: PASS.
- Rollback image:
  `workspace/private/inputs/boot_images/boot_linux_v2186_wifi_ui_polish.img`.
- Rollback boot SHA256:
  `7a0db3bb76232f778869d3bf0788268f3a1942b230b094158dddf7a7d500fd32`.
- Previous baseline: `A90 Linux init 0.9.257 (v2185-network-ping-test)`.

## Promotion Basis

- Source build passed:
  `docs/reports/NATIVE_INIT_V2186_WIFI_UI_POLISH_SOURCE_BUILD_2026-06-10.md`.
- Live validation passed:
  `docs/reports/NATIVE_INIT_V2186_WIFI_UI_POLISH_LIVE_VALIDATION_2026-06-10.md`.
- Final promotion flash passed after the V2185 rollback proof:
  - local, pushed, and boot-partition readback SHA matched
    `7a0db3bb76232f778869d3bf0788268f3a1942b230b094158dddf7a7d500fd32`;
  - booted `A90 Linux init 0.9.258 (v2186-wifi-ui-polish)`;
  - post-boot `status` reported selftest `fail=0`.
- Passing private evidence directory:
  `workspace/private/runs/wifi/v2186-wifi-ui-polish-live-retry-20260610-082311`.
- The validation covered cleanup, carrier connect, DHCP, redacted runtime Wi-Fi
  status metrics, bounded gateway ping, `screenmenu`, rollback, and selftest.

## Promoted Contract

- Future rollback should target V2186 unless a test explicitly requires an older
  fallback.
- V2186 preserves the V2169+ boot/bridge/transport contract and the V2185
  network ping command path.
- V2186 adds clearer `NETWORK > WIFI STATUS` labels plus redacted WPA/RSSI/link
  speed/frequency runtime metrics.
- Public artifacts must continue to omit raw SSID, BSSID, PSK, private IP,
  gateway, and peer MAC details.

## Residual Work

- Physical button selection of `NETWORK > WIFI STATUS` and `NETWORK > PING TEST`
  is still not captured.
- Longer N-run or multi-hour Wi-Fi/data-path soak remains optional hardening, not
  a blocker for this promotion.

## Safety Scope

- No credential exposure is part of the promoted UI/status path.
- No Wi-Fi scan/connect/DHCP/ping action runs implicitly from status screens.
- No PMIC/GPIO/GDSC/regulator writes, eSoC notify/BOOT_DONE, PCI rescan,
  platform bind/unbind, or `/dev/subsys_esoc0` path is included.

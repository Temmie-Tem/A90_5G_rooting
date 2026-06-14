# Native Init V2184 Network UI P0/P1 Live Validation

## Summary

- Candidate tag: `v2184-network-ui-p0-p1`
- Parent baseline: `v2182-hud-menu-cleanup` source tree; rollback-safe image currently verified as `v2178-wifi-profile-autoconnect`.
- Type: live flash and smoke validation.
- Decision: `v2184-network-ui-p0-p1-live-smoke-pass`
- Result: PASS
- Reason: V2184 flashed, booted, verified `selftest fail=0`, exposed the new build marker, and the P0/P1 Wi-Fi backing commands passed.
- Evidence directory: `workspace/private/runs/ui/v2184-network-ui-p0-p1-live-20260609-100056`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2184_network_ui_p0_p1.img`
- Boot SHA256: `d4d274a4e2b5b27a8136d45d4f176ed6b4adc1a3eb1c0195fa1361f0005d83f5`
- Flashed boot partition prefix SHA256 matched the local image during `native_init_flash.py`.
- Device-visible init: `A90 Linux init 0.9.256 (v2184-network-ui-p0-p1)`.

## Smoke Results

- `version`: rc `0`, status `ok`.
- `status`: rc `0`, status `ok`, contains `selftest fail=0`.
- `selftest`: rc `0`, status `ok`, contains `fail=0`.
- `wifi status`: decision `wifi-status-wlan0-present`, `wlan0_present=1`, `secret_values_logged=0`.
- `wifi profile list`: decision `wifi-profile-list-ready`, `profile_count=3`, `secret_values_logged=0`.
- `wifi scan 1500`: decision `wifi-scan-pass`, `scan_result_count=12`, `credentials=0`, `connect=0`, `dhcp_routing=0`, `external_ping=0`.
- `screenmenu`: rc `0`, status `ok`, background HUD menu show request accepted.

## Safety Scope

- No Wi-Fi connect, DHCP, route/DNS install, credential readback, or external ping was run.
- The scan smoke was bounded to `1500ms` and reported `raw_results_redacted=1`.
- Raw scan details remain in screen/UI memory only for the app path; the serial command path reports counts and safety fields.

## Notes

- The device is currently flashed to V2184 test boot, not yet a promoted baseline.
- The local private `boot_linux_v2182_hud_menu_cleanup.img` file was previously regenerated and no longer matches the V2183 promotion SHA; use `boot_linux_v2178_wifi_profile_autoconnect.img` as the verified rollback image until V2184 is promoted or V2182 is restored from external backup.

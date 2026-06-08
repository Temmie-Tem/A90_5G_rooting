# Native Init V2179 V2178 Wi-Fi Profile Autoconnect Baseline Promotion

Date: `2026-06-09`

## Summary

- Run ID: `V2179`
- Promoted baseline tag: `v2178-wifi-profile-autoconnect`
- Native init: `A90 Linux init 0.9.253 (v2178-wifi-profile-autoconnect)`
- Decision: `v2179-v2178-wifi-profile-autoconnect-baseline-promoted`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2178_wifi_profile_autoconnect.img`
- Boot SHA256: `8ea6f468f997446e9fa3e80606db107ca27d067f3ee023ff45c2ecf159341047`
- Previous rollback image: `workspace/private/inputs/boot_images/boot_linux_v2174_wifi_urandom_connect.img`
- Previous rollback SHA256: `cda957e4302d66e407fc97a95932501f0ef2ac655ee264c94519111fece0b3ba`
- Source/build report: `docs/reports/NATIVE_INIT_V2178_WIFI_PROFILE_AUTOCONNECT_SOURCE_BUILD_2026-06-09.md`
- Earlier live validation report: `docs/reports/NATIVE_INIT_V2178_WIFI_PROFILE_AUTOCONNECT_LIVE_VALIDATION_2026-06-09.md`
- Final device state: V2178 flashed as the current baseline, autoconnect disabled, `selftest fail=0`

## P0 Fixes Included

- `autoconnect.log` is reset at the start of each autoconnect run instead of accumulating unrelated historical events.
- Valid autoconnect runs write `wifi-autoconnect-running` immediately, so long boot bring-up no longer exposes a stale prior `pass` or `disabled` result.
- Disabled/no-config boot paths write authoritative `autoconnect.result` and runtime summary state.
- `wifi profile list` deduplicates primary/cache profile names and reports `profile_duplicates_skipped` plus `profile_overflow_skipped`.
- `wifi status` now surfaces `runtime.decision` and the current `autoconnect.result` fields for UI/HUD/automation.
- HUD Wi-Fi line falls back to the latest runtime decision when `wlan0` is not connected.

## Live Validation Evidence

### Disabled Boot / Profile Inventory

After flashing the patched V2178 image with autoconnect disabled:

- `wifi autoconnect status`: `autoconnect=0`, `decision=wifi-autoconnect-disabled`.
- `wifi profile list`: `profile_count=1`, `profile_duplicates_skipped=1`, `decision=wifi-profile-list-ready`.
- `wifi status`: `autoconnect.decision=wifi-autoconnect-disabled`, `autoconnect.final_rc=0`, no stale `wifi-autoconnect-pass`.
- Selftest: `pass=11 warn=1 fail=0`.

### Boot Autoconnect Reproducibility

Patched V2178 was flashed and booted three times with explicit autoconnect enabled.
All three runs reached carrier plus DHCP without external ping.

| Run | Flash RC | Decision | Final RC | Carrier | IPv4 | Polls |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| 1 | `0` | `wifi-autoconnect-pass` | `0` | `1` | assigned | `13` |
| 2 | `0` | `wifi-autoconnect-pass` | `0` | `1` | assigned | `14` |
| 3 | `0` | `wifi-autoconnect-pass` | `0` | `1` | assigned | `13` |

One run hit a transient serial `AT` noise parse failure during polling; the bridge wrapper restarted and the same boot run still reached `wifi-autoconnect-pass`.

### Two-Band Profile Checks

Both private target bands were staged through `a90_wifi_profile_stage.py` with `secret_values_logged=0` and tested through `wifi autoconnect once <profile>`:

| Band | Observed Frequency | Connect | DHCP | Final Decision |
| --- | ---: | --- | --- | --- |
| 2.4 GHz | `2412` | `wifi-connect-carrier-up` | `wifi-dhcp-pass` | `wifi-autoconnect-pass` |
| 5 GHz | `5745` | `wifi-connect-carrier-up` | `wifi-dhcp-pass` | `wifi-autoconnect-pass` |

No raw SSID, PSK, BSSID, DHCP lease transcript, route gateway, DNS server, or external ping transcript is required in public reports.

### Rollback Safety

After the validation window:

- V2178 Wi-Fi state was cleaned with `wifi cleanup` and autoconnect was disabled.
- V2174 rollback image was flashed successfully.
- Rollback boot observed `A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`.
- Final rollback selftest: `pass=11 warn=1 fail=0`.

### Final Baseline Flash

After rollback safety was proven, the same V2178 image was flashed again as the current baseline:

- Local/remote/readback boot SHA256: `8ea6f468f997446e9fa3e80606db107ca27d067f3ee023ff45c2ecf159341047`.
- Device-visible version: `A90 Linux init 0.9.253 (v2178-wifi-profile-autoconnect)`.
- `wifi autoconnect status`: `autoconnect=0`, `decision=wifi-autoconnect-disabled`.
- `wifi status`: `wlan0_present=0`, `autoconnect.decision=wifi-autoconnect-disabled`, no running supplicant.
- Final selftest: `pass=11 warn=1 fail=0`.

## Private Artifacts

- `workspace/private/runs/wifi/v2179-promotion-validation-20260609/`
- `workspace/private/builds/native-init/v2178-wifi-profile-autoconnect-test-boot/manifest.json`
- `workspace/private/inputs/boot_images/boot_linux_v2178_wifi_profile_autoconnect.img`

## Scope And Residual Risk

- V2178 promotes profile-backed connect/DHCP, boot autoconnect, and redacted status/HUD surfaces.
- Boot autoconnect remains explicit opt-in and does not run external ping.
- External connectivity, credentials, and unbounded network activity remain outside baseline boot behavior.
- Wi-Fi bring-up can take roughly three minutes on this route because the firmware/helper window dominates; automation must poll the machine-readable result rather than assume early failure.
- Serial bridge `AT` noise can still corrupt an individual cmdv1 exchange; current runner behavior is to restart the bridge and retry the command, which was sufficient during V2179.
- `v2174-wifi-urandom-connect` remains the immediate rollback image.

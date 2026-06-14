# Native Init V2178 Wi-Fi Profile Autoconnect Live Validation

## Summary

- Candidate tag: `v2178-wifi-profile-autoconnect`
- Init: `A90 Linux init 0.9.253 (v2178-wifi-profile-autoconnect)`
- Latest patched boot SHA256: `8ea6f468f997446e9fa3e80606db107ca27d067f3ee023ff45c2ecf159341047`
- Result: PASS; superseded by V2179 P0/P1 promotion validation for final baseline SHA.
- Rollback baseline: `A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`
- Final rollback selftest: `fail=0`

## Initial Finding

The first live V2178 image exposed a real autoconnect ordering bug:

- `wifi autoconnect once default` called `wifi scan` before `wlan0` existed.
- `wifi scan` does not wait for `wlan0`; it immediately tried link-up and failed with `link_up_errno=19`.
- Decision: `wifi-autoconnect-scan-failed`

Fix applied before continuing validation:

- `wifi_run_autoconnect_sequence()` now waits for `wlan0` before a configured pre-connect scan.
- The wait is background-safe and writes a clear `wifi-autoconnect-wlan0-timeout` result on timeout.

## Live Gates

### Gate 1: patched V2178 flash

- Local image SHA256 matched the flashed boot block prefix.
- V2178 booted and responded over cmdv1.
- Selftest: `pass=11 warn=1 fail=0`
- Transport: `transport.preferred=tcpctl`

### Gate 2: secret-safe profile staging

- Helper: `workspace/public/src/scripts/revalidation/a90_wifi_profile_stage.py`
- Decision: `wifi-profile-stage-pass`
- Profile: `default`
- Root: persistent SD workspace
- `secret_values_logged=0`
- Native profile status decision: `wifi-profile-ready`
- Native config prepare decision: `wifi-config-supplicant-prepared`

### Gate 3: explicit autoconnect once

Command: `wifi autoconnect once default`

Observed result:

- `config_decision=wifi-autoconnect-ready`
- `autoconnect.wlan0_wait_elapsed_ms=70843`
- scan completed: `scan_result_count=9`, `decision=wifi-scan-pass`
- connect completed: `decision=wifi-connect-carrier-up`
- DHCP completed: `decision=wifi-dhcp-pass`
- final decision: `wifi-autoconnect-pass`
- `secret_values_logged=0`

No external ping was run.

### Gate 4: boot-background autoconnect

Setup:

- `wifi autoconnect enable default` returned `decision=wifi-autoconnect-enabled`.
- `wifi autoconnect status` showed `autoconnect=1` and `decision=wifi-autoconnect-ready`.
- Patched V2178 was re-flashed and booted again.

Observed result after background worker completed:

- `/cache/a90-wifi/autoconnect.result` decision: `wifi-autoconnect-pass`
- `connect_rc=0`
- `dhcp_rc=0`
- `final_rc=0`
- `carrier_up=1`
- `default_route_present=1`
- `nameserver_count=2`
- `secret_values_logged=0`
- `wifi status`: `wlan0_present=1`, `operstate=up`, `carrier=1`, IPv4 assigned, `supplicant.process_count=1`

No external ping was run.

### Gate 5: cleanup and rollback

Post-test cleanup on V2178:

- `wifi autoconnect disable` returned `decision=wifi-autoconnect-disabled`.
- `wifi cleanup` returned `decision=wifi-cleanup-done`.
- `wifi status` showed `carrier=0`, no IPv4, and `supplicant.process_count=0`.

Rollback:

- Flashed `workspace/private/inputs/boot_images/boot_linux_v2174_wifi_urandom_connect.img`.
- Booted `A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`.
- Final status selftest: `pass=11 warn=1 fail=0`.

## Artifacts

Private artifacts:

- `workspace/private/runs/wifi/a90-wifi-profile-stage-20260609-012919/`
- `workspace/private/runs/wifi/a90-wifi-profile-stage-20260609-013200/`
- `workspace/private/runs/wifi/v2178-autoconnect-once-live/`
- `workspace/private/runs/wifi/v2178-autoconnect-once-live-patched/`
- `workspace/private/runs/wifi/v2178-boot-autoconnect-live/`

Generated image/build artifacts:

- `workspace/private/inputs/boot_images/boot_linux_v2178_wifi_profile_autoconnect.img`
- `workspace/private/builds/native-init/v2178-wifi-profile-autoconnect-test-boot/manifest.json`

## Residual Risks

- V2179 fixed the append-only autoconnect log, stale result, and profile-list duplicate issues found here.
- Boot autoconnect can take roughly three minutes because the firmware/helper path dominates; status automation must poll `autoconnect.decision` until a terminal result.
- Serial `AT` noise can still corrupt an individual cmdv1 exchange. V2179 mitigated this at the runner layer with bridge restart/retry, not in the device command parser.

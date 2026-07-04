# Server Distro Wi-Fi STA Upstream WSTA29 Confirmed Retry Scan Blocked

- Date: `2026-07-04`
- Decision: `wsta25-blocked-helper-confirmed-autoconnect`
- Resident under test: `A90 Linux init 0.11.143 (v3387-wifi-uplink-service-redacted)`
- Precondition evidence: WSTA28 scan gate pass
  `workspace/private/runs/server-distro/wsta28-reboot-materialization-gate-20260704T025013Z/wsta28_result.json`
- Confirmed retry evidence:
  `workspace/private/runs/server-distro/wsta25-confirmed-autoconnect-live-20260704T025506Z/wsta25_result.json`

## Scope

Retry the existing WSTA25 confirmed live path after WSTA28 restored the native scan precondition.
This unit used the already-gated WSTA25 live runner and did not start public exposure or external
ping.  After the retry, autoconnect was disabled again and native Wi-Fi cleanup was run.

## Precondition

WSTA28 had just passed:

- native reboot returned V3387 with `selftest fail=0`;
- nested WSTA27 materialized `wlan0`;
- direct native scan returned `decision=wifi-scan-pass`;
- `scan_result_count=11`;
- `scan_engine_ok=true`;
- `scan_has_bss=true`;
- `link_up_errno=0`;
- `trigger_errno=0`;
- autoconnect was still disabled.

Immediately before retrying WSTA25, native status showed V3387 with clean selftest, autoconnect
disabled, `wlan0_present=1`, no IPv4, no default route, and no supplicant process.

## Confirmed Retry Result

Preparation:

- `wifi autoconnect enable` returned `decision=wifi-autoconnect-enabled`.
- WSTA25 helper status then reported:
  - `autoconnect_config_decision=wifi-autoconnect-ready`
  - `autoconnect_enabled=1`
  - `autoconnect_ready=1`
  - `config_profile_present=1`
  - `profile_valid=1`
  - `external_ping_execution=0`
  - `public_tunnel=0`
  - `secret_values_logged=0`

Confirmed helper:

- The confirmed helper request was sent through the redacted stdin executor.
- Helper return code was `10`.
- Native response:
  - `native_wifi_uplink_client_decision=native-wifi-uplink-client-native-failed`
  - `native_wifi_uplink_client_native_rc=-22`
  - `native_wifi_uplink_client_requested_op=autoconnect-confirmed`
  - `decision=wifi-uplink-service-autoconnect-failed`
  - `autoconnect_decision=wifi-autoconnect-scan-failed`
  - `rc=-22`
  - `connect_rc=-22`
  - `dhcp_rc=0`
  - `final_rc=-22`
  - `carrier_up=0`
  - `default_route_present=0`
  - `external_ping_execution=0`
  - `public_tunnel=0`
  - `secret_values_logged=0`

The WSTA25 runner cleanup passed, including native service stop, helper cleanup, chroot/dropbear/loop
cleanup, final V3387 check, and final selftest.

Post-retry cleanup:

- `wifi autoconnect disable` returned `decision=wifi-autoconnect-disabled`.
- `wifi cleanup` returned `decision=wifi-cleanup-done`.
- Final redacted `wifi status` showed no IPv4, no default route, no supplicant process, and
  `decision=wifi-status-wlan0-present`.
- Final native selftest remained `fail=0`.

## Interpretation

WSTA29 narrows the remaining blocker: WSTA28 proves the direct native scan engine can be restored,
but WSTA25 still fails inside the native autoconnect pre-scan.  In source, `wifi_run_autoconnect_sequence`
calls `a90_wifi_scan_once(5000)` before `wifi_connect_profile_with_carrier_timeout`; if that pre-scan
returns negative, the code writes `wifi-autoconnect-scan-failed` and never starts the actual
supplicant/connect path.

So the next fix should target the autoconnect path itself, not Debian helper transport.  A bounded
source unit should either:

- add an immediate materialization/scan gate inside the WSTA25 runner right before sending the
  confirmed request and abort before confirmed request if it fails; or
- update native autoconnect to use the same materialization recovery that WSTA28 proved before
  treating pre-scan `-22` as terminal.

The second option likely requires a new native build/flash; the first option can be host-side but may
only avoid bad attempts rather than fixing the native autoconnect sequence.

## Safety

No boot flash, switch-root, successful association, DHCP lease, default route, external ping, public
tunnel, raw credential logging, SSID, PSK, BSSID, MAC, private IP, gateway, DNS server, public URL, or
confirm-token value is recorded in public artifacts.  Raw transcripts remain under
`workspace/private/`.

## Validation

- WSTA28 scan-green precondition:
  - `wsta28-reboot-materialization-scan-gate-pass`
- WSTA25 confirmed retry:
  - `python3 workspace/public/src/scripts/server-distro/run_wsta25_confirmed_autoconnect_live.py --allow-confirmed-live --ack-credentialed-wifi --confirm-token <redacted>`
  - `wsta25-blocked-helper-confirmed-autoconnect`
- Post-retry cleanup:
  - `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi autoconnect disable`
  - `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi cleanup`
  - `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi autoconnect status`
  - `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi status`
  - `python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest`
- `git diff --check`

## Next

WSTA30 should add a same-run pre-confirm scan/materialization guard to the WSTA25 runner so it will
not send confirmed autoconnect when the native scan state has already gone stale.  If that guard
proves the state goes stale between WSTA28 and WSTA25, the next native build should move
materialization recovery into `wifi_run_autoconnect_sequence` before the pre-scan returns terminal
`wifi-autoconnect-scan-failed`.

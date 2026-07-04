# Server Distro Wi-Fi STA Upstream WSTA30 Pre-Confirm Scan Guard

- Date: `2026-07-04`
- Decision: `wsta25-blocked-pre-confirm-scan`
- Resident under test: `A90 Linux init 0.11.143 (v3387-wifi-uplink-service-redacted)`
- Evidence:
  `workspace/private/runs/server-distro/wsta25-confirmed-autoconnect-live-20260704T030140Z/wsta25_result.json`

## Scope

Add a same-run native scan guard to the WSTA25 confirmed-autoconnect live runner.  The guard runs
after the redacted helper status proves autoconnect readiness and before the confirmed helper request
is sent.  If the native scan engine is not ready, the runner records a blocked decision and does not
send the confirmed request.

This unit did not perform a boot flash, switch-root, userdata formatter action, successful association,
DHCP lease, default route, external ping, or public tunnel action.

## Source Changes

`run_wsta25_confirmed_autoconnect_live.py` now:

- imports the WSTA15 scan summarizer;
- adds `pre_confirm_scan_window` with bounded `wifi scan` attempts;
- classifies failed pre-confirm scan as `wsta25-blocked-pre-confirm-scan`;
- records `helper_confirmed.skipped=true` with `reason=pre-confirm-scan-not-ready`;
- leaves `helper_confirmed_attempted=false` when the guard blocks.

Focused WSTA25 tests now cover the new classification, scan-engine predicate, and source-surface
markers.

## Live Result

The WSTA25 readiness gate passed:

- `explicit_live_gate=true`
- `confirm_token_supplied=true`
- `confirm_token_matches=true`
- `helper_status_pass=true`
- `autoconnect_ready=true`
- `service_start_pass=true`

The pre-confirm native scan guard ran two bounded `wifi scan 5000` attempts and both failed before
any confirmed helper request was sent:

- best scan decision: `wifi-scan-trigger-failed`
- `scan_engine_ok=false`
- `scan_has_bss=false`
- `cmd_rc=-22`
- `link_up_rc=1`
- `link_up_errno=0`
- `ifindex=9`
- `netlink_open=1`
- `family_id=19`
- `trigger_rc=-1`
- `trigger_errno=22`

Because the guard failed:

- `helper_confirmed_attempted=false`
- `helper_confirmed_pass=false`
- `helper_confirmed.reason=pre-confirm-scan-not-ready`
- the confirmed `autoconnect` request was not sent.

Cleanup and health:

- native uplink-service stop passed;
- helper cleanup passed;
- service directory cleanup passed;
- mount, loop node, and dropbear postcheck were absent;
- final version was still V3387;
- final selftest remained `fail=0`.

Post-run operator cleanup also restored autoconnect disabled state and ran native Wi-Fi cleanup before
rechecking redacted Wi-Fi status and selftest.

## Interpretation

WSTA30 confirms that WSTA29 was not only a Debian-helper or confirm-token problem.  The direct native
scan state can go stale before the confirmed request, even after WSTA28 previously proved a scan-green
state.  This run changed the observed failure from the earlier link-up failure to a later nl80211 scan
trigger `EINVAL`: the interface had an ifindex and netlink family, but `trigger_rc=-1` /
`trigger_errno=22`.

The host-side guard is useful because it prevents another credentialed confirmed request when the
native scan engine is already not ready.  It does not by itself fix the underlying connection path.

## Safety

No boot flash, switch-root, successful association, DHCP lease, default route, external ping, public
tunnel, raw credential logging, SSID, PSK, BSSID, MAC, private IP, gateway, DNS server, public URL, or
confirm-token value is recorded in public artifacts.  Raw transcripts remain under `workspace/private/`.

## Validation

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_wsta25_confirmed_autoconnect_live.py tests/test_server_distro_wsta25_confirmed_autoconnect_live.py`
- `PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_server_distro_wsta25_confirmed_autoconnect_live`
- `python3 workspace/public/src/scripts/server-distro/run_wsta25_confirmed_autoconnect_live.py --allow-confirmed-live --ack-credentialed-wifi --confirm-token <redacted>`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi autoconnect disable`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi cleanup`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi autoconnect status`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi status`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest`
- `git diff --check`

## Next

WSTA31 should move the recovery into the native autoconnect path.  The bounded native change should
refresh or recover materialization/scan state before `wifi_run_autoconnect_sequence` treats a pre-scan
`-22` as terminal.  The host guard should stay as a fail-closed safety layer, but the actual fix needs
to be native-side if confirmed autoconnect is to progress to association.

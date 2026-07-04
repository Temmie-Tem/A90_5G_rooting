# Server Distro Wi-Fi STA Upstream WSTA31 Native Scan Recovery V3388 Live

- Date: `2026-07-04`
- Decision: `wsta25-blocked-helper-confirmed-autoconnect`
- Candidate: `A90 Linux init 0.11.144 (v3388-wifi-autoconnect-scan-recovery)`
- Boot image:
  `workspace/private/inputs/boot_images/boot_linux_v3388_wifi_autoconnect_scan_recovery.img`
- Boot SHA256: `2971367ef2421161ee18a30a2eeb8088fa1a04b377dbfdf208aa9130cfa6d1f9`
- Source-build report:
  `docs/reports/NATIVE_INIT_V3388_WIFI_AUTOCONNECT_SCAN_RECOVERY_SOURCE_BUILD_2026-07-04.md`
- Live evidence:
  `workspace/private/runs/server-distro/wsta25-confirmed-autoconnect-live-20260704T031912Z/wsta25_result.json`

## Scope

Move WSTA30's scan-stale handling into native init.  V3388 adds one bounded native autoconnect
recovery path: when the pre-connect scan fails, native init runs Wi-Fi cleanup, performs the already
proven AP-iftype add/delete materialization probe, and retries scan once before treating the scan
failure as terminal.

The WSTA25 live runner was then rerun against V3388 with `--skip-pre-confirm-scan-gate` so the
credentialed confirmed request would reach native autoconnect and exercise the new native boundary.
Public exposure and external ping stayed disabled.

## Source And Build

Changed public source:

- `workspace/public/src/native-init/a90_wifi.c`
- `workspace/public/src/scripts/server-distro/a90_native_wifi_uplink_client.sh`
- `workspace/public/src/scripts/server-distro/run_wsta24_native_wifi_uplink_client.py`
- `workspace/public/src/scripts/server-distro/run_wsta25_confirmed_autoconnect_live.py`
- `workspace/public/src/scripts/server-distro/run_wsta26_scan_failure_diagnostic.py`
- focused tests and V3388 builder.

V3388 build validation completed:

- AArch64 helper/native-init compile;
- required-string audit for the new scan-recovery fields;
- preserved ramdisk overlay;
- boot image pack;
- SHA256 capture.

## Flash Gate

Rollback image checks passed before flash:

- v2321 SHA matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`;
- v2237 SHA matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`;
- v48 was present and hashed.

`native_init_flash.py` was run from native mode with the V3388 SHA pinned.  The helper rebooted to
recovery, pushed the sealed image, verified remote SHA, wrote only boot, verified boot-prefix SHA,
rebooted system, and verified native V3388 over cmdv1.  Total helper time was `62.040s`.  Post-flash
native health reported V3388 and `selftest fail=0`.

## Live Result

Pre-run:

- V3388 boot health passed;
- autoconnect config/profile was ready;
- autoconnect was explicitly enabled;
- WSTA25 explicit live gate and confirm token matched;
- pre-confirm scan guard was explicitly skipped for this native recovery proof.

Confirmed helper:

- `helper_confirmed_attempted=true`
- `helper_confirmed_pass=false`
- `native_wifi_uplink_client_requested_op=autoconnect-confirmed`
- `native_wifi_uplink_client_native_rc=-107`
- `decision=wifi-uplink-service-autoconnect-failed`
- `autoconnect_decision=wifi-autoconnect-connect-failed`
- `connect_rc=-107`
- `dhcp_rc=0`
- `final_rc=-107`
- `carrier_up=0`
- `default_route_present=0`
- `external_ping_execution=0`
- `public_tunnel=0`
- `secret_values_logged=0`

Scan-recovery telemetry:

- `scan_recovery_attempted=0`
- `scan_recovery_decision=wifi-autoconnect-scan-recovery-not-attempted`
- `scan_recovery_first_scan_rc=0`
- `scan_recovery_rc=0`
- `scan_recovery_rescan_rc=0`
- `scan_recovery_success=0`

Interpretation: the scan failure that blocked WSTA25/WSTA29 did not reproduce in this V3388 run.
Native autoconnect reached the connect/carrier stage and then failed with `-107`.  Therefore WSTA31
does not prove the recovery branch by execution, but it does prove the V3388 candidate boots cleanly,
keeps the credential/public boundaries intact, exposes the new redacted recovery fields through the
uplink-service response, and moves the current live blocker from native scan to association/carrier.

## Cleanup

The runner stopped the native uplink service, cleaned helper staging, and passed mount/loop/dropbear
postcheck.  Post-run cleanup then disabled autoconnect, ran native Wi-Fi cleanup, verified no IPv4,
no default route, no supplicant process, and final `selftest fail=0`.

## Safety

No forbidden partition was touched.  The only flash was the checked-helper boot-image flash.  No
public tunnel, external ping, raw credential logging, SSID, PSK, BSSID, MAC, gateway, DNS server,
public URL, or confirm-token value is recorded in public artifacts.  No successful association, DHCP
lease, default route, or public exposure occurred.  Raw transcripts remain under `workspace/private/`.

## Validation

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile ...`
- `sh -n workspace/public/src/scripts/server-distro/a90_native_wifi_uplink_client.sh`
- `PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_build_native_init_boot_v3388_wifi_autoconnect_scan_recovery tests.test_native_wifi_uplink_service_source tests.test_server_distro_wsta24_native_wifi_uplink_client tests.test_server_distro_wsta25_confirmed_autoconnect_live tests.test_server_distro_wsta26_scan_failure_diagnostic`
- `aarch64-linux-gnu-gcc -fsyntax-only -Wall -Wextra -Werror ... workspace/public/src/native-init/a90_wifi.c`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/build_native_init_boot_v3388_wifi_autoconnect_scan_recovery.py`
- `python3 workspace/public/src/scripts/revalidation/native_init_flash.py ... --expect-sha256 2971367ef2421161ee18a30a2eeb8088fa1a04b377dbfdf208aa9130cfa6d1f9 --expect-version 0.11.144 --verify-protocol cmdv1 --from-native`
- `python3 workspace/public/src/scripts/server-distro/run_wsta25_confirmed_autoconnect_live.py --allow-confirmed-live --ack-credentialed-wifi --confirm-token <redacted> --skip-pre-confirm-scan-gate --service-lifetime-ms 360000 --confirmed-timeout-sec 300`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi autoconnect disable`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi cleanup`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py wifi status`
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest`

## Next

WSTA32 should target the new downstream blocker: native connect/carrier diagnostics.  Add or expose
redacted autoconnect result fields for `wpa_state`, carrier wait result/elapsed, control socket status,
and scan/connect command outcomes so the helper path can explain `connect_rc=-107` without requiring
raw console transcripts.

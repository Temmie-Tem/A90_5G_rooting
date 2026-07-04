# WSTA61 Native Persistent-State Screen Source Build

- Date: 2026-07-04
- Scope: native WSTA redacted persistent-state screen source/build
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta61-native-persistent-state-screen-source-build-pass`

## Summary

WSTA61 implements the WSTA52 native HUD/screen rung as a display-only source/build
unit.  The existing WSTA screen was publish-runbook oriented; it now shows the
redacted persistent exposure state contract:

```text
STATE: PUBLIC_OFF LEASE-GATED
PROOF: WSTA55 START / WSTA58 RENEW
URL: REDACTED PRIVATE-RUN ONLY
NATIVE: DISPLAY-ONLY NO CONNECT
```

The screen does not read or display raw public URLs, Wi-Fi identifiers, network
addresses, credentials, or confirm-token values.  It also does not add any native
connect, DHCP, public tunnel, reboot, flash, or userdata behavior.

## Source Change

Updated:

- `workspace/public/src/native-init/a90_app_network.c`
- `workspace/public/src/scripts/server-distro/run_wsta24_native_wifi_uplink_client.py`
- `tests/test_native_wsta_operator_screenapp_source.py`
- `tests/test_server_distro_wsta24_native_wifi_uplink_client.py`
- `tests/test_server_distro_wsta26_scan_failure_diagnostic.py`

Added:

- `workspace/public/src/scripts/revalidation/build_native_init_boot_v3396_wsta_persistent_state_screen.py`
- `tests/test_build_native_init_boot_v3396_wsta_persistent_state_screen.py`
- `docs/reports/NATIVE_INIT_V3396_WSTA_PERSISTENT_STATE_SCREEN_SOURCE_BUILD_2026-07-04.md`

The shared WSTA native lineage gate now accepts V3396:

```text
version=0.11.152
build=v3396-wsta-persistent-state-screen
```

## Build Evidence

V3396 source build completed successfully:

```text
init=A90 Linux init 0.11.152 (v3396-wsta-persistent-state-screen)
boot_image=workspace/private/inputs/boot_images/boot_linux_v3396_wsta_persistent_state_screen.img
boot_sha256=499f2b348d5d6ed9a5d219043d4fbef25dc4c158f542a4eec014b293c5e9872f
init_sha256=ac4532ad7ebff899ddd2de24d7702ac53635b66418217e8c1eba7881c85b51ca
candidate_type=wsta-persistent-state-screen
```

Candidate manifest summary:

```text
state=PUBLIC_OFF
lease_policy=host-private-lease-gated
proofs=WSTA55 short start + WSTA58 renew/manual-stop
public_url_display=redacted-private-run-only
native_public_action=none
redacted_result_source=WSTA48
```

## Safety

- No boot image was flashed.
- No forbidden partition was touched.
- No native reboot, Wi-Fi association, DHCP, public tunnel, public smoke,
  userdata action, switch-root, or external service action ran.
- The committed report and source changes contain no raw public URL, public
  tunnel domain, confirm-token value, Wi-Fi credential, SSID, BSSID, MAC, IP,
  gateway, DNS, lease id value, or device serial.
- Generated boot image and binaries remain private-only under `workspace/private/`.

## Validation

Focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_native_wsta_operator_screenapp_source \
  tests.test_build_native_init_boot_v3395_wsta_screenapp_live \
  tests.test_build_native_init_boot_v3396_wsta_persistent_state_screen \
  tests.test_server_distro_wsta24_native_wifi_uplink_client \
  tests.test_server_distro_wsta26_scan_failure_diagnostic \
  tests.test_server_distro_wsta58_renewal_manual_stop_proof
```

Result: `Ran 29 tests ... OK`

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_native_init_boot_v3396_wsta_persistent_state_screen.py \
  workspace/public/src/scripts/server-distro/run_wsta24_native_wifi_uplink_client.py
```

Result: pass

V3396 builder execution: pass.

`git diff --check`: pass.

## Next

If the operator wants live visual confirmation, flash the exact V3396 boot image
through `native_init_flash.py`, health-check V3396, run `screenapp wsta` and
`screenapp dpublic`, verify the new redacted markers, then keep public exposure
off.  Otherwise continue the persistent exposure ladder without a third WSTA58
live retry.

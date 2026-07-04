# WSTA80 Persistent Operator Execute Gate Source

- Date: 2026-07-04
- Scope: host-only execute gate from WSTA79 status to WSTA58
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta80-persistent-operator-execute-gate-preflight-pass`

## Summary

WSTA80 consumes a private WSTA79 READY status, reloads the referenced WSTA78
operator packet, validates the WSTA58 command template, and writes a default-off
execution gate.

This is the concrete bridge between the WSTA72-WSTA79 operator packet pipeline
and the existing WSTA58 renewal/manual-stop live runner.  It proves that a
current WSTA79 status can become a WSTA58-ready handoff, while keeping WSTA58
execution locked behind the full explicit live acknowledgement stack.

Default WSTA80 execution does not replace token placeholders, start a tunnel,
touch the device, connect Wi-Fi, run DHCP, run public smoke, or execute WSTA58.

## Source Change

Added:

- `workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py`
- `tests/test_server_distro_wsta80_persistent_operator_execute_gate.py`

The runner is fail-closed until a private WSTA79 status is supplied:

```text
python3 workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py \
  --wsta79-operator-packet-status-json workspace/private/runs/server-distro/<wsta79-run>/wsta79_operator_packet_status.json
```

Optional WSTA58 delegation is present in source, but it requires all of:

```text
--execute-wsta58-from-status
--allow-operator-live
--allow-native-reboot
--allow-public-live
--ack-credentialed-wifi
--ack-public-exposure
--force-ttl-expiry-proof
--force-manual-stop-proof
--native-confirm-token <native-confirm-token>
--public-confirm-token <public-confirm-token>
```

WSTA80 does not write confirm-token values to its public summary.

## Gate State

```text
READY_FOR_EXPLICIT_WSTA58_LIVE_GATE
```

This state requires:

- WSTA79 decision pass.
- WSTA79 status `READY_TO_RUN_DEFAULT_OFF`.
- WSTA79 `packet_match=true`.
- WSTA79 `template_match=true`.
- Referenced WSTA78 packet decision pass.
- Referenced WSTA58 command template contains placeholders, not raw token values.

## Private Smoke

Private smoke directory:

```text
workspace/private/runs/server-distro/wsta80-execute-gate-smoke-20260704T113919Z
```

Observed flow:

```text
WSTA72 prepare-to-arm
WSTA73 arming packet
WSTA75 arming inventory
WSTA76 launch brief
WSTA77 launch brief summary
WSTA78 operator packet
WSTA79 operator packet status
WSTA80 execute gate preflight
```

Observed WSTA80 result:

```text
decision=wsta80-persistent-operator-execute-gate-preflight-pass
state=READY_FOR_EXPLICIT_WSTA58_LIVE_GATE
selected_wsta73_arming_packet=workspace/private/runs/server-distro/wsta80-execute-gate-smoke-20260704T113919Z/packet/wsta73_arming_packet.json
selected_wsta76_launch_brief=workspace/private/runs/server-distro/wsta80-execute-gate-smoke-20260704T113919Z/brief/wsta76_launch_brief.json
initial_seconds_remaining=295
packet_match=true
template_match=true
ack_count=7
guardrail_count=5
live_execution_requested=false
public_url_value_logged=false
secret_values_logged=0
```

Generated gate:

```text
workspace/private/runs/server-distro/wsta80-execute-gate-smoke-20260704T113919Z/gate/wsta80_execute_gate.json
workspace/private/runs/server-distro/wsta80-execute-gate-smoke-20260704T113919Z/gate/wsta80_execute_gate.md
```

## Safety

- No boot image was built or flashed.
- No forbidden partition was touched.
- No device command, native reboot, Wi-Fi association, DHCP, public tunnel,
  public smoke, userdata action, switch-root, or external service action ran.
- WSTA80 default mode does not call WSTA58.
- WSTA80 live delegation is source-present but explicit-gated and tested with a
  mocked WSTA58 call only.
- The runner has no `native_init_flash.py` or `a90ctl.py` call path.
- Redaction checks are applied to the public summary and generated Markdown.
- The committed report/source/test changes contain no raw public URL, public
  tunnel domain, confirm-token value, Wi-Fi credential, SSID, BSSID, MAC, IP,
  gateway, DNS, lease id value, or device serial.
- Raw private prepare-to-arm outputs, WSTA73 packets, WSTA75 inventories,
  WSTA76 briefs, WSTA77 summaries, WSTA78 packets, WSTA79 statuses, and WSTA80
  gate artifacts remain under `workspace/private/`.

## Validation

Compile check:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py \
  tests/test_server_distro_wsta80_persistent_operator_execute_gate.py
```

Result: pass

WSTA80 focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta80_persistent_operator_execute_gate
```

Result: `Ran 9 tests ... OK`

Focused WSTA52-WSTA80 regression:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta52_persistent_exposure_design \
  tests.test_server_distro_wsta53_persistent_exposure_plan \
  tests.test_server_distro_wsta54_private_lease_artifact \
  tests.test_server_distro_wsta55_short_lived_public_proof \
  tests.test_server_distro_wsta58_renewal_manual_stop_proof \
  tests.test_server_distro_wsta63_persistent_session_controller \
  tests.test_server_distro_wsta64_persistent_session_readiness_audit \
  tests.test_server_distro_wsta65_persistent_session_status \
  tests.test_server_distro_wsta66_persistent_session_retire \
  tests.test_server_distro_wsta67_persistent_session_inventory \
  tests.test_server_distro_wsta68_persistent_session_bulk_retire \
  tests.test_server_distro_wsta69_persistent_session_snapshot \
  tests.test_server_distro_wsta70_persistent_session_launch_manifest \
  tests.test_server_distro_wsta71_persistent_launch_readiness_audit \
  tests.test_server_distro_wsta72_persistent_prepare_to_arm \
  tests.test_server_distro_wsta73_persistent_arming_packet \
  tests.test_server_distro_wsta74_persistent_arming_status \
  tests.test_server_distro_wsta75_persistent_arming_inventory \
  tests.test_server_distro_wsta76_persistent_launch_brief \
  tests.test_server_distro_wsta77_persistent_launch_brief_summary \
  tests.test_server_distro_wsta78_persistent_operator_packet \
  tests.test_server_distro_wsta79_persistent_operator_packet_status \
  tests.test_server_distro_wsta80_persistent_operator_execute_gate
```

Result: `Ran 177 tests ... OK`

Fresh WSTA72 + WSTA73 + WSTA75 + WSTA76 + WSTA77 + WSTA78 + WSTA79 + WSTA80
private smoke: pass.

## Next

The default-off persistent exposure pipeline now reaches a concrete WSTA58
execute gate without starting public exposure.  The next meaningful move should
be either an explicitly selected WSTA80/WSTA58 live proof with fresh private
tokens, or native/appliance UI integration that displays this execute-gate state
without auto-starting public exposure.

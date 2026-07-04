# WSTA78 Persistent Operator Packet Source

- Date: 2026-07-04
- Scope: host-only operator packet for WSTA77-selected launch briefs
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta78-persistent-operator-packet-pass`

## Summary

WSTA78 consumes a private WSTA77 launch brief summary, reruns WSTA77 against
the original private scan root, selects a fresh READY brief, loads the fresh
WSTA76 recheck brief, and writes a compact operator packet.

This packet is the explicit default-off handoff artifact for an operator who
may later choose to run WSTA58 manually.  It contains the WSTA58 command
template, required placeholder replacements, acknowledgements, abort
conditions, cleanup expectations, and WSTA78-specific execution guardrails.

WSTA78 does not replace token placeholders, start a tunnel, touch the device,
connect Wi-Fi, run DHCP, run public smoke, or execute WSTA58.

## Source Change

Added:

- `workspace/public/src/scripts/server-distro/run_wsta78_persistent_operator_packet.py`
- `tests/test_server_distro_wsta78_persistent_operator_packet.py`

The runner is fail-closed until a private WSTA77 summary is supplied:

```text
python3 workspace/public/src/scripts/server-distro/run_wsta78_persistent_operator_packet.py \
  --wsta77-launch-summary-json workspace/private/runs/server-distro/<wsta77-run>/wsta77_launch_brief_summary.json \
  --ready-index 0
```

WSTA78 never trusts the supplied summary as fresh.  It extracts the original
scan root, reruns WSTA77 into a private recheck directory, sorts the fresh READY
briefs, and applies WSTA78's `--ready-index` only after that recheck.  This
keeps a final selection error distinct from a stale/no-ready recheck result.

## Packet State

```text
READY_OPERATOR_PACKET_DEFAULT_OFF
```

The packet includes:

- `source_wsta77_summary`
- `fresh_wsta77_summary`
- `selected_wsta76_launch_brief`
- `fresh_wsta76_launch_brief`
- `selected_wsta73_arming_packet`
- `wsta58_live_command_template`
- `operator_required_replacements`
- `operator_acknowledgements_required`
- `abort_conditions`
- `cleanup_expectations`
- `operator_preflight_checks`
- `execution_guardrails`

The guardrails are:

```text
wsta78-does-not-execute-live
rerun-wsta78-if-time-elapsed-before-live
replace-placeholders-out-of-band-only
run-wsta58-only-with-explicit-operator-intent
verify-public-off-after-wsta58
```

## Private Smoke

Private smoke directory:

```text
workspace/private/runs/server-distro/wsta78-operator-packet-smoke-20260704T112439Z
```

Observed flow:

```text
WSTA72 prepare-to-arm
WSTA73 arming packet
WSTA75 arming inventory
WSTA76 launch brief
WSTA77 launch brief summary
WSTA78 operator packet
```

Observed WSTA78 result:

```text
decision=wsta78-persistent-operator-packet-pass
state=READY_OPERATOR_PACKET_DEFAULT_OFF
ready_for_live=true
selected_wsta73_arming_packet=workspace/private/runs/server-distro/wsta78-operator-packet-smoke-20260704T112439Z/packet/wsta73_arming_packet.json
selected_wsta76_launch_brief=workspace/private/runs/server-distro/wsta78-operator-packet-smoke-20260704T112439Z/brief/wsta76_launch_brief.json
fresh_wsta76_launch_brief=workspace/private/runs/server-distro/wsta78-operator-packet-smoke-20260704T112439Z/operator/wsta77-recheck/brief-000/wsta76-recheck/wsta76_launch_brief.json
initial_seconds_remaining=296
ack_count=7
guardrail_count=5
live_execution_requested=false
public_url_value_logged=false
secret_values_logged=0
```

Generated packet:

```text
workspace/private/runs/server-distro/wsta78-operator-packet-smoke-20260704T112439Z/operator/wsta78_operator_packet.json
workspace/private/runs/server-distro/wsta78-operator-packet-smoke-20260704T112439Z/operator/wsta78_operator_packet.md
```

## Safety

- No boot image was built or flashed.
- No forbidden partition was touched.
- No device command, native reboot, Wi-Fi association, DHCP, public tunnel,
  public smoke, userdata action, switch-root, or external service action ran.
- The runner has no `native_init_flash.py` or `a90ctl.py` call path.
- WSTA78 invokes WSTA77/WSTA76/WSTA75/WSTA74/WSTA73 host-only summary,
  brief, inventory, status, and packet surfaces only.
- WSTA58 live execution remains a separate explicit operator-selected gate.
- Redaction checks are applied to the public summary and generated Markdown.
- The committed report/source/test changes contain no raw public URL, public
  tunnel domain, confirm-token value, Wi-Fi credential, SSID, BSSID, MAC, IP,
  gateway, DNS, lease id value, or device serial.
- Raw private prepare-to-arm outputs, WSTA73 packets, WSTA75 inventories,
  WSTA76 briefs, WSTA77 summaries, and WSTA78 packet artifacts remain under
  `workspace/private/`.

## Validation

Compile check:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta78_persistent_operator_packet.py \
  tests/test_server_distro_wsta78_persistent_operator_packet.py
```

Result: pass

WSTA78 focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta78_persistent_operator_packet
```

Result: `Ran 8 tests ... OK`

Focused WSTA52-WSTA78 regression:

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
  tests.test_server_distro_wsta78_persistent_operator_packet
```

Result: `Ran 160 tests ... OK`

Fresh WSTA72 + WSTA73 + WSTA75 + WSTA76 + WSTA77 + WSTA78 private smoke: pass.

## Next

The default-off persistent exposure workflow now has prepare-to-arm, arming
packet, per-packet status, multi-packet inventory, launch brief, multi-brief
operator summary, and a final operator packet.  Continue only with explicit
operator-selected WSTA58 live proof, or further default-off operator
UX/reporting that does not start public exposure.

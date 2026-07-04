# WSTA107 Compact Status HUD Source Pass

Date: 2026-07-05 02:00 KST

## Scope

WSTA107 adds a compact, redacted operator status surface to the WSTA88 persistent
operator workflow. This is source-only work. No device action, native reboot,
Wi-Fi connect, DHCP, public tunnel, public smoke, packet-filter mutation, or boot
flash ran.

## Changes

- Added `status_hud` to WSTA88 public output and `workflow.status_hud`.
- The HUD reports enum/boolean-only state for:
  - public state and default-off status;
  - WSTA80 preflight/live decisions;
  - short lease TTL, ready index, and current initial seconds remaining;
  - packet-filter state, readiness, backend, policy, apply point, and restore triggers;
  - image-prep summary for initial and renewal runs;
  - manual-stop state and cleanup result;
  - redaction booleans.
- Added a `## Status HUD` markdown section so the operator sees the compact state
  before the artifact list.
- Kept raw public URL values, token values, SSID/PSK values, image paths, and SHA
  values out of the new summary.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta42_native_uplink_dpublic_tunnel.py \
  workspace/public/src/scripts/server-distro/run_wsta43_orchestrated_native_uplink_dpublic.py \
  workspace/public/src/scripts/server-distro/run_wsta45_appliance_operator.py \
  workspace/public/src/scripts/server-distro/run_wsta55_short_lived_public_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta58_renewal_manual_stop_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py \
  workspace/public/src/scripts/server-distro/run_wsta88_persistent_operator_workflow.py \
  workspace/public/src/scripts/server-distro/run_wsta94_packet_filter_live_gate.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta42_native_uplink_dpublic_tunnel \
  tests.test_server_distro_wsta43_orchestrated_native_uplink_dpublic \
  tests.test_server_distro_wsta45_appliance_operator \
  tests.test_server_distro_wsta55_short_lived_public_proof \
  tests.test_server_distro_wsta58_renewal_manual_stop_proof \
  tests.test_server_distro_wsta80_persistent_operator_execute_gate \
  tests.test_server_distro_wsta88_persistent_operator_workflow \
  tests.test_server_distro_wsta94_packet_filter_live_gate
```

Result:

- `87 tests OK`
- The WSTA94 runner-error JSON printed during the run is the expected exception-path
  fixture from the unit test; unittest still completed OK.
- A fresh WSTA88 preflight artifact was generated under
  `workspace/private/runs/server-distro/wsta107-status-hud-preflight-20260705T0200KST`.
  Its markdown renders `## Status HUD` before `## Key Artifacts`, with public state
  `PUBLIC_OFF`, live execution `false`, packet filter ready `true`, and manual stop
  `NOT_RUN`.

## Next

The WSTA88 operator output now surfaces the key live/public state without requiring
the operator to inspect nested WSTA80/WSTA58 JSON. Next useful work is either:

- run an attended WSTA88 live pass only if the operator wants another end-to-end proof; or
- move to Debian handoff/server polish while preserving WSTA88 public exposure as
  default-off and explicitly gated.

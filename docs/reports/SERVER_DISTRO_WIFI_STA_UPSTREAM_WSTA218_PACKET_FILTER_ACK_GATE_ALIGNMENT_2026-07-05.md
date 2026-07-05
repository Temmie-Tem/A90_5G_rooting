# WSTA218 Packet-Filter Ack Gate Alignment

Date: 2026-07-05
Scope: host-only source/test/preflight validation

## Result

PASS.  The D-public live gate chain now enforces the packet-filter acknowledgement
stack that WSTA76 already required:

- `--ack-packet-filter-mutation`
- `--force-packet-filter-restore-proof`

No live device action was run.  No boot flash, reboot, Wi-Fi association, DHCP,
public tunnel, public smoke, packet-filter mutation, rootfs mutation, userdata
write, LSM profile load, or switch-root occurred.

## Drift Fixed

WSTA76 operator packets already listed the packet-filter mutation acknowledgement
and restore-proof force flag, but the executable live path did not uniformly
enforce or preserve them.  The concrete drift was:

- WSTA42 could reach the actual packet-filter apply path without these explicit
  operator flags.
- WSTA43/WSTA45/WSTA55/WSTA58 delegated the live path without carrying the new
  packet-filter flags.
- WSTA63 generated a WSTA58 live command template without the packet-filter
  flags, so WSTA72/WSTA73/WSTA76/WSTA78/WSTA80 could expose a stale operator
  command.
- WSTA80/WSTA88 could accept the older acknowledgement stack and rely on later
  restore checks instead of requiring the explicit mutation/restore-proof flags
  before live delegation.

## Implementation

Updated the actual mutation and delegation chain:

- WSTA42 now fails closed unless both packet-filter flags are supplied.
- WSTA43 and WSTA45 now require the flags and pass them to the nested path.
- WSTA55 and WSTA58 now require the flags and pass them through WSTA45/WSTA55.
- WSTA63 live command template and WSTA64 template validator include both flags.
- WSTA73 operator acknowledgement list includes both flags.
- WSTA80 template, explicit gate, and WSTA58 argv reconstruction include both
  flags; old packet templates are supplemented only after WSTA80's explicit gate
  has accepted the flags.
- WSTA88 optional live template, parser, and WSTA80 delegation include both
  flags.

## Host Preflight Evidence

Generated:

`workspace/private/runs/server-distro/wsta218-packet-filter-ack-gate-alignment-20260705T211246KST/wsta88_operator_workflow.json`

Decision:

`wsta88-persistent-operator-workflow-preflight-pass`

The generated private artifacts contain both flags in the expected surfaces:

- `prepare/wsta63/wsta63_session_manifest.json`
- `operator/wsta78_operator_packet.json`
- `gate-preflight/wsta80_execute_gate.json`

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile <touched WSTA scripts and tests>
PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest tests/test_server_distro_wsta63_persistent_session_controller.py tests/test_server_distro_wsta64_persistent_session_readiness_audit.py tests/test_server_distro_wsta70_persistent_session_launch_manifest.py tests/test_server_distro_wsta71_persistent_launch_readiness_audit.py tests/test_server_distro_wsta72_persistent_prepare_to_arm.py tests/test_server_distro_wsta73_persistent_arming_packet.py tests/test_server_distro_wsta42_native_uplink_dpublic_tunnel.py tests/test_server_distro_wsta43_orchestrated_native_uplink_dpublic.py tests/test_server_distro_wsta45_appliance_operator.py tests/test_server_distro_wsta55_short_lived_public_proof.py tests/test_server_distro_wsta58_renewal_manual_stop_proof.py tests/test_server_distro_wsta80_persistent_operator_execute_gate.py tests/test_server_distro_wsta88_persistent_operator_workflow.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest discover -s tests -p 'test_server_distro*.py'
```

Results:

- Focused gate/template regression: `118 tests OK`.
- Full server-distro regression: `804 tests OK`.
- Host-only WSTA88 preflight: pass, with no live execution requested.

## Next

The attended D-public/default-drop path is internally consistent again.  Continue
only through the explicit live gate, or move to the next hardening layer without
weakening default-off/public-off behavior.

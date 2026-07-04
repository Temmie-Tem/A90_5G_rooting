# WSTA95 Packet Filter Lifecycle Source Gate

- Date: 2026-07-04
- Scope: D-public packet-filter lifecycle wiring, host/source only
- Decision: `wsta95-packet-filter-lifecycle-source-pass`
- Device action: none
- Boot flash / native reboot: none
- Wi-Fi / DHCP / public tunnel / public smoke: none
- Packet-filter mutation: none

## Summary

WSTA95 wires the WSTA94-proven D-public packet-filter into the existing
persistent operator lifecycle as a default-off hardening contract.  It does not
execute the packet-filter helper or start public exposure.  Instead, the
WSTA76 -> WSTA78 -> WSTA79 -> WSTA80 -> WSTA88 host-only path now carries and
validates a `PACKET_FILTER_REQUIRED_DEFAULT_OFF` contract:

- backend: `legacy-iptables`
- helper: `/usr/local/bin/a90-dpublic-packet-filter`
- policy: `loopback-default-drop`
- proof basis: `wsta94-packet-filter-loopback-live-pass`
- apply point: before public exposure starts
- restore points: manual-stop, retire, and failure cleanup
- default state: public off, live execution not requested

## Changes

- `run_wsta76_persistent_launch_brief.py` now emits
  `packet_filter_hardening`, adds packet-filter mutation/restore acknowledgement
  requirements, and records packet-filter preflight/cleanup expectations.
- `run_wsta78_persistent_operator_packet.py` propagates the hardening contract
  into the operator packet and adds execution guardrails requiring apply before
  exposure and restore on stop/retire/failure.
- `run_wsta79_persistent_operator_packet_status.py` now treats the hardening
  contract as part of logical packet identity.  Missing or drifted hardening
  prevents READY status.
- `run_wsta80_persistent_operator_execute_gate.py` blocks preflight if the
  current packet/status lacks ready packet-filter hardening and exposes the
  contract in the final execute gate.
- `run_wsta88_persistent_operator_workflow.py` surfaces
  `packet_filter_hardening_ready` in the one-command workflow output.

## Validation

Commands run:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_wsta76_persistent_launch_brief.py workspace/public/src/scripts/server-distro/run_wsta78_persistent_operator_packet.py workspace/public/src/scripts/server-distro/run_wsta79_persistent_operator_packet_status.py workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py workspace/public/src/scripts/server-distro/run_wsta88_persistent_operator_workflow.py
```

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest tests.test_server_distro_wsta76_persistent_launch_brief tests.test_server_distro_wsta78_persistent_operator_packet tests.test_server_distro_wsta79_persistent_operator_packet_status tests.test_server_distro_wsta80_persistent_operator_execute_gate tests.test_server_distro_wsta88_persistent_operator_workflow -v
```

Result: 41 tests passed.

## Safety

This was a host/source-only change.  It did not flash, reboot, associate Wi-Fi,
run DHCP, expose a public tunnel, start public smoke, touch userdata, switch
root, or mutate packet-filter state.  Existing no-public/no-credential defaults
remain inert.

## Next

WSTA96 should move from source contract to bounded live integration: invoke the
packet-filter helper inside the explicit public-live path, apply before tunnel
start, and prove exact restore on stop/retire/failure cleanup while preserving
all WSTA94 restore gates and WSTA80 explicit live acknowledgements.

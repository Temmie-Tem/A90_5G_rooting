# WSTA220 Operator Status Attended Default-Drop Live

Date: 2026-07-05
Scope: host-only WSTA108 status folding

## Result

PASS.  WSTA220 folds the WSTA219 attended default-drop live proof into the
WSTA108 operator server status bundle.

Representative host-only status run:

`workspace/private/runs/server-distro/wsta220-operator-status-attended-default-drop-live-fullest-20260705T220310KST/wsta108_operator_server_status.json`

Decision: `wsta108-operator-server-status-source-pass`.

## Implementation

`run_wsta108_operator_server_status.py` now accepts:

`--wsta219-attended-default-drop-live-json`

The supplied JSON must be a private WSTA88 live-pass result from the attended
default-drop path.  WSTA108 fail-closes if the proof is non-pass or if any
required live condition is missing.

The compact status object is:

`server_status.hardening.attended_default_drop_live`

Pass state:

`LEGACY_IPTABLES_DEFAULT_DROP_ATTENDED_LIVE_PROVEN`

## Proof Requirements

WSTA220 requires all of the following before setting the live-proven state:

- WSTA88 decision `wsta88-persistent-operator-workflow-live-pass`.
- WSTA80 live decision `wsta80-persistent-operator-execute-gate-live-pass`.
- Explicit `ack_packet_filter_mutation`.
- Explicit `force_packet_filter_restore_proof`.
- Packet filter ready as `legacy-iptables` / `loopback-default-drop`.
- Packet filter applied before public exposure.
- Initial and renewal WSTA55 public smoke passed.
- Initial and renewal TTL expiry ended `PUBLIC_OFF`.
- Initial and renewal packet-filter restore passed.
- Manual stop cleanup ended `PUBLIC_OFF`.
- Public URL values, tunnel credentials, Wi-Fi credentials, and raw secrets are
  not committed or emitted in the public status.

## Live Evidence Consumed

WSTA219 attended live proof:

`workspace/private/runs/server-distro/wsta219-explicit-default-drop-live-fixed-20260705T213431KST/wsta88_operator_workflow.json`

The representative WSTA220 run also supplied the current WSTA108 hardening
evidence bundle, including WSTA122, WSTA125, WSTA147, WSTA151, WSTA208, WSTA209,
WSTA212, WSTA214, WSTA216, and the WSTA219 live proof.

Observed representative checks:

- `attended_default_drop_live_proven=true`
- `seccomp_real_services_live_proven=true`
- `capability_drop_nonroot_services_live_proven=true`
- `cloudflared_model_defined=true`
- `hud_presenter_durable_restart_live_proven=true`
- `dropbear_admin_syscall_trace_live_proven=true`

Resulting next actions:

- `keep-public-exposure-default-off`
- `use-explicit-wsta88-live-gate-only-when-attended`
- `continue-next-hardening-layer-after-attended-default-drop-live`
- `move-to-next-hardening-layer-after-attended-default-drop-live`

The previous attended-live-use action is retired when WSTA219 is supplied and
validated.

## Safety

WSTA220 is host-only.  It reads existing private run artifacts and emits a
status bundle.

It did not perform any device action, boot flash, native reboot, Wi-Fi connect,
DHCP, public tunnel, public smoke, packet-filter mutation, rootfs mutation,
userdata write, LSM profile load, or switch-root.

## Validation

Static compile:

`PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_wsta108_operator_server_status.py tests/test_server_distro_wsta108_operator_server_status.py`

Focused WSTA108 tests:

`PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest tests/test_server_distro_wsta108_operator_server_status.py`

Result: `60 tests OK`.

Full server-distro regression:

`PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest discover -s tests -p 'test_server_distro*.py'`

Result: `809 tests OK`.

## Next

Continue from the visible hardening state.  Public exposure remains default-off
and explicit-gated; the next unit should choose the next hardening layer without
weakening the proven legacy-iptables default-drop path.

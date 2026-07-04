# WSTA102-WSTA104 Public Smoke Retry and WSTA88 Live Proof

Date: 2026-07-05 01:43 KST host clock
Scope: server-distro native STA uplink plus D-public persistent workflow
Device mutation: SD/chroot/userspace only, no boot flash
Secret hygiene: no SSID, PSK, confirm token, or public URL value recorded here

## Summary

WSTA102 reran the orchestrated WSTA43 path after the packet-filter
control-plane fixes.  It proved that the repeated native uplink autoconnect
failure from WSTA100/WSTA101 was not persistent when WSTA28 reboot/scan gating
ran first:

- run: `workspace/private/runs/server-distro/wsta102-orchestrated-packet-filter-live-20260704T160914Z`
- WSTA28: `wsta28-reboot-materialization-scan-gate-pass`
- WSTA42 native uplink: confirmed
- default route: `wlan0`
- resolver sync: ready
- local smoke: pass
- packet-filter preflight/apply/restore: pass
- tunnel URL observed: yes
- decision: `wsta42-blocked-public-smoke`

The public smoke blocker was host-side DNS propagation, not the device public
path.  All six attempts failed with `URLError` / `gaierror` / errno `-2`, while
the public URL value remained private/redacted.

The WSTA42 public smoke retry policy now keeps the URL redacted but gives DNS
propagation enough time:

- default attempts: `6` -> `20`
- default retry delay: `2.5s` -> `3.0s`
- failure records now summarize `dns_error_count`,
  `last_error_class`, and `last_error_reason_class`
- success records also preserve the prior DNS retry count and last error class

WSTA103 then passed the same orchestrated WSTA43 path:

- run: `workspace/private/runs/server-distro/wsta103-public-smoke-retry-live-20260704T161758Z`
- decision: `wsta43-orchestrated-native-uplink-dpublic-pass`
- nested WSTA42: `wsta42-native-uplink-dpublic-tunnel-pass`
- WSTA28: `wsta28-reboot-materialization-scan-gate-pass`
- public smoke: HTTP `200` on attempt `3`
- public smoke markers: app marker, loopback service marker, and
  outbound-tunnel-only marker all present
- cleanup: D-public cleanup, packet-filter restore, native uplink profile
  cleanup, chroot cleanup, service stop, and final selftest all passed

WSTA104 then exercised the full persistent operator workflow through WSTA88:

- run: `workspace/private/runs/server-distro/wsta104-wsta88-persistent-live-20260704T162855Z`
- WSTA88: `wsta88-persistent-operator-workflow-live-pass`
- WSTA80: `wsta80-persistent-operator-execute-gate-live-pass`
- WSTA58: `wsta58-renewal-manual-stop-live-pass`
- initial WSTA55: `wsta55-short-lived-public-proof-live-pass`
- renewal WSTA55: `wsta55-short-lived-public-proof-live-pass`
- WSTA58 checks:
  - initial and renewal WSTA55 passed
  - initial and renewal packet-filter restore passed
  - second renewal gate required
  - manual-stop cleanup passed
  - manual-stop public state ended `PUBLIC_OFF`
  - WSTA48 redaction and aggregate checks passed

Nested WSTA42 public-smoke details stayed redacted:

- initial public smoke: HTTP `200` on attempt `3`, `dns_error_count=2`
- renewal public smoke: HTTP `200` on attempt `6`, `dns_error_count=3`
- both runs: app marker, loopback service marker, and outbound-tunnel-only
  marker present
- both runs: packet-filter restore, D-public cleanup, and final selftest passed

Final device health after WSTA104:

- resident: `A90 Linux init 0.11.153 (v3397-wsta-execute-gate-screen)`
- selftest: `pass=12 warn=1 fail=0`
- transport: serial ready, NCM ready, tcpctl ready
- storage: SD mounted rw
- postchecks from both WSTA42 runs: mount absent, loop node absent,
  Dropbear absent

## Validation

Host-side static and focused unit validation:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta42_native_uplink_dpublic_tunnel.py \
  workspace/public/src/scripts/server-distro/run_wsta43_orchestrated_native_uplink_dpublic.py \
  workspace/public/src/scripts/server-distro/run_wsta55_short_lived_public_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta58_renewal_manual_stop_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py \
  workspace/public/src/scripts/server-distro/run_wsta88_persistent_operator_workflow.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta42_native_uplink_dpublic_tunnel \
  tests.test_server_distro_wsta43_orchestrated_native_uplink_dpublic \
  tests.test_server_distro_wsta55_short_lived_public_proof \
  tests.test_server_distro_wsta58_renewal_manual_stop_proof \
  tests.test_server_distro_wsta80_persistent_operator_execute_gate \
  tests.test_server_distro_wsta88_persistent_operator_workflow
```

Result: `Ran 63 tests ... OK`.

Live validation:

- WSTA102: bounded public-live rerun, blocked only at host DNS public smoke.
- WSTA103: bounded WSTA43 public-live pass.
- WSTA104: bounded WSTA88 persistent workflow live pass, including initial and
  renewal WSTA55 public proof and manual-stop cleanup.
- Final `a90ctl status` returned v3397, transport ready, SD rw.
- Final `a90ctl selftest` returned `pass=12 warn=1 fail=0`.

## Next

The D-public persistent operator path is now live-proven through the WSTA88
one-command gate with packet-filter hardening, renewal proof, redaction checks,
and manual-stop cleanup.  The next useful unit should focus on operator polish
and serverization ergonomics rather than re-proving the same WSTA88 path:

- surface a concise operator-facing public-state/HUD status;
- reduce repeated 2GiB image hash/restore cost where safely cacheable;
- keep D-public disabled by default and continue requiring explicit live gates.

# WSTA172 Seccomp Fresh Execute Preflight Pass

Date: 2026-07-05 14:14 KST

## Verdict

WSTA172 bundles the final pre-execution refresh: it runs a fresh WSTA169
read-only readiness check, regenerates the WSTA170 source gate from that fresh
readiness proof, and regenerates the WSTA171 execution preflight from the fresh
WSTA170 proof.  It does not execute the generated WSTA170 command.

Result: PASS.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta172_seccomp_fresh_execute_preflight.py`.
- Added focused tests in
  `tests/test_server_distro_wsta172_seccomp_fresh_execute_preflight.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta172-seccomp-fresh-execute-preflight-20260705T142100KST/
```

Decision:

```text
wsta172-seccomp-fresh-execute-preflight-pass
```

Nested results:

```text
wsta169-readiness/wsta169_result.json      wsta169-seccomp-live-readiness-readonly-pass
wsta170-source-gate/wsta170_result.json    wsta170-blocked-explicit-execution-gate-required
wsta171-execute-preflight/wsta171_result.json  wsta171-seccomp-live-observation-execute-preflight-pass
```

Generated fresh execution command:

```text
workspace/private/runs/server-distro/wsta172-seccomp-fresh-execute-preflight-20260705T142100KST/wsta171-execute-preflight/wsta171_wsta170_execute_command.json
workspace/private/runs/server-distro/wsta172-seccomp-fresh-execute-preflight-20260705T142100KST/wsta171-execute-preflight/wsta171_wsta170_execute_command.sh
```

Command state:

```text
state=READY_TO_RUN_NOT_EXECUTED
executed=false
required_ack_count=6
```

## Fresh Readiness

The fresh WSTA169 read-only check passed:

- resident build: `v3402-dpublic-hud-presenter-restart-policy`.
- bridge readiness: true.
- version check: true.
- status check: true.
- selftest fail-zero check: true.
- WSTA168 command artifacts still match the readiness proof.

## Safety Boundary

This unit did not flash, reboot, connect Wi-Fi, run DHCP, open a public tunnel,
mutate packet filters, write userdata, switch root, execute WSTA170, execute
WSTA168/WSTA167, load a seccomp filter, enforce seccomp, or supply the correct
WSTA161 token.  Device contact was limited to WSTA169 read-only
bridge/version/status/selftest queries.

## Validation

- `py_compile`:
  - `run_wsta172_seccomp_fresh_execute_preflight.py`
  - `test_server_distro_wsta172_seccomp_fresh_execute_preflight.py`
- Focused WSTA171 + WSTA172 tests: `7 tests OK`.
- WSTA172 fresh pre-execution bundle against the current bridge/device: pass.
- Full server-distro regression: `591 tests OK`.

## Next

The fresh WSTA172-generated command is the exact next execution step.  It must
only be run with explicit operator approval for the no-load live observation.

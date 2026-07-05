# WSTA170 Seccomp Live-Observation Execute Source Gate

Date: 2026-07-05 14:03 KST

## Verdict

WSTA170 adds the fail-closed executor for the WSTA168 no-load live observation
command.  The runner consumes the WSTA169 read-only readiness proof and the
WSTA168 command artifacts, validates both, and refuses to execute unless a
separate WSTA170 acknowledgement set is supplied.

Result: SOURCE GATE PASS.  The real WSTA169/WSTA168 artifacts validated, then
the runner stopped with:

```text
wsta170-blocked-explicit-execution-gate-required
```

No live command was executed in this unit.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta170_seccomp_live_observation_execute.py`.
- Added focused tests in
  `tests/test_server_distro_wsta170_seccomp_live_observation_execute.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta170-seccomp-live-observation-execute-source-gate-20260705T140000KST/
```

Inputs:

```text
workspace/private/runs/server-distro/wsta169-seccomp-live-readiness-readonly-20260705T135709KST/wsta169_result.json
workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/wsta168_live_command.json
workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/wsta168_live_command.sh
```

Checks that passed before the execution gate:

- WSTA169 readiness proof decision is
  `wsta169-seccomp-live-readiness-readonly-pass`.
- WSTA169 proof still says bridge, version, status, and selftest readiness are
  valid.
- WSTA169 proof still says the WSTA168 live command was not executed.
- WSTA168 command artifacts are private, present, and
  `READY_TO_RUN_NOT_EXECUTED`.
- WSTA168 command targets `run_wsta167_seccomp_live_observation.py`.
- WSTA168 command contains all required WSTA167 ack flags.
- WSTA168 command excludes `WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD`.
- WSTA168 command expected outcome remains no seccomp load and no seccomp
  enforcement.
- Nested WSTA167 run directory is private.

## Execution Gate

WSTA170 requires all of these before executing:

```text
--execute-wsta170-no-load-live-observation
--allow-wsta168-command-execution
--ack-readiness-proof-current
--ack-no-correct-wsta161-token
--ack-no-seccomp-load
--ack-cleanup-required
```

Only after those flags are present does it run the generated WSTA168 command.
The executor then requires the nested WSTA167 result to pass and to report no
seccomp load/enforcement, no correct WSTA161 token, no flash, no reboot, no
Wi-Fi connect, no DHCP, no public tunnel, and no packet-filter mutation.

## Safety Boundary

This unit did not flash, reboot, connect Wi-Fi, run DHCP, open a public tunnel,
mutate packet filters, write userdata, switch root, execute the WSTA168 live
command, load a seccomp filter, enforce seccomp, or supply the correct WSTA161
token.

## Validation

- `py_compile`:
  - `run_wsta170_seccomp_live_observation_execute.py`
  - `test_server_distro_wsta170_seccomp_live_observation_execute.py`
- Focused WSTA169 + WSTA170 tests: `8 tests OK`.
- WSTA170 source-gate proof against the real WSTA169/WSTA168 artifacts: blocked
  before execution as designed, readiness and command checks true.
- Full server-distro regression: `584 tests OK`.

## Next

The next step is the actual WSTA170 no-load live observation execution, but only
with explicit operator approval for the full WSTA170 acknowledgement set above.

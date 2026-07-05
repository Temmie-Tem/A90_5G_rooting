# WSTA177 Seccomp One-Shot Execute Gate

Date: 2026-07-05 14:43 KST

## Verdict

WSTA177 adds a one-shot execution gate above WSTA176.  It creates a fresh
WSTA176/WSTA175 execution packet immediately before any possible execution,
validates the generated command, then stops unless the full WSTA177
acknowledgement set is supplied.

Result: SOURCE GATE PASS.  The runner generated and validated a fresh WSTA175
command packet, then stopped with:

```text
wsta177-blocked-explicit-execution-gate-required
```

No WSTA175, WSTA170, WSTA168, or WSTA167 command was executed in this unit.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta177_seccomp_one_shot_execute_gate.py`.
- Added focused tests in
  `tests/test_server_distro_wsta177_seccomp_one_shot_execute_gate.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta177-seccomp-one-shot-execute-gate-20260705T144329KST/
```

Decision:

```text
wsta177-blocked-explicit-execution-gate-required
```

Nested WSTA176 result:

```text
workspace/private/runs/server-distro/wsta177-seccomp-one-shot-execute-gate-20260705T144329KST/wsta176-handoff-execute-preflight/wsta176_result.json
wsta176-seccomp-handoff-execute-preflight-pass
```

Generated execution command:

```text
workspace/private/runs/server-distro/wsta177-seccomp-one-shot-execute-gate-20260705T144329KST/wsta176-handoff-execute-preflight/wsta176_wsta175_execute_command.json
workspace/private/runs/server-distro/wsta177-seccomp-one-shot-execute-gate-20260705T144329KST/wsta176-handoff-execute-preflight/wsta176_wsta175_execute_command.sh
```

Checks:

```text
fresh_preflight_valid=true
execution_command_valid=true
explicit_execution_gate=false
command_ready=true
command_not_executed=true
correct_token_literal_absent=true
```

Safety flags:

```text
fresh_preflight_generated=true
live_command_executed=false
wsta175_execute_command_executed=false
wsta170_execute_command_executed=false
seccomp_filter_loaded=false
seccomp_enforced=false
correct_wsta161_token_supplied=false
```

## Execution Gate

WSTA177 requires all of these before executing the generated WSTA175 command:

```text
--execute-wsta177-one-shot
--allow-wsta175-command-execution
--ack-fresh-preflight
--ack-no-correct-wsta161-token
--ack-no-seccomp-load
--ack-cleanup-required
```

Without that exact acknowledgement set, WSTA177 only refreshes and validates
the handoff/execution packet.

## Safety Boundary

This unit did not flash, reboot, connect Wi-Fi, run DHCP, open a public tunnel,
mutate packet filters, write userdata, switch root, execute WSTA175, execute
WSTA170, execute WSTA168/WSTA167, load a seccomp filter, enforce seccomp, or
supply the correct WSTA161 token.  Device contact was limited to the nested
WSTA176/WSTA174/WSTA172/WSTA169 read-only bridge/version/status/selftest
checks.

## Validation

- `py_compile`:
  - `run_wsta177_seccomp_one_shot_execute_gate.py`
  - `test_server_distro_wsta177_seccomp_one_shot_execute_gate.py`
- Focused WSTA176 + WSTA177 tests: `8 tests OK`.
- WSTA177 one-shot source-gate proof against the current bridge/device:
  blocked before WSTA175 execution as designed.
- Full server-distro regression: `611 tests OK`.

## Next

WSTA177 is now the freshest executor surface for the no-load live observation.
It still requires explicit operator approval for the full WSTA177 acknowledgement
set before WSTA175/WSTA170/WSTA167 execution.

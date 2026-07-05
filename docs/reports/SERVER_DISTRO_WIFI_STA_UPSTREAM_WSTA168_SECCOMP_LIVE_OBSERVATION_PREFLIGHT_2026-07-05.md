# WSTA168 Seccomp Live-Observation Preflight Pass

Date: 2026-07-05 13:50 KST

## Verdict

WSTA168 consumes the WSTA167 no-live-gate proof and emits the exact command
packet for the later WSTA167 live observation.  This unit is host-only: it does
not contact the device and does not execute the live command.

Result: PASS.  The preflight verified WSTA167's no-live proof, generated a
ready-to-run command with all five required WSTA167 acknowledgements, and kept
the expected outcome no-load/no-enforce:

```text
seccomp_filter_loaded=false
seccomp_enforced=false
correct_wsta161_token_supplied=false
scenario_returncode=65
```

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta168_seccomp_live_observation_preflight.py`.
- Added focused tests in
  `tests/test_server_distro_wsta168_seccomp_live_observation_preflight.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/
```

Input:

```text
workspace/private/runs/server-distro/wsta167-seccomp-live-observation-source-gate-20260705T1354KST/wsta167_result.json
```

Decision:

```text
wsta168-seccomp-live-observation-preflight-pass
```

Generated command artifacts:

```text
workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/wsta168_live_command.json
workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/wsta168_live_command.sh
```

Command:

```text
python3 workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py --run-id wsta168-seccomp-live-observation-execute --run-dir workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/wsta167-live-run --execute-seccomp-live-observation --allow-seccomp-live-observation --ack-no-correct-wsta161-token --ack-no-seccomp-load --ack-cleanup-required
```

Command state:

```text
schema=a90-wsta168-seccomp-live-observation-command-v1
state=READY_TO_RUN_NOT_EXECUTED
executed=false
required_ack_count=5
```

## Checks

WSTA168 fail-closes unless:

- the preflight emission is explicitly gated.
- run dir and WSTA167 proof JSON are private.
- WSTA167 proof decision is
  `wsta167-blocked-seccomp-live-observation-required`.
- WSTA167 proof has `contract_valid=true` and `local_inputs_present=true`.
- WSTA167 proof has `explicit_live_gate=false`.
- WSTA167 proof safety says device action, seccomp load, seccomp enforcement,
  and correct WSTA161 token are all false.
- every WSTA167 contract check is true.
- generated command targets `run_wsta167_seccomp_live_observation.py`.
- generated command contains all five required ack flags.
- generated command excludes the correct WSTA161 token and external network
  inputs.
- generated command expected outcome is no-load/no-enforce.
- generated command is marked not executed.

## Validation

- `py_compile`:
  - `run_wsta168_seccomp_live_observation_preflight.py`
  - `test_server_distro_wsta168_seccomp_live_observation_preflight.py`
- Focused WSTA167 + WSTA168 tests: `8 tests OK`.
- Full server-distro regression: `576 tests OK`.
- WSTA168 preflight generation from the real WSTA167 no-live proof: pass.

## Next

The next step can execute the generated `wsta168_live_command.sh` to perform the
actual no-load live observation.  That execution must still expect no seccomp
load/enforcement and must not supply the correct WSTA161 load token.

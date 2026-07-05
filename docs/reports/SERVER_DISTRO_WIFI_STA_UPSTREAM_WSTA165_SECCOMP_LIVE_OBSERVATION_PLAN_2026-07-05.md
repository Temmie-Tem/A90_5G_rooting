# WSTA165 Seccomp Live-Observation Plan Pass

Date: 2026-07-05 13:33 KST

## Verdict

WSTA165 consumes the WSTA164 chroot proof and emits a structured host-only plan
for a later device-side observation of the staged seccomp apply/load-env gates.
It does not contact the device and does not include the correct WSTA161 load
token in the plan.  The plan describes only no-load observations and stop
conditions.

This unit is host-only: it did not touch the device, flash, reboot, connect
Wi-Fi, run DHCP, open a public tunnel, mutate packet filters, write userdata,
load BPF, load a seccomp filter, enforce seccomp, chroot, or switch root.

Result: PASS.  The WSTA164 proof was verified as pass, all WSTA164 proof
checks were true, WSTA164 did not supply the correct token, and WSTA165 emitted
three later-live observation scenarios with filter load and enforcement both
expected false.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta165_seccomp_live_observation_plan.py`.
- Added focused tests in
  `tests/test_server_distro_wsta165_seccomp_live_observation_plan.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta165-seccomp-live-observation-plan-20260705T1335KST/
```

Input:

```text
workspace/private/runs/server-distro/wsta164-seccomp-load-env-contract-chroot-proof-20260705T1329KST/wsta164_result.json
```

Decision:

```text
wsta165-seccomp-live-observation-plan-pass
```

Plan artifact:

```text
workspace/private/runs/server-distro/wsta165-seccomp-live-observation-plan-20260705T1335KST/wsta165_live_observation_plan.json
```

Plan summary:

```text
schema=a90-wsta165-seccomp-live-observation-plan-v1
state=HOST_ONLY_PLAN_NOT_EXECUTED
scenarios=no-load-env-gate,load-env-gate-missing-token,load-env-gate-wrong-token
correct_wsta161_token_supplied=false
seccomp_filter_load_expected=false
seccomp_enforcement_expected=false
```

Stop conditions:

```text
any scenario prints A90WSTA161_SECCOMP_LOAD_ATTEMPT=1
any scenario reaches a90_service_launcher_decision=exec
any scenario omits its expected block marker
any live pre/post native health check regresses
operator has not supplied the separate live-observation gate
```

Forbidden inputs:

```text
correct WSTA161 load token
public tunnel gates
Wi-Fi connect/DHCP gates
packet-filter mutation gates
```

## Checks

WSTA165 fail-closes unless:

- the plan emission is explicitly gated.
- run dir and WSTA164 proof JSON are private.
- WSTA164 decision is
  `wsta164-seccomp-load-env-contract-chroot-proof-pass`.
- every WSTA164 proof check is true.
- WSTA164 proves launcher load-env gate, load-env forwarding, and no hardcoded
  WSTA161 token.
- WSTA164 proof says the correct WSTA161 token was not supplied.
- WSTA164 proof says filter load and enforcement were false.
- WSTA164 no-gate, missing-token, and wrong-token paths all had no load
  attempt.
- the emitted plan has exactly three no-load scenarios.
- the emitted plan includes only an intentionally wrong token placeholder, not
  the correct WSTA161 token.

## Validation

- `py_compile`:
  - `run_wsta165_seccomp_live_observation_plan.py`
  - `test_server_distro_wsta165_seccomp_live_observation_plan.py`
- Focused WSTA164 + WSTA165 tests: `5 tests OK`.
- Full server-distro regression: `565 tests OK`.
- WSTA165 plan generation from the real WSTA164 proof JSON: pass.

## Next

WSTA166 can either implement the bounded live-observation runner from this plan
without the correct WSTA161 load token, or stop for an explicit design review
before any first real seccomp-load experiment.  Actual seccomp
load/enforcement remains unproven.

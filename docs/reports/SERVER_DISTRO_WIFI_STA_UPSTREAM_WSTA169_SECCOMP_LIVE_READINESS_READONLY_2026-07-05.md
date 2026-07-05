# WSTA169 Seccomp Live-Readiness Read-Only Pass

Date: 2026-07-05 13:57 KST

## Verdict

WSTA169 adds a read-only readiness gate for the WSTA168 no-load live
observation command.  It contacts the device only through read-only bridge,
version, status, and selftest queries, then confirms the generated WSTA168
command remains ready-not-executed and still excludes the correct WSTA161
seccomp-load token.

Result: PASS.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta169_seccomp_live_readiness_readonly.py`.
- Added focused tests in
  `tests/test_server_distro_wsta169_seccomp_live_readiness_readonly.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta169-seccomp-live-readiness-readonly-20260705T135709KST/
```

Decision:

```text
wsta169-seccomp-live-readiness-readonly-pass
```

Consumed WSTA168 command artifacts:

```text
workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/wsta168_live_command.json
workspace/private/runs/server-distro/wsta168-seccomp-live-observation-preflight-20260705T1358KST/wsta168_live_command.sh
```

## Read-Only Device Observations

- Bridge process: running.
- Bridge port: listening.
- Bridge probe: connected.
- Selected serial device and realpath: present.
- Resident init: `A90 Linux init 0.11.158`
  (`v3402-dpublic-hud-presenter-restart-policy`).
- Selftest: `pass=12 warn=1 fail=0`.
- Transport: NCM ready.
- Runtime backend: SD.
- Storage: SD present, mounted, read-write.

## Command Artifact Checks

WSTA169 verified the WSTA168 command artifacts are private and still have:

- schema `a90-wsta168-seccomp-live-observation-command-v1`.
- state `READY_TO_RUN_NOT_EXECUTED`.
- `executed=false`.
- target `run_wsta167_seccomp_live_observation.py`.
- all five required WSTA167 ack flags.
- no `WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD` token.
- expected `seccomp_filter_loaded=false`.
- expected `seccomp_enforced=false`.

## Safety Boundary

This unit did not flash, reboot, connect Wi-Fi, run DHCP, open a public tunnel,
mutate packet filters, write userdata, switch root, execute the WSTA168 live
command, load a seccomp filter, enforce seccomp, or supply the correct WSTA161
token.

## Validation

- `py_compile`:
  - `run_wsta169_seccomp_live_readiness_readonly.py`
  - `test_server_distro_wsta169_seccomp_live_readiness_readonly.py`
- Focused WSTA168 + WSTA169 tests: `7 tests OK`.
- WSTA169 read-only proof against the current bridge/device: pass.
- Full server-distro regression: `580 tests OK`.

## Next

WSTA170 can execute the generated WSTA168 command for the actual no-load live
observation if the operator explicitly wants that step.  The expected result
remains no seccomp load/enforcement and no correct WSTA161 load token.

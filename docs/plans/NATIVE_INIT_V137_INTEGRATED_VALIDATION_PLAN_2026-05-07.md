# v137 Plan: Integrated Validation Matrix

## Summary

v137 targets `A90 Linux init 0.9.37 (v137)` / `0.9.37 v137 VALIDATION MATRIX`.

This version is the **B candidate** from the post-v135/v136 choice: broaden
validation coverage after v136 confirmed there is no blocking structure issue.
The goal is to make one repeatable validation gate that exercises the current
safety owners together before any Wi-Fi, broader network exposure, or larger
controller split.

Current baseline:

- latest verified build is `A90 Linux init 0.9.36 (v136)`;
- v136 structure audit found no blocking ownership drift;
- largest future hotspots are `v136/40_menu_apps.inc.c`,
  `v136/80_shell_dispatch.inc.c`, and `v136/70_storage_android_net.inc.c`;
- local targeted v136 rescan is `PASS=16`, `WARN=1`, `FAIL=0`;
- remaining warning is the accepted USB-local/localhost root-control boundary.

## Scope Decision

Choose `integrated validation matrix / host harness expansion` for v137.

Rationale:

- v135 added native `policycheck`, but it only covers controller busy policy.
- v134 added `exposure`, v121 added `pid1guard`, v94 added `selftest`, and
  v101+ added service manager views. These checks are useful separately, but
  there is no single gate that proves they all still agree.
- v136 identified that further splitting of menu/shell/storage handlers should
  wait until regression coverage is stronger.
- v137 should therefore strengthen validation rather than move more logic.

Do not implement Wi-Fi bring-up, new listeners, new authentication protocols,
new root-control channels, or a large source split in v137.

## Key Changes

- Copy v136 into `init_v137.c` and `v137/*.inc.c`.
- Bump metadata in `a90_config.h` to `0.9.37` / `v137` and add changelog text
  `0.9.37 v137 VALIDATION MATRIX`.
- Add host harness `scripts/revalidation/native_integrated_validate.py`.
- Keep native command behavior unchanged unless the harness exposes a concrete
  bug.
- Update `native_soak_validate.py` default expected version to v137 after flash
  verification.
- Update `local_security_rescan.py` scope to active v137 and add a wiring check
  that confirms the integrated validation harness exists and includes the core
  validation commands.
- Write `docs/reports/NATIVE_INIT_V137_VALIDATION_MATRIX_2026-05-07.md` after
  real-device validation.

## Integrated Host Harness

New script:

```text
scripts/revalidation/native_integrated_validate.py
```

Default command set should be non-destructive and bounded:

```text
version
status
bootstatus
selftest verbose
pid1guard verbose
exposure guard
exposure verbose
policycheck run
policycheck verbose
service list
service status autohud
service status tcpctl
service status rshell
netservice status
rshell audit
runtime
helpers status
userland status
storage
mountsd status
wififeas gate
diag summary
screenmenu
hide
```

The script should:

- use repo-root pinned `a90ctl.py`, not CWD-relative paths;
- default to `--expect-version "A90 Linux init 0.9.37 (v137)"`;
- run every command through framed cmdv1/a90ctl;
- fail if `A90P1 END` or `status=ok` is missing;
- check semantic output for key commands:
  - `version` contains expected version;
  - `selftest` contains `fail=0`;
  - `pid1guard` contains `fail=0`;
  - `exposure guard` contains `guard=ok` and `fail=0`;
  - `policycheck run` contains `fail=0`;
  - `rshell audit` does not print token values;
  - `netservice status` is observable without starting services;
  - `screenmenu` returns immediately and `hide` succeeds;
- write a transcript to `tmp/validation/native-integrated-v137.txt` by default;
- optionally write JSON with command rc/status/duration checks if `--json-out`
  is provided.

## Validation Matrix Semantics

The integrated gate should not replace detailed tools. It should prove that the
current safety layers agree:

| Layer | Evidence command | Required condition |
|---|---|---|
| Version/protocol | `version` | expected v137 and framed status ok |
| Boot health | `bootstatus` | selftest/pid1guard/exposure summaries present |
| Module smoke | `selftest verbose` | `fail=0` |
| PID1 invariant | `pid1guard verbose` | `fail=0` |
| Root-control exposure | `exposure guard` | `guard=ok`, `fail=0` |
| Menu/power policy | `policycheck run` | `fail=0` |
| Service metadata | `service list`, `service status ...` | observable without mutation |
| Network policy | `netservice status`, `rshell audit` | observable, no service start required |
| Storage/runtime | `runtime`, `helpers status`, `storage`, `mountsd status` | observable and status ok |
| UI nonblocking | `screenmenu`, `hide` | immediate rc=0/status=ok |

## Deferred Work

v137 must not include these:

- native menu/shell/storage handler migration;
- Wi-Fi active bring-up;
- dropbear/SSH exposure;
- automatic netservice/rshell enablement;
- destructive validation commands by default;
- local serial/USB ACM auth changes.

## Test Plan

### Local Build

Build v137 with the same module set as v136 and confirm markers:

```bash
strings stage3/linux_init/init_v137 | rg "A90 Linux init 0\.9\.37 \(v137\)|A90v137|0\.9\.37 v137 VALIDATION MATRIX"
```

### Static Checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/local_security_rescan.py \
  scripts/revalidation/native_soak_validate.py \
  scripts/revalidation/native_integrated_validate.py
rg -n "A90v136|0\.9\.36|init_v136|v136/" stage3/linux_init/init_v137.c stage3/linux_init/v137 stage3/linux_init/a90_config.h || true
```

### Device Validation

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v137.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.37 (v137)" \
  --verify-protocol auto
```

Integrated validation:

```bash
python3 scripts/revalidation/native_integrated_validate.py \
  --expect-version "A90 Linux init 0.9.37 (v137)" \
  --out tmp/validation/native-integrated-v137.txt \
  --json-out tmp/validation/native-integrated-v137.json
```

Regression baseline:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.37 (v137)" \
  --out tmp/soak/v137-quick-soak.txt
```

## Acceptance

- v137 boots and verifies as `A90 Linux init 0.9.37 (v137)`.
- `native_integrated_validate.py` passes with all default commands.
- The integrated harness transcript and optional JSON are written.
- `selftest`, `pid1guard`, `exposure`, `policycheck`, service status,
  netservice status, rshell audit, storage/runtime status, and screenmenu/hide
  are covered in one command.
- Local targeted v137 security rescan remains `FAIL=0`.
- No new network exposure is introduced.

## Assumptions

- v136 is latest verified when v137 starts.
- v137 is primarily a validation release; behavior changes should be limited to
  version/changelog marker updates unless a bug is found.
- The accepted USB-local/localhost root-control warning remains accepted only
  while bridge and ACM use stay local/trusted-lab-only.

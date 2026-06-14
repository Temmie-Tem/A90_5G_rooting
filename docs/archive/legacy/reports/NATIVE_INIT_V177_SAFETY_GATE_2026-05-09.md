# Native Init v177 Safety Gate / Dry-Run Policy Report (2026-05-09)

## Summary

- label: `v177 Safety Gate / Dry-Run Policy`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- scope: host-side supervisor module gate only; no boot image change
- result: `PASS`

v177 adds module safety metadata, listing/planning, dry-run output, and default
blocking for environment-dependent or risky modules.

## Implemented

- `scripts/revalidation/a90harness/gate.py`
  - `GateOptions`
  - `GateResult`
  - `evaluate_gate()`
- `scripts/revalidation/a90harness/module.py`
  - `operator_confirm_required`
  - metadata fields for gate evaluation
- `scripts/revalidation/native_test_supervisor.py`
  - `list`
  - `plan <module>`
  - `run <module> --dry-run`
  - `--allow-ncm`
  - `--allow-usb-rebind`
  - `--allow-destructive`
  - `--assume-yes`
- `scripts/revalidation/a90harness/modules/usb_recovery.py`
  - marks USB recovery as `operator_confirm_required=True`

## Validation

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

CLI validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py list
python3 scripts/revalidation/native_test_supervisor.py plan usb-recovery
python3 scripts/revalidation/native_test_supervisor.py run usb-recovery --dry-run
python3 scripts/revalidation/native_test_supervisor.py run kselftest-feasibility --dry-run
python3 scripts/revalidation/native_test_supervisor.py plan ncm-tcp-preflight --allow-ncm
```

Observed gate state:

- `cpu-mem-thermal`: allowed by default
- `kselftest-feasibility`: allowed by default
- `ncm-tcp-preflight`: blocked until `--allow-ncm`
- `storage-io`: blocked until `--allow-ncm`
- `usb-recovery`: blocked until `--allow-usb-rebind --assume-yes`

Blocking validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py run usb-recovery
```

Result:

```text
rc=2
required_flags:
- --allow-usb-rebind
- --assume-yes
```

Allowed module regression:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  run kselftest-feasibility \
  --observer-duration-sec 0 \
  --run-dir tmp/soak/harness/v177-gate-allowed-20260508T180349Z
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v177-gate-allowed-20260508T180349Z module=kselftest-feasibility observer_failures=n/a
```

## Acceptance

| Requirement | Evidence | Result |
| --- | --- | --- |
| `list` shows module gate state | command output shows allowed/required flags | PASS |
| `plan usb-recovery` explains blocked reasons | output lists USB rebind and confirmation reasons | PASS |
| `run usb-recovery --dry-run` does not mutate state | dry-run prints plan only | PASS |
| `run usb-recovery` blocks without flags | rc=2 and required flags listed | PASS |
| safe module dry-run reports allowed | `kselftest-feasibility --dry-run` | PASS |
| safe module still runs | `v177-gate-allowed-20260508T180349Z` | PASS |
| Static validation passes | `py_compile` and `git diff --check` | PASS |

## Cycle Decision

The v170-v177 host harness cycle is complete enough to support v178 Wi-Fi
baseline refresh on top of the supervisor. Environment-dependent modules now
have explicit preflight and dry-run gates.

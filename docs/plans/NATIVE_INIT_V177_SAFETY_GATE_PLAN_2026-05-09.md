# Native Init v177 Safety Gate / Dry-Run Policy Plan (2026-05-09)

## Summary

- label: `v177 Safety Gate / Dry-Run Policy`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: add supervisor module listing, planning, dry-run, and explicit gates for risky or environment-dependent modules.

v177 is host tooling only. It does not change or flash the boot image.

## Scope

- Add `a90harness/gate.py`.
- Add module metadata gate fields.
- Add supervisor commands:
  - `list`
  - `plan <module>`
  - `run <module> --dry-run`
- Add explicit allow flags:
  - `--allow-ncm`
  - `--allow-usb-rebind`
  - `--allow-destructive`
  - `--assume-yes`

## Guardrails

- `requires_ncm` modules are blocked by default unless `--allow-ncm` is given.
- `requires_usb_rebind` modules are blocked by default unless `--allow-usb-rebind` is given.
- `destructive` modules are blocked by default unless `--allow-destructive` is given.
- `operator_confirm_required` modules are blocked by default unless `--assume-yes` is given.
- Dry-run must not execute module code or mutate device/host state.

## Acceptance

- Static validation passes:

```bash
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py scripts/revalidation/a90harness/modules/*.py
git diff --check
```

- CLI validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py list
python3 scripts/revalidation/native_test_supervisor.py plan usb-recovery
python3 scripts/revalidation/native_test_supervisor.py run usb-recovery --dry-run
python3 scripts/revalidation/native_test_supervisor.py run kselftest-feasibility --dry-run
```

Expected behavior:

- `usb-recovery` dry-run reports blocked until `--allow-usb-rebind` and `--assume-yes`.
- `kselftest-feasibility` dry-run reports allowed.
- `list` and `plan` show exact module preconditions and required flags.

## Completion

v177 closes the v170-v177 host harness cycle and decides that Wi-Fi baseline
refresh can start on top of the supervisor.

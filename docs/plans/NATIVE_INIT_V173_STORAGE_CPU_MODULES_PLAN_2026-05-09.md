# Native Init v173 Storage/CPU Module Port Plan (2026-05-09)

## Summary

- label: `v173 Storage/CPU Module Port`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: port storage I/O and CPU/memory/thermal validators onto `native_test_supervisor.py run`.

v173 is host tooling only. It does not change or flash the boot image.

## Scope

- Add `storage-io` module wrapper for `scripts/revalidation/storage_iotest.py`.
- Add `cpu-mem-thermal` module wrapper for `scripts/revalidation/cpu_mem_thermal_stability.py`.
- Add module profile support to the supervisor:
  - `smoke`: shortest bounded validation.
  - later profiles can expand duration and data sizes.
- Keep existing standalone scripts usable.

## Guardrails

- `storage-io` requires host-configured USB NCM (`192.168.7.2`) because the existing validator transfers files over TCP.
- If NCM is not reachable, `storage-io` records a structured skip instead of attempting sudo, USB rebind, or host network mutation.
- `cpu-mem-thermal` uses a short smoke profile by default.
- Observer remains read-only and shares the module run directory.

## Acceptance

- Static validation passes:

```bash
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py scripts/revalidation/a90harness/modules/*.py
git diff --check
```

- CPU module:

```bash
python3 scripts/revalidation/native_test_supervisor.py run cpu-mem-thermal --profile smoke --observer-duration-sec 5
```

- Storage module:

```bash
python3 scripts/revalidation/native_test_supervisor.py run storage-io --profile smoke --observer-duration-sec 5
```

Expected behavior:

- CPU smoke must PASS.
- Storage smoke must PASS when NCM is already configured, otherwise it must report structured SKIP with the exact precondition reason.

## Next

- v174 USB/NCM Module Port.

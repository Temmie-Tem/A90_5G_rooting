# Native Init v174 USB/NCM Module Port Plan (2026-05-09)

## Summary

- label: `v174 USB/NCM Module Port`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: port USB recovery and NCM/TCP checks onto the supervisor module runner.

v174 is host tooling only. It does not change or flash the boot image.

## Scope

- Add `usb-recovery` module wrapper for `scripts/revalidation/usb_recovery_validate.py`.
- Add `ncm-tcp-preflight` module wrapper for `scripts/revalidation/tcpctl_host.py smoke`.
- Keep existing standalone scripts usable.

## Guardrails

- `usb-recovery` is an explicit USB rebind module and must use a bounded smoke profile.
- `ncm-tcp-preflight` requires host-configured USB NCM (`192.168.7.2`) and must structured-SKIP if unavailable.
- No module may run sudo or mutate host network configuration.
- Final USB recovery state should return to ACM-only.

## Acceptance

- Static validation passes:

```bash
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py scripts/revalidation/a90harness/modules/*.py
git diff --check
```

- USB recovery smoke:

```bash
python3 scripts/revalidation/native_test_supervisor.py run usb-recovery --profile smoke --observer-duration-sec 0
```

- NCM/TCP preflight:

```bash
python3 scripts/revalidation/native_test_supervisor.py run ncm-tcp-preflight --profile smoke --observer-duration-sec 5
```

Expected behavior:

- `usb-recovery` must PASS and leave ACM bridge recoverable.
- `ncm-tcp-preflight` must PASS when NCM is configured, otherwise structured-SKIP with a precondition reason.

## Next

- v175 Unified Evidence Bundle.

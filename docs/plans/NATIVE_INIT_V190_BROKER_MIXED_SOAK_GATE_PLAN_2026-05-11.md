# v190 Plan: Broker Mixed-Soak Gate

- date: `2026-05-11`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- cycle label: `v190` host-side broker/supervisor validation
- device flash: none

## Summary

v190 verifies that the host-side `A90B1` broker can sit in front of the mixed
soak supervisor without reintroducing raw ACM contention.

This is not a native-init boot image change. The device remains on the latest
verified native build, and the work is limited to host tooling and validation.

## Scope

- Add a broker-backed mixed-soak gate wrapper.
- Start an `a90_broker.py serve --backend acm-cmdv1` subprocess in a private
  runtime directory.
- Run `native_test_supervisor.py mixed-soak` with `--device-backend broker`.
- Use `cpu-memory-profiles` as the default workload so observer and workload
  commands both pass through the broker.
- Validate:
  - supervisor exit code
  - supervisor manifest `pass=true`
  - `device_client.backend=broker`
  - observer success
  - workload success
  - broker audit integrity
  - broker accepted/dispatched/result counts

## Non-Goals

- No NCM/tcpctl broker backend in v190.
- No Wi-Fi work.
- No native init version bump.
- No USB rebind/destructive mixed-soak workload.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker_mixed_soak_gate.py \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90_broker.py
```

```bash
python3 scripts/revalidation/a90_broker_mixed_soak_gate.py \
  --dry-run \
  --duration-sec 15 \
  --observer-interval 5
```

```bash
python3 scripts/revalidation/a90_broker_mixed_soak_gate.py \
  --duration-sec 45 \
  --observer-interval 10 \
  --workload-profile smoke \
  --seed 190
```

## Acceptance

- dry-run PASS
- live ACM broker mixed-soak PASS
- supervisor manifest says `pass=true`
- observer failures are `0`
- workload failures are `0`
- broker audit integrity is PASS
- every accepted broker request has exactly one dispatch and one result

## Next

If v190 passes, v191 should add the `ncm/tcpctl` broker backend.


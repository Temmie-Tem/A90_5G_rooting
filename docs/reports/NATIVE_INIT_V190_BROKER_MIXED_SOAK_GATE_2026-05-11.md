# Native Init v190 Broker Mixed-Soak Gate

- date: `2026-05-11`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- boot image change: none
- scope: host-side broker/supervisor mixed-soak validation

## Summary

v190 adds `scripts/revalidation/a90_broker_mixed_soak_gate.py`.

The gate starts an `A90B1` broker, runs `native_test_supervisor.py mixed-soak`
with `--device-backend broker`, then validates both the supervisor manifest and
broker audit. The default workload is `cpu-memory-profiles`, which keeps the
short live gate fully broker-owned: observer and workload commands both go
through the broker instead of writing the ACM bridge directly.

## Implementation

- Added broker mixed-soak wrapper:
  - private run directory
  - private broker runtime directory
  - broker subprocess lifecycle management
  - supervisor stdout capture
  - supervisor manifest validation
  - broker audit integrity/count/status validation
  - private summary/report output
- Updated revalidation README with v190 gate usage.
- Updated task queue and next-work documents.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker_mixed_soak_gate.py \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90_broker.py
```

Result: PASS.

### Dry Run

```bash
python3 scripts/revalidation/a90_broker_mixed_soak_gate.py \
  --dry-run \
  --duration-sec 15 \
  --observer-interval 5 \
  --run-dir tmp/a90-v190-dry-fixed-20260511-212931
```

Result:

```text
PASS backend=acm-cmdv1 workloads=cpu-memory-profiles supervisor_rc=0 failures=0 out=tmp/a90-v190-dry-fixed-20260511-212931
```

### Live ACM Broker Gate

```bash
python3 scripts/revalidation/a90_broker_mixed_soak_gate.py \
  --duration-sec 45 \
  --observer-interval 10 \
  --workload-profile smoke \
  --seed 190 \
  --run-dir tmp/a90-v190-live-fixed-20260511-212947
```

Result:

```text
PASS backend=acm-cmdv1 workloads=cpu-memory-profiles supervisor_rc=0 failures=0 out=tmp/a90-v190-live-fixed-20260511-212947
```

Supervisor manifest:

- pass: `true`
- duration_sec: `45.69750055199256`
- device_client.backend: `broker`
- workload_count: `1`
- pass_count: `1`
- skip_count: `0`
- blocked_count: `0`
- fail_count: `0`
- observer.ok: `true`
- observer.samples: `28`
- observer.failures: `0`

Broker audit:

- accepted: `42`
- dispatched: `42`
- results: `42`
- non_ok_results: `0`
- status_counts: `ok=42`
- class_counts: `observe=32`, `exclusive=10`
- backend_counts: `acm-cmdv1=42`
- integrity: PASS

## Decision

v190 is PASS.

The broker-backed supervisor gate is now usable as the next baseline before
adding an NCM/tcpctl broker backend. v191 should focus on transport backend
selection and authenticated tcpctl request handling while keeping ACM as the
rescue/fallback path.


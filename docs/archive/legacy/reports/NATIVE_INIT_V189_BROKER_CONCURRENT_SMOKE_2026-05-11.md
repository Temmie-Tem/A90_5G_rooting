# Native Init v189 Broker Concurrent Smoke

- date: `2026-05-11`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- boot image change: none
- scope: host-side `A90B1` broker concurrency validation

## Summary

v189 adds `scripts/revalidation/a90_broker_concurrent_smoke.py`.

The goal is to prove that multiple host clients can submit broker requests at
the same time while the broker remains the single owner of the backend control
path. The backend command stream is serialized through the broker worker queue,
and rebind/destructive commands remain blocked with `operator-required`.

## Implementation

- Added concurrent smoke script:
  - starts a private broker subprocess by default
  - supports `fake` and `acm-cmdv1` backends
  - sends concurrent `version`, `status`, `bootstatus`, and `selftest verbose`
    requests
  - optionally sends blocked `reboot` requests to verify raw-control separation
  - validates response ids, protocol, rc/status, expected version, and blocked
    command status
  - writes private evidence:
    - `concurrent-smoke-summary.json`
    - `concurrent-smoke-responses.json`
    - `concurrent-smoke-report.md`
    - `broker-audit-summary.json`
    - `broker-audit-report.md`
- Updated revalidation README with concurrent smoke examples.
- Updated task queue and next-work documents with v189 PASS status.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py \
  scripts/revalidation/a90harness/device.py
```

Result: PASS.

### Fake Backend

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend fake \
  --clients 4 \
  --rounds 3 \
  --include-blocked \
  --run-dir tmp/a90-v189-fake-20260511-204752
```

Result:

```text
PASS backend=fake clients=4 rounds=3 requests=16 failed=0 blocked_expected=4 out=tmp/a90-v189-fake-20260511-204752
```

Summary:

- requests: `16`
- ok: `16`
- failed: `0`
- blocked_expected: `4`
- audit_ok: `true`

### Live ACM Backend

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend acm-cmdv1 \
  --clients 4 \
  --rounds 2 \
  --include-blocked \
  --expect-version "A90 Linux init 0.9.59 (v159)" \
  --run-dir tmp/a90-v189-live-20260511-204803
```

Result:

```text
PASS backend=acm-cmdv1 clients=4 rounds=2 requests=12 failed=0 blocked_expected=4 out=tmp/a90-v189-live-20260511-204803
```

Summary:

- requests: `12`
- ok: `12`
- failed: `0`
- blocked_expected: `4`
- duration_sec: `3.392097`
- audit_ok: `true`

Audit:

- accepted: `12`
- dispatched: `12`
- results: `12`
- non_ok_results: `4`
- status_counts: `ok=8`, `operator-required=4`
- class_counts: `observe=8`, `rebind-destructive=4`
- integrity: PASS

## Decision

v189 is PASS.

The broker can accept concurrent host-local clients while preserving a single
serialized backend command owner. This is sufficient to move the next decision
to either:

- v190 NCM/tcpctl broker backend
- v190 broker mixed-soak gate


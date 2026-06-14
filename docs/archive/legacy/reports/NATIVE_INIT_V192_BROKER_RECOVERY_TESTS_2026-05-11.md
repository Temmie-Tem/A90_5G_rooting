# Native Init v192 Broker Failure/Recovery Tests

- date: `2026-05-11`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- boot image change: none
- scope: host-side broker failure/recovery validation

## Summary

v192 adds `scripts/revalidation/a90_broker_recovery_tests.py`.

The test runner validates expected broker failure states and recovery paths:

- blocked command audit
- broker restart after stale socket
- stale non-socket path refusal
- NCM listener-down `transport-error`
- `ncm-tcpctl` ACM fallback for native shell built-ins

## Implementation

- Added recovery test script:
  - fake backend tests by default
  - live tests behind `--include-live`
  - private JSON/Markdown evidence
  - per-runtime broker audit summaries
- Updated README, task queue, and next-work documents.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker_recovery_tests.py \
  scripts/revalidation/a90_broker.py
```

Result: PASS.

### Fake-Only Recovery

```bash
python3 scripts/revalidation/a90_broker_recovery_tests.py \
  --run-dir tmp/a90-v192-fake-20260511-214426
```

Result:

```text
PASS tests=3 failed=0 include_live=False out=tmp/a90-v192-fake-20260511-214426
```

Coverage:

- blocked command audit: PASS
- broker restart stale socket recovery: PASS
- stale non-socket path refusal: PASS

### Live Recovery

```bash
python3 scripts/revalidation/a90_broker_recovery_tests.py \
  --include-live \
  --run-dir tmp/a90-v192-live-20260511-214438
```

Result:

```text
PASS tests=5 failed=0 include_live=True out=tmp/a90-v192-live-20260511-214438
```

Coverage:

- blocked command audit: PASS
  - status: `operator-required`
  - audit: accepted=1 dispatched=1 results=1 non_ok=1
- broker restart stale socket recovery: PASS
  - first status: `ok`
  - down connection failed as expected
  - second status after restart: `ok`
- stale non-socket path refusal: PASS
  - broker refused to replace non-socket socket path
- NCM listener down: PASS
  - status: `transport-error`
  - error: `ConnectionRefusedError`
  - audit backend: `ncm-tcpctl`
- ACM fallback: PASS
  - status: `ok`
  - response backend: `acm-cmdv1`
  - audit backend: `acm-cmdv1`

## Decision

v192 is PASS.

The v185→v192 broker sequence now covers:

- host-local broker skeleton
- harness broker backend
- audit reporting
- concurrent smoke
- mixed-soak gate
- NCM/tcpctl run backend
- failure/recovery classification

The next cycle should be selected from broker/auth hardening, NCM listener
lifecycle automation, Wi-Fi baseline preparation, or fresh security scan
follow-up.


# v192 Plan: Broker Failure/Recovery Tests

- date: `2026-05-11`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- cycle label: `v192` host-side broker failure/recovery validation
- device flash: none

## Summary

v192 adds a focused broker recovery test runner.

The goal is not to add another transport. The goal is to prove that failures
introduced by the broker boundary are classified and recoverable:

- blocked command audit remains explicit
- stale Unix socket paths can be replaced on restart
- non-socket runtime path attacks are refused
- NCM listener-down state becomes `transport-error`
- `ncm-tcpctl` can still fall back to ACM for native shell built-ins

## Scope

- Add `scripts/revalidation/a90_broker_recovery_tests.py`.
- Run fake backend tests by default.
- Run live ACM/NCM-path tests only with `--include-live`.
- Write private JSON/Markdown evidence.

## Non-Goals

- No native init build change.
- No new broker backend.
- No automatic host NCM sudo setup.
- No destructive/rebind foreground operation.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker_recovery_tests.py \
  scripts/revalidation/a90_broker.py
```

```bash
python3 scripts/revalidation/a90_broker_recovery_tests.py
```

```bash
python3 scripts/revalidation/a90_broker_recovery_tests.py --include-live
```

## Acceptance

- fake-only tests PASS
- live tests PASS
- blocked command returns `operator-required`
- NCM listener-down run request returns `transport-error`
- fallback `version` request returns `ok` through `acm-cmdv1`
- audit integrity is PASS for every broker runtime used by the tests

## Next

If v192 passes, v193 should be selected from:

- broker/auth hardening follow-up
- NCM listener lifecycle automation
- Wi-Fi baseline refresh preparation
- fresh security scan follow-up


# F047/F048/F052 Batch H1 Report

Date: `2026-05-12`
Scope: host-side broker authorization, tcpctl final status parsing, recovery token leak prevention

## Summary

Batch H1 mitigates:

- `F047`: live recovery test can leak tcpctl auth token;
- `F048`: broker forwards exclusive root commands without authorization;
- `F052`: NCM broker treats auth OK as command success.

This is a host tooling change only. It does not change the native-init boot image.

## Changes

- `scripts/revalidation/a90_broker.py`
  - Added `BrokerPolicy` with default observe-only behavior.
  - Added `--allow-operator` and `--allow-exclusive` serve flags.
  - Kept `rebind-destructive` commands out of broker multiplexing.
  - Added Unix socket peer credential capture to broker audit records when available.
  - Changed `NcmTcpctlBackend.tcpctl_status()` to inspect the final non-empty tcpctl line.
- `scripts/revalidation/a90_broker_recovery_tests.py`
  - Added a listener-down port precheck.
  - Changed the NCM listener-down negative test to use explicit no-auth/allow-no-auth and allow-exclusive, avoiding real token retrieval for an arbitrary listener.
- `scripts/revalidation/a90_broker_concurrent_smoke.py`
  - Added pass-through `--allow-operator` and `--allow-exclusive` options.
- `scripts/revalidation/a90_broker_mixed_soak_gate.py`
  - Starts its broker with `--allow-exclusive` because mixed-soak intentionally runs exclusive workload commands.
- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py`
  - Passes `--allow-exclusive` to broker concurrent smoke for authenticated NCM `run` checks.
- `scripts/revalidation/a90_broker_auth_hardening_check.py`
  - Added default policy checks, allow-exclusive checks, and tcpctl parser fixture checks.
- `scripts/revalidation/README.md`
  - Documents default observe-only policy and explicit exclusive mode.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_recovery_tests.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py \
  scripts/revalidation/a90_broker_auth_hardening_check.py \
  scripts/revalidation/a90_broker_mixed_soak_gate.py \
  scripts/revalidation/a90_broker_ncm_lifecycle_check.py
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker.py selftest
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_auth_hardening_check.py \
  --run-dir tmp/a90-h1-auth-check-2
```

Result: PASS.

Checks include:

- default broker policy blocks `run`, `menu`, and `reboot` appropriately;
- `--allow-exclusive` permits exclusive and operator command classes;
- tcpctl final status parser rejects `OK authenticated` followed by final `ERR exit=1`;
- existing no-auth hardening checks still pass.

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend fake \
  --clients 2 \
  --rounds 2 \
  --include-blocked \
  --run-dir tmp/a90-h1-fake-smoke-2
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_recovery_tests.py \
  --run-dir tmp/a90-h1-recovery-fake
```

Result: PASS.

Targeted recovery leak precheck fixture:

```text
result.ok=false
result.detail=unsafe precheck: 127.0.0.1:29999 is open; refused to send request
captured_len=0
```

This confirms the live listener-down path refuses to send a request when the negative-test port is already open.

```bash
git diff --check
```

Result: PASS.

## Remaining

Batch H2 still needs to address:

- `F050`: outer soak timeout can orphan live broker processes;
- `F051`: default lifecycle run can fail to stop tcpctl listener.

Batch H3 still needs duplicate/closure evidence for:

- `F049` linked to `F045`;
- `F053` linked to `F046`.

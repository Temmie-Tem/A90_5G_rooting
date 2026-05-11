# v193 Broker/Auth Hardening Follow-up

## Summary

v193 hardens the host-local `A90B1` broker auth boundary. This is a host tooling
change only; the latest verified native-init device build remains
`A90 Linux init 0.9.59 (v159)`.

## Changes

- Updated `scripts/revalidation/a90_broker.py`:
  - `ncm-tcpctl --no-auth` now requires explicit `--allow-no-auth`.
  - explicit tcpctl tokens are validated before broker startup.
  - token-like values are redacted from broker errors and sanitized audit output.
  - tcpctl `ERR auth-*` responses are classified as `auth-failed`.
  - broker metadata records auth policy without storing token values.
- Updated `scripts/revalidation/a90_broker_concurrent_smoke.py` to pass
  `--allow-no-auth` when legacy negative tests intentionally need it.
- Added `scripts/revalidation/a90_broker_auth_hardening_check.py`.
- Updated broker README and task queue docs.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py \
  scripts/revalidation/a90_broker_auth_hardening_check.py
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_auth_hardening_check.py \
  --run-dir tmp/a90-v193-auth-check
```

Result: PASS.

Evidence:

- `tmp/a90-v193-auth-check/broker-auth-hardening-summary.json`
- `tmp/a90-v193-auth-check/broker-auth-hardening-report.md`

Checks:

- broker selftest: PASS
- no-auth denied unless explicitly allowed: PASS
- invalid token rejected cleanly: PASS
- explicit no-auth records disabled auth metadata: PASS

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend fake \
  --clients 2 \
  --rounds 2 \
  --include-blocked \
  --run-dir tmp/a90-v193-fake-regress
```

Result: PASS.

## Acceptance

- No unauthenticated NCM/tcpctl broker mode is enabled accidentally.
- Token values are not persisted in broker metadata or sanitized audit output.
- Existing broker fake concurrency behavior remains intact.

## Next

v194 should automate NCM/tcpctl listener lifecycle around broker-backed tests so
operators no longer need to manually start a max-client-unlimited listener before
NCM broker validation.

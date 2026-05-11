# v193 Plan: Broker/Auth Hardening Follow-up

## Summary

v193 is a host-tooling hardening release for the `A90B1` broker. It does not
change the native-init boot image. The goal is to make the v191/v192 NCM/tcpctl
backend safer before any broader network exposure work.

## Scope

- Require an explicit second flag for legacy unauthenticated `ncm-tcpctl` broker
  mode.
- Validate explicit broker tcpctl tokens before the broker starts.
- Redact token-like values from broker error/audit/report paths.
- Classify tcpctl authentication failures as `auth-failed` instead of generic
  backend errors.
- Add a host-only validator for the hardening behavior.

## Non-Goals

- Do not start or stop the device-side `a90_tcpctl` listener.
- Do not change Wi-Fi, NCM interface setup, or native-init PID1 code.
- Do not remove the legacy no-auth path completely; keep it available only for
  explicit negative tests.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py \
  scripts/revalidation/a90_broker_auth_hardening_check.py

python3 scripts/revalidation/a90_broker_auth_hardening_check.py \
  --run-dir tmp/a90-v193-auth-check

python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend fake \
  --clients 2 \
  --rounds 2 \
  --include-blocked \
  --run-dir tmp/a90-v193-fake-regress
```

## Acceptance

- `--no-auth` without `--allow-no-auth` fails closed.
- Invalid tokens fail before broker socket creation without Python traceback.
- Explicit legacy no-auth mode records `auth.required=false` and
  `token_source=disabled` in private broker metadata.
- Existing fake concurrent smoke and broker selftest remain PASS.

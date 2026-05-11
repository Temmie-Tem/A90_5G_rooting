# v191 Plan: NCM/tcpctl Broker Backend

- date: `2026-05-11`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- cycle label: `v191` host-side broker backend expansion
- device flash: none

## Summary

v191 adds a thin `ncm-tcpctl` backend to the host-local `A90B1` broker.

The backend does not replace the native shell. It only routes
`run /absolute/path ...` requests through token-authenticated NCM `a90_tcpctl`.
Native init built-ins such as `version`, `status`, `selftest`, and `netservice`
continue to use ACM `cmdv1` fallback.

## Scope

- Add `a90_broker.py serve --backend ncm-tcpctl`.
- Add backend result metadata so audit result rows can show the actual backend:
  - `ncm-tcpctl` for TCP `run` requests
  - `acm-cmdv1` for fallback built-ins
- Keep rebind/destructive commands blocked by broker policy.
- Extend `a90_broker_concurrent_smoke.py` to start NCM backend brokers.

## Preconditions

- Host NCM interface configured as `192.168.7.1/24`.
- Device reachable at `192.168.7.2`.
- `a90_tcpctl` listener running on `192.168.7.2:2325`.
- tcpctl token is provided by `--token` or available through ACM fallback.

## Non-Goals

- No automatic NCM host interface sudo setup inside the broker.
- No automatic tcpctl listener lifecycle management inside the broker.
- No Wi-Fi exposure.
- No native init version bump.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py
```

```bash
python3 scripts/revalidation/a90_broker.py selftest
```

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend ncm-tcpctl \
  --token "$A90_TCPCTL_TOKEN" \
  --clients 4 \
  --rounds 3 \
  --command "run /cache/bin/toybox uptime" \
  --command "run /cache/bin/toybox uname -a"
```

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend ncm-tcpctl \
  --token "$A90_TCPCTL_TOKEN" \
  --clients 1 \
  --rounds 1 \
  --command version \
  --expect-version "A90 Linux init 0.9.59 (v159)"
```

## Acceptance

- fake/acm broker regression remains PASS.
- NCM `run` smoke PASS.
- NCM audit result backend is `ncm-tcpctl`.
- fallback `version` smoke PASS.
- fallback audit result backend is `acm-cmdv1`.
- broker audit integrity remains PASS.

## Next

If v191 passes, v192 should add broker failure/recovery tests.


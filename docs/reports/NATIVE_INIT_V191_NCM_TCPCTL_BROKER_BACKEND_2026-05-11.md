# Native Init v191 NCM/tcpctl Broker Backend

- date: `2026-05-11`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- boot image change: none
- scope: host-side broker backend expansion

## Summary

v191 adds `ncm-tcpctl` as an `A90B1` broker backend.

The backend is intentionally narrow. It sends `run /absolute/path ...` requests
over token-authenticated NCM `a90_tcpctl`, while native init shell built-ins
fall back to ACM `cmdv1`. This preserves ACM as the rescue/native control path
and lets the broker audit show whether a request actually used NCM or ACM.

## Implementation

- Updated `scripts/revalidation/a90_broker.py`:
  - added `BackendResult`
  - added `NcmTcpctlBackend`
  - added `serve --backend ncm-tcpctl`
  - added NCM options: `--device-ip`, `--tcp-port`, `--tcp-timeout`, `--token`, `--no-auth`
  - result audit now records actual backend returned by the backend implementation
- Updated `scripts/revalidation/a90_broker_concurrent_smoke.py`:
  - accepts `--backend ncm-tcpctl`
  - passes NCM/tcpctl options to the broker subprocess
- Updated README, task queue, and next-work docs.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py \
  scripts/revalidation/a90_broker_mixed_soak_gate.py
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker.py selftest
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend fake \
  --clients 3 \
  --rounds 2 \
  --include-blocked \
  --run-dir tmp/a90-v191-fake-regress-20260511-213447
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend acm-cmdv1 \
  --clients 2 \
  --rounds 1 \
  --include-blocked \
  --expect-version "A90 Linux init 0.9.59 (v159)" \
  --run-dir tmp/a90-v191-acm-regress-20260511-213727
```

Result: PASS.

## Live NCM Setup

Host NCM was configured through NetworkManager because direct `sudo ip addr`
was blocked by sudo authentication:

```bash
nmcli con add type ethernet ifname enxa63ce1dd2035 \
  con-name a90-ncm-v191 \
  ipv4.method manual \
  ipv4.addresses 192.168.7.1/24 \
  ipv6.method disabled \
  autoconnect no
nmcli con up a90-ncm-v191
ping -c 1 -W 2 192.168.7.2
```

Result: PASS.

The v159 ramdisk does not contain `/bin/a90_tcpctl`, so the live validation used
the existing verified `/cache/bin/a90_tcpctl` helper:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_tcpctl \
  --toybox /cache/bin/toybox \
  --token <redacted> \
  --idle-timeout 120 \
  --max-clients 0 \
  start
```

The first attempt used the default `max_clients=8`; the listener exited after
serving 8 requests and the final 4 broker requests correctly failed with
`transport-error`. The PASS run used `max_clients=0`.

## NCM Backend Smoke

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend ncm-tcpctl \
  --token <redacted> \
  --clients 4 \
  --rounds 3 \
  --command "run /cache/bin/toybox uptime" \
  --command "run /cache/bin/toybox uname -a" \
  --run-dir tmp/a90-v191-ncm-smoke-fixed-20260511-213909
```

Result:

```text
PASS backend=ncm-tcpctl clients=4 rounds=3 requests=12 failed=0 blocked_expected=0 out=tmp/a90-v191-ncm-smoke-fixed-20260511-213909
```

Audit:

- accepted: `12`
- dispatched: `12`
- results: `12`
- non_ok_results: `0`
- backend_counts: `ncm-tcpctl=12`
- status_counts: `ok=12`
- class_counts: `exclusive=12`
- integrity: PASS

## ACM Fallback Smoke

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend ncm-tcpctl \
  --token <redacted> \
  --clients 1 \
  --rounds 1 \
  --command version \
  --expect-version "A90 Linux init 0.9.59 (v159)" \
  --run-dir tmp/a90-v191-ncm-fallback-20260511-213933
```

Result: PASS.

Audit:

- accepted: `1`
- dispatched: `1`
- results: `1`
- backend_counts: `acm-cmdv1=1`
- status_counts: `ok=1`
- integrity: PASS

## Decision

v191 is PASS.

The broker now has a working NCM/tcpctl backend for `run` requests and a verified
ACM fallback for native shell built-ins. v192 should focus on failure and
recovery behavior: NCM listener down, stale socket, backend timeout, broker
crash, and blocked command audit classification.


# F050/F051 Batch H2 Report

Date: `2026-05-12`
Scope: host-side broker soak timeout cleanup and NCM lifecycle token propagation

## Summary

Batch H2 mitigates:

- `F050`: outer soak timeout can orphan live broker processes;
- `F051`: default lifecycle run can fail to stop tcpctl listener.

This is a host tooling change only. It does not change the native-init boot image.

## Changes

- `scripts/revalidation/a90_broker_soak_suite.py`
  - Replaced `subprocess.run(..., timeout=...)` with explicit `Popen(..., start_new_session=True)` and controlled `communicate(timeout=...)` handling.
  - On timeout, terminates the immediate process group and records `[TIMEOUT]` evidence.
  - Adds suite-owned orphan broker cleanup by scanning for `a90_broker.py` processes under the suite run directory and terminating their process groups.
  - Adds `timed_out` to suite step evidence and report output.
- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py`
  - Captures one tcpctl token before starting the long-running listener when no CLI token was supplied.
  - Passes the same token to `tcpctl_host.py start`, broker smoke, and `tcpctl_host.py stop`.
  - Redacts the token in planned command evidence.
  - Adds token command/path/bridge-timeout pass-through arguments for consistency with `tcpctl_host.py`.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker_soak_suite.py \
  scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  scripts/revalidation/tcpctl_host.py \
  scripts/revalidation/a90_broker.py
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_soak_suite.py \
  --dry-run \
  --duration-sec 1 \
  --observer-interval 1 \
  --run-dir tmp/a90-h2-soak-suite-dry-2
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  --dry-run \
  --token 0123456789ABCDEF0123456789ABCDEF \
  --run-dir tmp/a90-h2-lifecycle-dry-2
```

Result: PASS.

Follow-up check on `planned-commands.json`:

- raw token does not appear;
- `<redacted>` appears;
- `--token` is present in start, smoke, and stop command plans.

Timeout fixture:

```text
SuiteStep(name='timeout-child', ok=False, rc=124, timed_out=True)
[TIMEOUT] step exceeded 0.5s; process group terminated
```

```bash
git diff --check
```

Result: PASS.

## Remaining

Batch H3 still needs duplicate/closure evidence for:

- `F049` linked to `F045`;
- `F053` linked to `F046`.

A live NCM lifecycle run is still recommended before broader Wi-Fi work, but the code-level issue is addressed and dry-run/token propagation evidence is present.

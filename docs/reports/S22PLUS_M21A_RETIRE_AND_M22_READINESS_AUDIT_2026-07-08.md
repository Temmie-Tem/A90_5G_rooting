# S22+ M21A Retire + M22 Readiness Audit (2026-07-08)

## Verdict

Host-only progress. No live flash, reboot, Odin transfer, Android command,
partition write, sysfs write, or recovery action was performed.

M21A is now retired as an unconsumed stale live authorization. The current
forward path remains observability-first: M22 retained-console positive-control
is staged and audited, but still inactive until a fresh operator approval
promotes the inert policy draft.

## Why

After M20A and P00, the Download-mode beacon is still not a reliable native-init
proof channel. M21A would only further characterize that beacon. The higher-value
path is to prove whether the DTBO-enabled ramoops channel can retain an
intentional kernel-crash marker.

## M21A Retirement

`AGENTS.md` now marks the M21A raw nanosleep-download floor-discriminator and
its M21A Odin path as retired/unconsumed. The active M21A ack strings are
intentionally absent from `AGENTS.md`, so the M21A helper fails closed at the
policy marker gate.

Validation:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m21a_raw_nanosleep_download_live_gate.py \
  --offline-check

rc=1
AGENTS.md missing M21A live authorization markers: [...]
```

## M22 Readiness Audit

Added:

```text
workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit.py
tests/test_s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit.py
```

Audit result:

```text
result = pass
draft.complete = true
agents.complete = false
offline_check.returncode = 0
print_plan.returncode = 0
default_fail_closed.returncode = 1
```

The audit proves:

- the inert M22 exception draft contains the required pinned markers;
- active `AGENTS.md` is incomplete, so M22 live is still not authorized;
- the M22 gate `--offline-check` verifies DTBO/M22/rollback APs without device action;
- `--print-plan` includes the retained marker
  `S22_NATIVE_INIT_M22_KMSG_SYSRQ_PANIC`, `sysrq-trigger-c`, rollback, and stock
  DTBO cleanup commands;
- default execution fails closed at the AGENTS marker gate before Android/device
  access.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests/test_s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit.py \
  --expect-agents-active --no-default-fail-closed-check
```

Expected active-policy audit result is nonzero while M22 remains inert.

## Next

Do not run M21A, P10, M20B/M20C, or wider native-init prefixes by default. The
next live-capable step, only after explicit operator approval, is to promote the
M22 inert AGENTS draft, run the M22 default dry-run, then run the attended M22
retained-console gate.

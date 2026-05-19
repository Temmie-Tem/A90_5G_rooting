# v367 Report: Runtime Repair Smoke Gate Regression

- date: `2026-05-20`
- scope: host-only V366 approval/preexisting-node gate regression
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- plan: `docs/plans/NATIVE_INIT_V367_RUNTIME_REPAIR_SMOKE_REGRESSION_PLAN_2026-05-20.md`
- result: `PASS`, decision `runtime-repair-smoke-regression-pass`

## Summary

V367 fixes the V366 approval path so preflight blockers are evaluated before any
approved mutation step. This matters because `preexisting-temp-nodes` must be a
real pre-mutation blocker, not a post-run observation.

The new regression is host-only. It monkeypatches V366 live command functions,
so it never opens the serial bridge and never touches the device. This lets us
verify both refusal behavior and approved-path ordering without executing the
real temporary node smoke.

## Evidence

| item | path | decision |
| --- | --- | --- |
| synthetic regression | `tmp/wifi/v367-runtime-repair-smoke-regression-20260520-010304/` | `runtime-repair-smoke-regression-pass` |
| live no-approval refresh | `tmp/wifi/v367-v366-refusal-refresh-20260520-010326/` | `runtime-repair-smoke-approval-required` |

Regression summary:

```text
decision: runtime-repair-smoke-regression-pass
pass: True
reason: approval and preexisting-node gates behave as expected without device commands
next: V366 live smoke remains blocked by exact approval phrase
```

Live no-approval refresh:

```text
decision: runtime-repair-smoke-approval-required
pass: True
preexisting-temp-nodes: clean present=[]
approval-gate: needs-operator phrase_match=False apply=False assume_yes=False
```

## Cases

| case | result |
| --- | --- |
| `run-no-approval-clean-refuses` | PASS, no mutation calls |
| `run-wrong-phrase-full-flags-refuses` | PASS, no mutation calls |
| `run-approved-clean-executes-synthetic-smoke` | PASS, synthetic create/stat/property/cleanup calls observed |
| `run-approved-preexisting-vendor-blocks-before-mutation` | PASS, blocked before mutation calls |
| `run-approved-preexisting-binder-blocks-before-mutation` | PASS, blocked before mutation calls |

## Guardrails Kept

- No service-manager, Wi-Fi HAL, `wificond`, supplicant, hostapd,
  `cnss-daemon`, or `cnss_diag` was started.
- No Wi-Fi scan/connect/link-up was executed.
- No temporary `/dev` node was created by the regression or no-approval refresh.
- The real V366 live smoke remains blocked until the exact approval phrase is
  supplied.

## Next Step

Exact phrase still required for real V366 live smoke:

```text
approve v366 bounded runtime repair smoke only; no service-manager start and no Wi-Fi bring-up
```

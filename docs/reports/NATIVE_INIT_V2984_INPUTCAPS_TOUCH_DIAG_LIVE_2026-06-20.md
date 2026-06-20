# Native Init V2984 Inputcaps Touch Diagnostics Live

## Summary

- Decision: `v2984-inputcaps-live-pass-before-rollback`
- Result before rollback: `1`
- Track: Video playback / DOOM input prerequisite.
- Candidate: `A90 Linux init 0.10.62 (v2983-inputcaps-touch-diag)`
- Candidate SHA256: `3edb059b7887cd0577a98bc28b41f1ce8c643b4234b7d3100896bb27aa86d226`
- Private run dir: `workspace/private/runs/input/v2984-inputcaps-touch-diag-live-20260620-164505`

## Live Evidence

- Candidate version ok: `1`
- Candidate selftest fail=0: `1`
- Full `inputscan` rc: `0` events=`9` touch_candidates=`2`
- Candidate post-diagnostics selftest fail=0: `1`

## Touch Capability Diagnostics

| Event | rc | EV_ABS | BTN_TOUCH | MT_X | MT_Y | MT_TRACKING_ID | runtime_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `event6` | `0` | `1` | `1` | `1` | `1` | `1` | `unsupported` |
| `event8` | `0` | `1` | `1` | `1` | `1` | `1` | `unsupported` |

## Rollback Evidence

- Rollback attempted: `1`
- Rollback step ok: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Interpretation

- This unit does not prove live touch events; it explains the read-only capability/runtime-PM state after V2982 produced zero events.
- Capability verdict: touch/MT bits present on all requested events = `1`; runtime_status values = `unsupported`.
- Because both `event6` and `event8` expose `EV_ABS` + `BTN_TOUCH` + MT position/tracking bits and runtime PM reports `unsupported` rather than `suspended`, the prior zero-event samples are not explained by missing capabilities or a sysfs runtime-PM suspended state.
- Next branch: attempt a focused live `readinput` touch sample again with operator finger input on the proven MT-capable events, or choose the DOOM input fallback if real touches still produce no events.

## Safety

- Only the boot partition is flashed, through `native_init_flash.py`; rollback target is `v2321`.
- The live path only runs `inputscan` and `inputcaps`; it does not open an event stream, inject input, alter keymaps, or write touch configuration.
- Raw command output stays private under `workspace/private/runs/`; this report includes metadata only.

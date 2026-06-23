# Native Init V3128 DOOM Suspect Priority Audit

## Summary

- Run ID: `V3128`
- Decision: `v3128-doom-suspect-priority-audit-complete`
- Result: PASS
- Device flash: `no`; host-only evidence audit.
- Scope: close the operator-provided DOOM stutter suspect list against current V3124/V3127 live evidence.

## Suspect Status

### 1. producer_presenter_dual_sleep_or_unsynced_pacing

- Status: `closed`
- Conclusion: single presenter-token/pageflip pacing is stable; dual unsynced sleep is no longer the observed bottleneck
- Evidence:
  - V3127 pageflip avg/max us=16639/16666
  - V3127 seq missed/max_gap=0/1
  - V3127 paced-time telemetry available and presenter-token model validated

### 2. raw_frame_file_ipc_malloc_open_read_free

- Status: `closed`
- Conclusion: shared-mmap direct blit reduced presenter read cost to single-digit microseconds
- Evidence:
  - V3124 direct reader marker=1 read_avg_us=2
  - V3127 read_avg_us=3

### 3. dashboard_large_cpu_scaling

- Status: `closed`
- Conclusion: large per-frame presenter scaling is off the critical path; large DOOM frame stays within the 16.6ms vblank budget
- Evidence:
  - V3127 pre-scaled producer and 1:1-pre-scaled markers are present
  - V3127 draw_avg_us=4277 total_avg_us=6266

### 4. no_new_frame_sync

- Status: `closed`
- Conclusion: shared-frame sequence gating proves no presenter-side missed-frame stream in the bounded live runs
- Evidence:
  - V3127 shared seq missed/max_gap=0/1
  - V3124 shared seq missed/max_gap=0/1

### 5. low_frame_write_cadence_or_game_tick_cadence

- Status: `explained`
- Conclusion: when DOOM virtual time is paced per presented token, output-frame gametic repetition disappears; the prior stepped feel is original 35Hz DOOM cadence on a 60Hz panel
- Evidence:
  - V3127 smooth mode=1 telemetry=1
  - V3127 dump_gametic repeated/max_same_run=0/1
  - V3127 output_gametic_bounded=1

## Direct KMS Buffer Path

- Status: `defer`
- Reason: `not current bottleneck`
- Expected best-case saved time: `3 us` (current V3127 presenter read avg).
- Meaningful current win: `0`
- Code constraints:
  - a90_kms.c owns DRM fd, dumb-buffer maps, current buffer, and pageflip event wait inside static kms_state
  - a90_kms.h exposes framebuffer pointer only inside the native-init process; it does not expose a producer-safe back-buffer lease/export API
  - no PRIME/dma-buf export path is present in the current KMS source

## Key Metrics

- V3124 report: `docs/reports/NATIVE_INIT_V3124_DOOMGENERIC_SUMMARY_ONLY_DIRECT_BLIT_LIVE_2026-06-23.md`
- V3124 read/draw avg us: `2` / `4289`
- V3127 report: `docs/reports/NATIVE_INIT_V3127_DOOMGENERIC_SMOOTH_DEMO_DIRECT_BLIT_LIVE_2026-06-23.md`
- V3127 read/draw/total avg us: `3` / `4277` / `6266`
- V3127 flip avg/max us: `16639` / `16666`
- V3127 shared seq missed/max-gap: `0` / `1`
- V3127 dump gametic repeated/max-same-run: `0` / `1`

## Decision

- Do not implement helper-direct-KMS in this pass: it would remove at most the current `3 us` read stage while adding a broad display-ownership redesign.
- The actionable stutter path from the pasted suspect list is closed by current live evidence.
- Further visual quality work should be framed explicitly as a DOOM semantics/interpolation feature, not as another producer/presenter/IPC bug hunt.

## Validation

- Parsed V3124 and V3127 public reports.
- Inspected `a90_kms.c` / `a90_kms.h` ownership and export surface.
- `py_compile`: V3128 analyzer and focused tests.
- `unittest`: V3128 analyzer contract.
- `git diff --check`: PASS.

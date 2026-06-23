# Native Init V3125 DOOM Other Causes Recheck After V3124

- Date: 2026-06-23
- Cycle: `V3125`
- Track: DOOM visible demo residual stutter/audio/serial audit after V3124 live pass.
- Decision: `v3125-doom-other-causes-recheck-after-v3124-pass`

## Scope

This was a no-flash, read-only recheck. No boot image was built, flashed, or
rebooted.

The check reviewed the V3124 live result, the V3103/V3105 cadence experiments,
the V3124 source lineage, and current rollback-resident health. It separates
remaining visual causes from separate demo gaps such as real DOOM audio.

## Current Device State

- Managed serial bridge: running. Its status probe reported `busy-serial-lock`,
  but slow-mode serial commands completed.
- Resident: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`.
- `status`: transport/storage/display ready; `selftest fail=0`.
- `selftest verbose`: `pass=11 warn=1 fail=0`.
- NCM/tcpctl transport: ready. Concrete IP details are intentionally omitted.
- `audio status` on the rollback resident returned `unknown command`; this is
  not evidence about the V3124 candidate audio behavior.

## Evidence Reviewed

### V3124 Display And IPC

V3124 closed the V3122 validation-output gap and removed the measurable
presenter read/copy overhead:

- Frames requested/presented: `180 / 180`.
- Direct shared-blit reader: `shared-mmap-direct-blit`.
- Shared-frame read avg: `2 us`, down from the V3119 `477 us` baseline.
- Draw avg/max: `4289 / 4664 us`.
- Present avg: `1972 us`.
- Total avg/max: `6265 / 23766 us`.
- Pageflip delta avg/max: `16639 / 16663 us`.
- Shared missed/max-gap: `0 / 1`.
- Duplicate frame polls: `173`.

Interpretation: KMS/pageflip and shared-frame delivery are not the primary
remaining problem. The duplicate polls are consistent with the presenter
polling faster than the original-cadence producer publishes changed frames, not
with missed shared frames.

### Source Lineage

The V3124 visual candidate follows the original-cadence line:

`V3124 live -> V3123 source -> V3120 -> V3118 -> V3116 -> V3114 -> V3112 -> V3108 -> V3100`.

V3108 explicitly kept the original DOOM cadence instead of adopting the V3104
paced-tic diagnostic. Therefore V3124 is expected to retain original-speed
DOOM's visible game-tic quantization even after read/copy and scaling fixes.

### Cadence Experiments

V3105 proved the main visual quantizer:

- V3105 paced-time diagnostic: `flip_delta_avg_us=16626`,
  `flip_delta_max_us=16650`, `shared_missed_frames=0`.
- It forced `loop_tick.gametic_changed=300` and
  `loop_tick.gametic_repeated=0` for a 300-frame loop.
- The diagnostic is smoother because it advances DOOM virtual time by one
  35 Hz tic per presenter token, so gameplay speed is not original.

V3103 proved that changed-gametic-only presentation is not the right fix:

- 300-frame helper loop presented only `150` frames.
- Pageflip average regressed to about `49533 us`.
- Shared missed frames stayed `0`, so the regression was scheduling/cadence, not
  frame loss.

Interpretation: simply filtering to changed game tics makes cadence worse. The
viable choices are original-speed with interpolation/prediction, an explicit
non-original smooth demo mode, or a deliberate lower-rate present policy.

### Large Frame Cost

The old large CPU scaler is no longer the top suspect because V3124 is on
pre-scaled producer output plus direct shared blit:

- Frame mode/path: `minimal-large-pre-scaled-producer` /
  `producer-pre-scaled-raw-rowcopy`.
- No full clear: enabled.
- Read avg is now negligible.

The remaining draw work is still real (`4289 us` average on 960x600), and total
max reached `23766 us`, but pageflip delta stayed stable. This is a secondary
quality/performance budget item, not the current root cause of regular stepped
motion.

### Audio

Real DOOM music/SFX is still a separate feature gap:

- Reports and source expose bounded native tone co-run, not engine SFX/music.
- Foreground `video demo doom loop ...` does not start the audio co-run worker;
  background `loop-start` is the path that attempts the bounded tone co-run.
- V3124 explicitly records that it still uses bounded tone co-run, not real
  DOOM music/SFX.

Interpretation: missing sound is not a visual stutter cause. It should be
handled as a separate demo/audio activation unit.

### Serial Management

Serial command transport still shows management fragility:

- The bridge status probe can report `busy-serial-lock`.
- Earlier live runs recorded occasional missing `A90P1 END` markers.
- Slow-mode `version`, `status`, and `selftest verbose` succeeded in this
  recheck.

Interpretation: serial fragility can affect validation/dashboard management,
but optimized gameplay input and the V3124 visual path should be kept separated
from serial status polling.

## Ranked Remaining Causes / Issues

1. **Original DOOM 35 Hz game-tic cadence on a 60 Hz panel.** This remains the
   dominant explanation for the stepped feel after V3124.
2. **No interpolation/prediction layer.** V3124 keeps original speed but does
   not synthesize between game tics.
3. **Large pre-scaled producer draw budget.** It is no longer missing pageflips
   in V3124, but it is still measurable CPU work and should stay instrumented.
4. **Real DOOM audio absent.** The current demo path has bounded tone plumbing,
   not real WAD-driven SFX/music.
5. **Serial validation fragility.** Keep using slow/retry-aware management
   commands and avoid tying gameplay input to status polling.

## Recommended Next Unit

For visual smoothness, choose one semantic target before the next build:

1. Original-speed playable demo: prototype interpolation/prediction or a
   stable present policy that does not alter DOOM time.
2. Smooth showroom demo: add an explicit, labelled non-original smooth mode
   based on the V3105 paced-time proof.
3. Audio demo readiness: separately validate a bounded audible path first, then
   later implement real DOOM SFX/music if required.

No hidden KMS/pageflip, shared-frame IPC, or direct-blit regression is currently
more credible than the original-cadence explanation.

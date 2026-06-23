# Native Init V3105 DOOMGENERIC Paced Tic Live

## Summary

- Cycle: `V3105`
- Artifact under test: `workspace/private/inputs/boot_images/boot_linux_v3104_doomgeneric_paced_tic.img`
- Artifact SHA256: `f3c74471e642674be7e42797060f95cdeab346eebea9aeb5f3d6f42193150228`
- Resident after flash: `A90 Linux init 0.10.108 (v3104-doomgeneric-paced-tic)`
- Decision: `v3105-doomgeneric-paced-tic-live-pass-diagnostic-only`

V3105 flashed the exact V3104 boot artifact and verified resident health. The final
seeded paced-time build keeps the V3101-style 60 Hz pageflip cadence while eliminating
loop-time repeated `gametic` samples. This confirms the remaining visible stutter source
is DOOM's non-interpolated game-tic cadence, not KMS pageflip, shared-frame IPC, or 1:1
blit cost. It should stay diagnostic-only because it advances DOOM virtual time by one
35 Hz tic per 60 Hz presenter token, so gameplay speed is not original.

## Flash Gate

- Local boot image Android magic: pass.
- Local and readback SHA256: `f3c74471e642674be7e42797060f95cdeab346eebea9aeb5f3d6f42193150228`.
- Rollback precondition: v2321 clean identity image, v2237 fallback, v48 fallback, and TWRP recovery image present.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Post-flash version/status verification: pass.
- Post-loop selftest: `pass=12 warn=1 fail=0`.

## DOOM Status

- Active bridge: `v3104-doomgeneric-paced-tic`.
- Engine: `doomgeneric-private-link-v3104-paced-tic`.
- Frame IPC: `shared-mmap-seq`.
- Presenter: `kms-dumb-buffer-pageflip`.
- Pacing: `presenter-pageflip-pace-socket`.
- Scale: `large_frame=0`, `frame_scale=1:1`, `scale_path=raw-rowcopy`.
- Input: `udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`.
- Sequence telemetry: enabled.
- Gametic-present-only mode: disabled.
- Paced-time model: `presenter-token-doom-tic-quantum`.
- Paced-time quantum: `28571 us`.

## Live Results

### 180-frame loop

- `frames_presented=180`, `display.rc=0`, `loop.rc=0`, `helper_done=1`.
- `timing.total.avg_us=11219`, `timing.total.max_us=13250`.
- `timing.read.avg_us=171`, `timing.read.max_us=965`.
- `timing.draw.avg_us=774`, `timing.draw.max_us=1176`.
- `timing.present.avg_us=5771`, `timing.present.max_us=6897`.
- `seq.new_frame_polls=180`, `seq.duplicate_frame_polls=0`, `seq.read_errors=12`.
- `seq.shared_missed_frames=0`, `seq.shared_max_sequence_gap_frames=1`.
- `flip_events=180`, `flip_delta_avg_us=16626`, `flip_delta_min_us=16612`, `flip_delta_max_us=16648`.
- `pace_socket.tokens_sent=180`, `pace_socket.idle_tokens_sent=0`, `pace_socket.failures=0`, `pace_socket.wait_timeouts=0`.

Phase telemetry:

- `loop_tick.samples=180`
- `loop_tick.gametic_changed=180`
- `loop_tick.gametic_repeated=0`
- `draw_gametic.samples=222`
- `draw_gametic.changed_transitions=180`
- `draw_gametic.repeated_transitions=41`
- `dump_gametic.samples=180`
- `dump_gametic.changed_transitions=179`
- `dump_gametic.repeated_transitions=0`
- `dump_gametic.max_same_run=1`
- `paced_time.paced_ticks_ms=6344`
- `paced_time.advance_calls=180`

### 300-frame loop

- `frames_presented=300`, `display.rc=0`, `loop.rc=0`, `helper_done=1`.
- `timing.total.avg_us=11191`, `timing.total.max_us=17362`.
- `timing.read.avg_us=182`, `timing.read.max_us=977`.
- `timing.draw.avg_us=775`, `timing.draw.max_us=1318`.
- `timing.present.avg_us=5741`, `timing.present.max_us=11038`.
- `seq.new_frame_polls=300`, `seq.duplicate_frame_polls=0`, `seq.read_errors=11`.
- `seq.shared_missed_frames=0`, `seq.shared_max_sequence_gap_frames=1`.
- `flip_events=300`, `flip_delta_avg_us=16626`, `flip_delta_min_us=16609`, `flip_delta_max_us=16650`.
- `pace_socket.tokens_sent=300`, `pace_socket.idle_tokens_sent=0`, `pace_socket.failures=0`, `pace_socket.wait_timeouts=0`.

Phase telemetry:

- `loop_tick.samples=300`
- `loop_tick.gametic_changed=300`
- `loop_tick.gametic_repeated=0`
- `draw_gametic.samples=342`
- `draw_gametic.changed_transitions=300`
- `draw_gametic.repeated_transitions=41`
- `dump_gametic.samples=300`
- `dump_gametic.changed_transitions=299`
- `dump_gametic.repeated_transitions=0`
- `dump_gametic.max_same_run=1`
- `paced_time.paced_ticks_ms=9773`
- `paced_time.advance_calls=300`

## Interpretation

This separates the causes cleanly:

- KMS/pageflip is not the bottleneck: the 300-frame loop stayed at `16626 us` average flip delta.
- Shared-frame IPC is not dropping frames: `shared_missed_frames=0`.
- New-frame sync is not the remaining issue: sequence telemetry shows no duplicate frame polls in the final V3105 loops.
- DOOM's game-state cadence is the remaining visual quantizer: V3101 had 300 presented frames but only 150 changed `gametic`; V3105 forces 300 changed `gametic` samples for 300 displayed frames.

The cost is semantic. V3105 is smoother by making the game clock advance faster than
real-time original DOOM. That is useful proof, not a demo baseline.

## Implementation Note

The first V3104 live attempt advanced paced time from zero after `doomgeneric_Create()`.
That made the helper publish no frames (`frames_presented=0`, `helper_done=0`). The final
artifact seeds `paced_ticks_ms` from the accumulated setup `fake_ticks_ms` before enabling
paced time; the final artifact SHA above is the only V3104 artifact covered by this live
pass.

## Other Issues Checked

- Serial command transport still occasionally loses the `A90P1 END` marker on selftest
  output. Re-running observation commands with slower input framing worked; resident
  health remained `fail=0`.
- Audio remains separate from this visual cadence path. The DOOM status exposes
  `native-audio-corun-tone-v3053`, but actual DOOM SFX/music playback is not validated here.

## Next Step

Do not promote V3104/V3105 as the normal DOOM demo baseline. The practical next visual
path is either:

1. Keep original DOOM speed and add interpolation/prediction for camera/player motion.
2. Offer an explicit "smooth demo mode" that uses V3105-style faster virtual time, clearly
   labelled as non-original.
3. Try a stable lower-rate presenter, such as deliberate 30 Hz with original-time semantics,
   if demo smoothness matters more than immediate 60 Hz visual cadence.

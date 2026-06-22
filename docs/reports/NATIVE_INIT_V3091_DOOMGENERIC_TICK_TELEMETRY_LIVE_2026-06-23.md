# Native Init V3091 DOOMGENERIC Tick Telemetry Live Validation

## Summary

- Cycle: `V3091`
- Candidate flashed: `V3090` / `A90 Linux init 0.10.101 (v3090-doomgeneric-tick-telemetry)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3090_doomgeneric_tick_telemetry.img`
- Boot SHA256: `32b1fb8e1fb4b6a460b2ae8d8374983eee1d10076ecd3a23837f7f84d778269d`
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Result: PASS
- Rollback used: no

## Flash Gate

- Current resident before flash: V3086 pageflip cadence baseline, `selftest fail=0`.
- Rollback images confirmed before flash:
  - `boot_linux_v2321_usb_clean_identity_rodata.img` SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - `boot_linux_v2237_supplicant_terminate_poll.img` SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - `boot_linux_v48.img` present
- TWRP recovery image present at the private firmware input path.
- Local V3090 image Android boot magic and SHA256 were checked before flash.
- Remote pushed image SHA256 matched the local V3090 SHA256.
- Boot-block readback prefix SHA256 matched the local V3090 SHA256.

## Health Check

- `version`: `A90 Linux init 0.10.101 (v3090-doomgeneric-tick-telemetry)`
- `status`: boot OK, storage/runtime on SD, serial transport ready, NCM/tcpctl ready.
- `selftest verbose`: `pass=12 warn=1 fail=0`
- Final post-DOOM selftest: `pass=12 warn=1 fail=0`

## DOOM Status

- Engine bridge: `v3090-doomgeneric-tick-telemetry`
- Engine helper: `/bin/a90_doomgeneric_private_engine_v3090`
- Runtime WAD: present on SD, regular file, SHA256 matched expected.
- Frame IPC: `shared-mmap-seq`
- Input: `udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`
- Presenter: pageflip, pace socket active, min submit interval `0ms`
- Dashboard: native minimal fastdraw, large frame, fast 3:2 row-copy scale
- Audio mode: `native-audio-corun-tone-v3053`

## Bounded Loop

Command:

```text
video demo doom loop 180 --wad runtime-private --sha256 <expected-wad-sha256>
```

Result:

- `video.demo.doom.loop.rc=0`
- `frames_presented=179`
- `helper_done=1`
- `display.rc=0`
- `pace_socket.tokens_sent=180`
- `pace_socket.failures=0`
- `pace_socket.wait_timeouts=0`
- `buffer_allocations=1`

Timing probe:

| metric | avg us | max us |
| --- | ---: | ---: |
| alloc | 1 | 25 |
| read | 183 | 960 |
| begin | 4514 | 5467 |
| draw | 4350 | 16416 |
| present | 3770 | 16901 |
| total | 12818 | 27839 |

Pageflip telemetry:

- `flip_events=179`
- `flip_delta_count=178`
- `flip_delta_min_us=16587`
- `flip_delta_avg_us=18582`
- `flip_delta_max_us=33256`

## Tick Telemetry

Telemetry path read after the loop:

```text
/tmp/a90-doomgeneric-v3090-tick-telemetry.txt
```

Captured values:

| field | value |
| --- | ---: |
| frames_requested | 180 |
| loop_iterations | 180 |
| loop_rc | 0 |
| helper presented_frames | 222 |
| fake_ticks_ms | 3773 |
| sleep_calls | 3773 |
| sleep_ms_total | 3773 |
| getticks_calls | 7923 |
| i_get_time | 132 |
| gametic | 95 |
| ticrate | 35 |

Model markers:

- `fake_time_model=DG_SleepMs-accumulated`
- `pacing_model=presenter-pageflip-token`
- `input_model=udp-ncm-unix-dgram-file-fallback`

## Findings

1. Input is not the limiting factor in this sample. The bounded loop used no host input and still showed visible timing variance.
2. The display path is not perfectly locked to every 60 Hz vblank in this run. Average flip delta rose to about `18.6ms`, and max reached one missed-vblank class interval at about `33.3ms`.
3. The helper/presenter path still has occasional expensive frame stages. `draw.max_us=16416`, `present.max_us=16901`, and `total.max_us=27839` are enough to miss the next 16.6ms vblank when they land badly.
4. DOOM itself is not a 60 fps interpolated renderer here. The engine exposes `ticrate=35`, and this run ended with `gametic=95` for `179` displayed presenter frames. Some held or uneven visual motion is therefore expected even when pageflip is healthy.
5. The current time model is confirmed to be synthetic. The helper accumulated `3773ms` only through `DG_SleepMs(1)` calls rather than through a monotonic wall clock.
6. Actual DOOM sound effects are still not enabled by this lineage. The helper argv keeps `-nosound -nomusic`; the current audio path is the V3053 native corun tone path, not real DOOM SFX.

## Next Priority

1. Build a wall-clock tick candidate: make `DG_GetTicksMs()` return monotonic elapsed time and make `DG_SleepMs()` use a bounded real sleep or no-op policy selected for pageflip pacing. The goal is to compare `gametic`, `i_get_time`, presenter frames, and flip deltas against V3091.
2. If wall-clock ticks reduce game-time mismatch but flip spikes remain, isolate the display cost by running a large-scaling-off or 1:1 DOOM-only presenter sample.
3. Treat real DOOM audio as a separate sub-goal: remove `-nosound -nomusic` only after a safe native sound callback path exists.

## Validation Commands

- `python3 -m py_compile` with `PYTHONPYCACHEPREFIX=tmp/pycache-v3090`
- Focused unittest lineage: V3079/V3081/V3083/V3084/V3086/V3090
- `git diff --check`
- V3090 source build and marker check
- `native_init_flash.py --from-native --expect-version ... --expect-sha256 ... --expect-android-magic ...`
- `a90ctl version`
- `a90ctl status`
- `a90ctl selftest verbose`
- `a90ctl --hide-on-busy video demo doom status`
- `a90ctl --hide-on-busy video demo doom loop 180 ...`
- `a90ctl run /bin/busybox cat /tmp/a90-doomgeneric-v3090-tick-telemetry.txt`
- final `a90ctl selftest verbose`

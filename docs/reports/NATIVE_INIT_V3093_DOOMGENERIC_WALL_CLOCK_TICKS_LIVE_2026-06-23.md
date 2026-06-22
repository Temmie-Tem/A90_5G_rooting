# Native Init V3093 DOOMGENERIC Wall-Clock Ticks Live Validation

## Summary

- Cycle: `V3093`
- Candidate flashed: `V3092` / `A90 Linux init 0.10.102 (v3092-doomgeneric-wall-clock-ticks)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3092_doomgeneric_wall_clock_ticks.img`
- Boot SHA256: `2f0818db2843d555103ceca5d1e999da8d822c8034413dace0dd5b59dd8c0865`
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Result: PASS as a validation run, but the wall-clock sleep policy is not an improvement.
- Rollback used: no

## Flash Gate

- Current resident before flash: V3090 tick telemetry baseline, `selftest fail=0`.
- Rollback images confirmed before flash:
  - `boot_linux_v2321_usb_clean_identity_rodata.img` SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - `boot_linux_v2237_supplicant_terminate_poll.img` SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - `boot_linux_v48.img` present
- TWRP recovery image present at the private firmware input path.
- Local V3092 image Android boot magic and SHA256 were checked before flash.
- Remote pushed image SHA256 matched the local V3092 SHA256.
- Boot-block readback prefix SHA256 matched the local V3092 SHA256.

## Health Check

- `version`: `A90 Linux init 0.10.102 (v3092-doomgeneric-wall-clock-ticks)`
- `status`: boot OK, storage/runtime on SD, serial transport ready, NCM/tcpctl ready.
- `selftest verbose`: `pass=12 warn=1 fail=0`
- Final post-DOOM selftest: `pass=12 warn=1 fail=0`
- Serial note: one immediate post-flash command was mis-encoded as `cmdAT...`; subsequent validation used `a90ctl --input-mode slow` and was stable.

## DOOM Status

- Engine bridge: `v3092-doomgeneric-wall-clock-ticks`
- Engine helper: `/bin/a90_doomgeneric_private_engine_v3092`
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
- Command duration: `6543ms`
- Presenter poll count: `449`
- `buffer_allocations=1`

Timing probe:

| metric | avg us | max us |
| --- | ---: | ---: |
| alloc | 1 | 26 |
| read | 186 | 981 |
| begin | 4480 | 6018 |
| draw | 4281 | 5569 |
| present | 10911 | 15763 |
| total | 19859 | 27633 |

Pageflip telemetry:

- `flip_events=179`
- `flip_delta_count=178`
- `flip_delta_min_us=16578`
- `flip_delta_avg_us=29311`
- `flip_delta_max_us=33264`

## Tick Telemetry

Telemetry path read after the loop:

```text
/tmp/a90-doomgeneric-v3092-tick-telemetry.txt
```

Captured values:

| field | V3092 value |
| --- | ---: |
| frames_requested | 180 |
| loop_iterations | 180 |
| loop_rc | 0 |
| helper presented_frames | 222 |
| ticks_ms | 6461 |
| sleep_requested_ms | 1125 |
| sleep_calls | 1125 |
| sleep_ms_total | 1125 |
| getticks_calls | 2794 |
| i_get_time | 225 |
| gametic | 189 |
| ticrate | 35 |

Model markers:

- `time_model=clock-monotonic-elapsed`
- `fake_time_model=disabled-wall-clock-active`
- `sleep_policy=usleep-requested-ms`
- `pacing_model=presenter-pageflip-token`
- `input_model=udp-ncm-unix-dgram-file-fallback`

## Comparison With V3091

| metric | V3091 fake-time telemetry | V3092 wall-clock sleep |
| --- | ---: | ---: |
| command duration ms | 3502 | 6543 |
| frames_presented | 179 | 179 |
| flip_delta_avg_us | 18582 | 29311 |
| flip_delta_max_us | 33256 | 33264 |
| total.avg_us | 12818 | 19859 |
| draw.max_us | 16416 | 5569 |
| present.avg_us | 3770 | 10911 |
| present.max_us | 16901 | 15763 |
| game time/ticks ms | 3773 fake ticks | 6461 wall-clock ticks |
| gametic | 95 | 189 |
| sleep_calls | 3773 fake increments | 1125 real sleeps |

## Findings

1. V3092 proves the wall-clock + real `DG_SleepMs()` path is worse for smoothness in this architecture. It made helper progress obey DOOM's 35Hz wait path in wall time, which pushed pageflip average cadence close to every-other-vblank territory.
2. The earlier fake-time model is not the dominant source of the visible stutter. It is synthetic, but it also prevents the helper loop from spending real wall time inside `I_Sleep(1)` waits.
3. DOOM's 35Hz tic cadence remains a real visual limit, but V3092 made it more visible by letting game time advance according to wall time while the presenter still tries to pace through pageflip tokens.
4. The biggest regression moved into present cadence: V3092 `present.avg_us=10911` and `flip_delta_avg_us=29311`, compared with V3091 `present.avg_us=3770` and `flip_delta_avg_us=18582`.
5. Large-frame 3:2 scaling remains the next best suspect. V3092 reduced `draw.max_us`, but the end-to-end present cadence still worsened, so the next bounded experiment should remove/disable large scaling and compare a pure 1:1 DOOM path against V3091.
6. Real DOOM audio is still separate. This lineage still reports `native-audio-corun-tone-v3053`; actual DOOM SFX remains disabled by the helper argv.

## Decision

- Do not promote V3092 wall-clock sleep behavior as the playable baseline.
- Keep V3092 as evidence that naive wall-clock DOOM timing regresses this pageflip-paced helper architecture.
- Next unit: build a large-scaling-off / 1:1 DOOM-only candidate on the V3090/V3091 baseline, not on V3092.

## Validation Commands

- `python3 -m py_compile` with `PYTHONPYCACHEPREFIX=tmp/pycache-v3092`
- Focused unittest lineage: V3079/V3081/V3083/V3084/V3086/V3090/V3092
- `git diff --check`
- V3092 source build and marker check
- `native_init_flash.py --from-native --expect-version ... --expect-sha256 ... --expect-android-magic ...`
- `a90ctl --input-mode slow version`
- `a90ctl --input-mode slow status`
- `a90ctl --input-mode slow selftest verbose`
- `a90ctl --input-mode slow --hide-on-busy video demo doom status`
- `a90ctl --input-mode slow --hide-on-busy video demo doom loop 180 ...`
- `a90ctl --input-mode slow run /bin/busybox cat /tmp/a90-doomgeneric-v3092-tick-telemetry.txt`
- final `a90ctl --input-mode slow selftest verbose`

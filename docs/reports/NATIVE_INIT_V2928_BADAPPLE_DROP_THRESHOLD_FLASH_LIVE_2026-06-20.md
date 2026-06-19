# NATIVE_INIT_V2928_BADAPPLE_DROP_THRESHOLD_FLASH_LIVE_2026-06-20

## Scope

Validate the V2927 Bad Apple player sync/drop fix on live hardware after flashing
`v2927-badapple-drop-threshold`. This is still a bounded 120-frame validation,
not the full-song acceptance run.

## Artifact Under Test

- Native init: `0.10.42`
- Build tag: `v2927-badapple-drop-threshold`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2927_badapple_drop_threshold.img`
- SHA256: `34737dd605fae47a07eabdd63174ea19159cdb601648ed63fa50f2f325257ee9`
- Rollback target retained: `v2321`

## Source Delta

- Added `--sync-start-offset-ms N` for Bad Apple video sync and HUD telemetry.
- The corrected video clock anchor is now `audio_listen_begin + start_offset_ms`.
- The Bad Apple menu preview requests `--sync-start-offset-ms 450`.
- Relaxed late-frame drop threshold from half a frame to one full frame at the
  stream FPS. This avoids dropping frames that can still be presented on the next
  pageflip while keeping explicit late-frame accounting.

## Flash / Health

- Flashed via `workspace/public/src/scripts/revalidation/native_init_flash.py` only.
- Readback/post-boot verification passed.
- Resident version after flash: `A90 Linux init 0.10.42 (v2927-badapple-drop-threshold)`.
- Final selftest: `pass=12 warn=1 fail=0`.

## Live Validation

Private evidence:

- `workspace/private/runs/video/v2928-badapple-drop-threshold-final-20260620-083752/live.log`
- `workspace/private/runs/audio/v2928-chime-audibility-20260620-083534/live.log`

Bounded A/V command sequence:

1. Hide foreground menu.
2. Start `audio play internal-speaker-safe --mode listen --amplitude-milli 150 --duration-ms 4000 --pcm-file /cache/a90-runtime/pkg/av/v2920/audio/badapple.s16le --execute`.
3. Immediately start `video demo badapple play --trust-cache --frames 120 --present pageflip --layout player-hud --sync-audio-status /cache/a90-audio-play/status.txt --sync-wait-ms 10000 --sync-start-offset-ms 450`.
4. Poll audio worker after settle.
5. Run `selftest verbose`.

Key result:

| Metric | Value |
| --- | --- |
| `video.stream.presented` | `120` |
| `video.stream.frames_requested` | `120` |
| `video.stream.dropped_frames` | `0` |
| Presented ratio | `100.0%` |
| `video.stream.audio_sync.ready` | `1` |
| `video.stream.audio_sync.anchor_age_ns` | `399820625` |
| `video.stream.audio_sync.start_offset_ms` | `450` |
| `video.stream.audio_sync.initial_drop_late_ns` | `0` |
| `video.stream.audio_sync.drop_threshold_ns` | `33333333` |
| `video.stream.flip_delta_avg_us` | `33362` |
| `video.stream.flip_delta_target_us` | `33333` |
| Audio worker | `done=1 rc=0 exit_code=0` |
| Audio frames / bytes | `192000 / 768000` |
| Final selftest | `fail=0` |

Comparison:

| Run | Change | Presented / Requested | Dropped | Notes |
| --- | --- | --- | --- | --- |
| V2924 | Initial A/V menu route | `98 / 120` | `22` | Drop policy too aggressive with uncorrected start age. |
| V2925 | Start offset correction | `113 / 120` | `7` | One frame short of 95% target on 120-frame clip. |
| V2928 | Start offset + one-frame drop threshold | `120 / 120` | `0` | Bounded clip passes video presentation gate. |

## Audio Audibility Status

- The Bad Apple PCM worker completed successfully (`done=1 rc=0`, all requested
  frames and bytes written).
- A separate internal-speaker chime at the safety cap (`amplitude_milli=200`,
  `duration_ms=1500`) also completed successfully (`done=1 rc=0` after settle).
- Operator/user reported that Bad Apple video was visible but audio was not heard
  before this report was finalized. Therefore physical Bad Apple audibility is
  still an open checkpoint and the full demo acceptance is **not** closed.
- Source review found `--amplitude-milli` is a safety peak cap for PCM-file
  playback, not a software gain stage; the current Bad Apple PCM is already
  encoded at a low bounded level (peak about 17.7% of full scale, below the 20%
  cap). Increasing the command cap alone does not make the file louder.

## Decision

- `v2927-badapple-drop-threshold` fixes the bounded 120-frame video drop failure.
- Do not mark the Bad Apple demo complete: physical audio audibility/sync and the
  full-length 232 s run remain open.
- Next meaningful unit: either produce a cap-normalized Bad Apple audio asset
  within the 0.2 safety limit and retest audibility, or run a full-length
  bounded preview once the operator confirms the speaker output is physically
  audible.

# Native Init V2909 Trusted Video Cache A/V Sync Live Validation

## Summary

- Decision: `v2909-video-cache-av-sync-live-pass-before-rollback-posthoc-classifier-fix`
- Result before rollback: `1`
- Candidate: `v2908-video-cache-trust-play` / `0.10.35` / `3d0f12ce17245de8649841d44a382e11291f9e8a0b0df527ff96bdc4e1b0fc78`
- Cache SHA: `878dd867d63141eb6c9ce45a936d0454778ac91031e929b8da1c873c1c901890`
- Slice frames: `300` of `6501`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Command Results

- `video cache status`: rc=`0`, summary=`{'format_ok': True, 'frames_ok': True, 'manifest_ok': True, 'sha_ok': True, 'stream_exists': True, 'stream_size_match': True}`
- `video cache verify`: rc=`0`, summary=`{'actual_sha': True, 'expected_sha': True, 'sha_checked': True, 'sha_match': True}`
- `audio play`: rc=`0`, worker_done=`1`, pass=`1`
- `video cache play --trust-cache --sync-audio-status`: rc=`0`, pass=`1`
- Trust markers: `{'actual_not_checked': True, 'default_verify_not_repeated': True, 'sha_checked_zero': True, 'sha_match_zero': True, 'trust_cache': True}`
- Sync markers: `{'anchor_age_ns': 366829167, 'anchor_age_present': True, 'drop_policy_marker': True, 'duration_present': True, 'enabled': 1, 'enabled_ok': True, 'expected_duration_ns': 10000000000, 'first_presented_frame': 13, 'first_presented_frame_present': True, 'frame_bytes': 4, 'geometry_ok': True, 'initial_drop_late_ns': 383760104, 'initial_drop_late_present': True, 'listen_begin_ns': 187812895396, 'listen_begin_present': True, 'ready': 1, 'ready_elapsed_ms': 0, 'ready_ok': True, 'requested': 1, 'requested_ok': True, 'sample_rate': 48000, 'status_path_marker': True, 'total_frames': 480000, 'wait_ms': 90000, 'wait_ok': True}`
- Frame accounting: presented=`287` dropped=`13` accounted=`300`

## Evidence Paths

- Result JSON: `workspace/private/runs/video/v2909-video-cache-av-sync-live-20260620-015758/result.json`
- Cache status stdout: `workspace/private/runs/video/v2909-video-cache-av-sync-live-20260620-015758/11_candidate-video-cache-status.txt`
- Cache verify stdout: `workspace/private/runs/video/v2909-video-cache-av-sync-live-20260620-015758/12_candidate-video-cache-verify.txt`
- Audio execute stdout: `workspace/private/runs/video/v2909-video-cache-av-sync-live-20260620-015758/14_candidate-audio-play-execute.txt`
- Audio worker status stdout: `workspace/private/runs/video/v2909-video-cache-av-sync-live-20260620-015758/17_candidate-audio-play-status-02.txt`
- Audio worker log stdout: `workspace/private/runs/video/v2909-video-cache-av-sync-live-20260620-015758/18_candidate-audio-worker-log.txt`
- Cache play stdout: `workspace/private/runs/video/v2909-video-cache-av-sync-live-20260620-015758/15_candidate-video-cache-play-trust-audio-sync.txt`

## Interpretation

- This validates the intended fast repeat-test pattern: full cache SHA verify once, then explicit trusted cache playback for the A/V-sync slice.
- `--trust-cache` is accepted only because `video cache verify` succeeded earlier in the same run; the playback log must show `sha256_checked=0` and `trust-cache-not-checked`.
- Video remains the existing KMS dumb-buffer/page-flip path; audio remains the bounded internal-speaker-safe route.

## Classifier Note

- Posthoc classifier fix applied: `1`
- Reason: `initial runner over-gated cache wrapper markers and PCM-file-only audio markers`
- Cache/audio pass after fix: `1` / `1`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Persistent write scope: boot partition only; runtime audio/video files remain temporary/private.
- No Venus/GPU/raw DSI/panel init/backlight/PMIC/PWM/regulator/GPIO/GDSC path was used.
- Rollback target: `v2321-usb-clean-identity-rodata`.

# Native Init V2975 Nyan Real Preview Live Validation

## Summary

- Decision: `v2975-nyan-real-preview-live-pass-rollback-ok`
- Result before rollback: `1`
- Candidate: `v2974-nyan-real-preset` / `0.10.59` / `e6ac9bc08829c465e2126654b1f7020eab5e5cfb8491e7fc9d9a297e3b514410`
- Video SHA256: `9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573`
- Audio SHA256: `4c3774553195c04166a3a83de793253696a5bee60afe83a04219419fc28e43de`
- Slice: `300` frames / `10000` ms audio
- Present path: `setcrtc` / `player-hud`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Runtime Assets

- Video cache dir: `/mnt/sdext/a90/runtime/video/cache/sha256-9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573`
- Video cache source: `uploaded`
- Video cache hit before upload: `0`
- Video cache uploaded: `1`
- Stream size bytes: `6559098`
- Compression ratio milli: `112`
- Audio remote PCM: `/cache/a90-runtime/pkg/av/v2973/audio/nyancat.s16le`
- Audio cache hit before upload: `0`
- Audio uploaded: `1`
- Audio remote SHA matched: `1`
- Audio transfer: `tcpctl` control=`tcpctl`

## Command Results

- `video demo nyan status`: rc=`0` summary=`{'format_ok': True, 'frames_ok': True, 'manifest_ok': True, 'sha_ok': True, 'size_ok': True, 'stream_exists': True, 'stream_size_match': True, 'v2_size_sentinel': True}`
- `video demo nyan verify`: rc=`0` summary=`{'actual_sha': True, 'expected_sha': True, 'sha_checked': True, 'sha_match': True}`
- `audio play --pcm-file`: rc=`0` worker_done=`1` pass=`1`
- `video demo nyan play --trust-cache --layout player-hud --present setcrtc`: rc=`0` pass=`1`
- Frame accounting: presented=`300` dropped=`0` accounted=`300` fps_milli=`30093` elapsed_ns=`9968905569`
- Setcrtc markers: flip_events=`0` path_ok=`1` pixel_format=`1`
- Sync markers: `{'drop_policy_none': True, 'duration_present': True, 'enabled': 1, 'enabled_ok': True, 'frame_bytes': 4, 'geometry_ok': True, 'listen_begin_ns': 179492538577, 'listen_begin_present': True, 'ready': 1, 'ready_ok': True, 'requested': 1, 'requested_ok': True, 'sample_rate': 48000, 'start_offset_ms': 450, 'start_offset_ok': True, 'status_path_marker': True, 'total_frames': 480000, 'wait_ms': 60000, 'wait_ok': True}`

## Classifier Note

- Posthoc classifier fix applied: `1`
- Reason: `original V2975 classifier reused older pcm_output_pass expectations that require worker_pcm_file/integrated_pcm_file booleans; actual native output exposes pcm_file path plus source/validation markers`
- Cache/audio pass after fix: `1` / `1`

## Safety

- Only the boot partition was flashed, through `native_init_flash.py`; rollback target remained `v2321`.
- Raw Nyan stream/audio and run logs remained private and untracked.
- No Venus, GPU, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
- Audio was bounded to 10 seconds and amplitude-milli 150.

## Evidence

- Result JSON: `workspace/private/runs/video/v2975-nyan-real-preview-live-20260620-135253/result.json`
- Output dir: `workspace/private/runs/video/v2975-nyan-real-preview-live-20260620-135253`

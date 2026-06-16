# NATIVE_INIT V2574 — ACDB per-device indirect live handoff

Date: 2026-06-16

## Scope

Android own-process ACDB capture handoff using the checked V2490 Android boot/stage/pull/rollback engine plus the V2572 per-device helper/preload artifacts. Common topology is intentionally skipped because V2547 already pinned the 4916-byte topology payload.

Boundaries held: measurement-only, raw ACDB buffers private, fake audio-cal allocate policy enabled, no real `AUDIO_SET_CALIBRATION` pass-through, no native speaker write, and rollback to V2321.

## Result

- decision: `v2573-send-audio-cal-v5-no-per-device-records-rollback-pass`
- V2490 engine decision: `v2490-helper-timeout-acdbtap-call-events-no-return-before-rollback-rollback-pass`
- V2573 classifier ok: `False`
- V2490 recoverability ok: `True`
- rolled_back: `True`
- out_dir: `workspace/private/runs/audio/v2574-acdb-perdevice-indirect-capture-20260616-125616`
- final device health: V2321 resident, `selftest fail=0`

## Evidence

- `skip_real_common_topology_seen=True`
- `patch_initialized_flag_ok=True`
- `send_audio_cal_v5_reached=True`
- `topology_success_count=0`
- `per_device_success_count=0`
- `successful_nonzero_count=0`
- `real_audio_set_pass_through_count=0`
- fake `AUDIO_ALLOCATE_CALIBRATION` intercepts: `25`, all `ret=0`, covering cal types including `11`, `12`, `15`, `16`, and `39`
- `acdbtap` call events: `1`; return events/raw buffers: `0`
- helper timeout: `ownget-run-helper timed out after 120.0s`

The only armed `acdb_ioctl` call captured was `cmd=0x00000000`, `in_len=0`, `out_len=0`, with no matching return event. The V2572 preinit hook reached `before_send_audio_cal_v5`, then no per-device GET returned. This points away from Android/rollback/SELinux and toward the V2572 `send_audio_cal_v5` call-site/prototype/RE path.

## Interpretation

V2574 is a safe failed capture, not a payload capture. It proves the fake-allocate init path is viable and that the preinit hook reaches the intended per-device call boundary, but the current `send_audio_cal_v5` invocation does not generate valid per-device `acdb_ioctl` GET records.

Next unit should be host-only: re-verify the exact `acdb_loader_send_audio_cal_v5` prototype/calling convention and exported symbol target, then rebuild before any rerun. Do not blind-rerun the same V2572 helper.

## Private Artifacts

- helper sha256: `5cc7b9c6f2bacdb7c4789bb9f9f62ec2f2ec7488e9124e97b0364b3644af023d`
- preload sha256: `08046bcb104a9da948a8d05bba7d0126d07f35de30a9978231d445153189a7d4`
- result JSON: `workspace/private/runs/audio/v2574-acdb-perdevice-indirect-capture-20260616-125616/v2573-result.json`
- engine JSON: `workspace/private/runs/audio/v2574-acdb-perdevice-indirect-capture-20260616-125616/result.json`

Raw payload/log artifacts remain private and are not committed.

# NATIVE_INIT_V2389_AUD4_PCM_PROBE_PREPARE_EINVAL_2026-06-15

## Scope

Exact-gated AUD-4 live retry using:

- V2388 ADSP accepted-output recovery;
- V2386 diagnostic PCM write probe;
- same V2377 observed route apply/reset plan;
- same generated 48 kHz stereo S16_LE 0.02-amplitude 1 s WAV;
- V2321 rollback.

Approval phrase used:

```text
AUD-4-native-speaker-pilot go: one-shot V2377 observed route apply, low-amplitude tinyplay, reverse reset, rollback to V2321
```

## Private evidence

```text
workspace/private/runs/audio/v2379-native-speaker-pilot-20260615-055058/
```

## Result summary

The run reached the intended V2386 diagnostic point.

- ADSP boot: accepted, protocol OK.
- `/dev/snd` materialization: completed before route/probe.
- Route apply: 13/13 commands OK.
- Playback probe: failed with `A90_PCM_PROBE_WRITE_ERROR`.
- Route reset: 12/12 commands OK.
- Reset verification: OK, no mismatches.
- Rollback: V2321, `rollback_version_ok=True`, `rollback_selftest_fail0=True`.
- Final device health after run: V2321 `0.9.285`, `selftest fail=0`.

## ADSP boot classification

`result.adsp_boot_once`:

```json
{
  "decision": "accepted-protocol-ok",
  "accepted": true,
  "accepted_marker": true,
  "end_marker": true,
  "protocol_ok": true,
  "failure_markers": []
}
```

This confirms the V2388 recovery patch did not regress normal protocol-OK ADSP boot handling.

## Probe output

Playback step output:

```text
a90_tcpctl v1 ready
OK authenticated
[pid 690]
A90_PCM_PROBE_START version=V2386 card=0 device=0 channels=2 rate=48000 bits=16 data_bytes=192000 period_size=1024 period_count=4
A90_PCM_PROBE_PCM_OPEN_OK buffer_frames=4096 buffer_bytes=16384
A90_PCM_PROBE_WRITE_ERROR chunk=0 rc=-1 errno=22 strerror="Invalid argument" pcm_error="cannot prepare channel: Invalid argument" bytes=16384 frames=4096
[exit 40]
ERR exit=40
```

The probe succeeded at:

- WAV parse;
- `pcm_open(card=0, device=0, PCM_OUT, config)`;
- tinyalsa hw params / sw params path inside `pcm_open()`;
- status mmap enough for `pcm_get_buffer_size()` to report `4096` frames.

The probe failed before first `SNDRV_PCM_IOCTL_WRITEI_FRAMES`. Tinyalsa source path:

- `pcm_write()` calls `pcm_prepare()` when `pcm->running == 0` at `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/pcm.c:548`.
- `pcm_prepare()` issues `SNDRV_PCM_IOCTL_PREPARE` at `workspace/private/inputs/external_tools/audio/tinyalsa/e14bf1479ebaaabf60bc4472ce8d304f72f03c32/src/pcm.c:1082`.
- That ioctl failed with `EINVAL`, recorded by tinyalsa as `cannot prepare channel: Invalid argument`.

## Classification

This is no longer a transport, route syntax, bool encoding, `tinyplay` rc, ADSP boot, or `/dev/snd` materialization issue.

Current blocker:

```text
SNDRV_PCM_IOCTL_PREPARE returns EINVAL for card0/device0 after successful open/hw/sw params and after the V2377 observed speaker route is applied.
```

This means the next step should classify the kernel/driver reason for prepare failure before any tuning.

## Next unit

Host-only design first, then a bounded live retry only if needed:

1. Add kmsg capture around route apply + PCM prepare, or extend the probe to snapshot the exact PCM config and optionally issue a prepare-only diagnostic.
2. Keep route controls unchanged until the driver-side `EINVAL` reason is visible.
3. Do not change period size/count, card/device, sample rate, channel count, or amplitude yet.

Potential V2390 target: prepare-focused diagnostic capture for `SNDRV_PCM_IOCTL_PREPARE` failure, including continuous `/dev/kmsg` during the route/probe window if available under native init.

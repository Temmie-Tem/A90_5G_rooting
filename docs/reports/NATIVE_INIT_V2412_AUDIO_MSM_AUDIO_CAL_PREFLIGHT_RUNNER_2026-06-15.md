# V2412 — AUD-5C msm_audio_cal preflight runner dry-run

Scope: host-only implementation unit after V2411. No flash, Android boot, ADSP action, `/dev/msm_audio_cal` open, audio ioctl, mixer write, Magisk action, or playback ran in this unit.

## Decision

`v2412-msm-audio-cal-preflight-gate-dry-run`

V2412 turns the V2411 `/dev/msm_audio_cal` N2 design into a source-controlled dry-run planner:

```text
workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py
```

The script emits the future exact-gated AUD-5C sequence while keeping this unit host-only. `--run-live` is wired to the exact phrase but intentionally returns a source-only placeholder, so the first real open-only live run remains a separate bounded V-iteration after review/commit.

## Dry-run result

Command:

```bash
python3 workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py --dry-run
```

Summary:

```json
{
  "decision": "v2412-msm-audio-cal-preflight-gate-dry-run",
  "ok": true,
  "device_action": "none",
  "safety_ok": true,
  "commands": [
    "msm-audio-cal-inventory-before-materialize",
    "msm-audio-cal-materialize-if-needed",
    "msm-audio-cal-open-only",
    "msm-audio-cal-inventory-after-open",
    "msm-audio-cal-dmesg-tail",
    "msm-audio-cal-cleanup"
  ]
}
```

The future exact phrase is carried forward from V2411:

```text
AUD-5C-msm-audio-cal-preflight go: one-shot /dev/msm_audio_cal existence/open-only inventory on V2334, no AUDIO_SET ioctls, no ACDB payload, no playback, rollback to V2321
```

## Planned future live sequence

The source-only plan composes:

1. Verify resident V2321 and `selftest fail=0`.
2. Flash V2334 audio snd-nodes candidate through the checked helper.
3. Verify candidate version/status/selftest.
4. Run the already validated token-gated ADSP + `/dev/snd` materialization path.
5. Inventory `/proc/misc` and `/dev/msm_audio_cal`.
6. Materialize a runtime misc node from `/proc/misc` only if devtmpfs did not create it.
7. Perform one open/close-only probe: `O_RDONLY` first, then one `O_RDWR` fallback only if read-only open fails.
8. Capture bounded dmesg tail.
9. Roll back to V2321 and require `selftest fail=0`.

V2412 does **not** run that sequence. It only makes the plan inspectable and test-covered.

## Safety contract encoded in the runner

Allowed future runtime mutations:

- temporary `/dev/msm_audio_cal` `mknod c 10 <minor>` based on `/proc/misc`;
- `chmod 0600` on that runtime devnode;
- one open/close-only probe when enabled.

Forbidden by command safety tests:

- `AUDIO_ALLOCATE_CALIBRATION`, `AUDIO_DEALLOCATE_CALIBRATION`, `AUDIO_PREPARE_CALIBRATION`, `AUDIO_SET_CALIBRATION`, `AUDIO_GET_CALIBRATION`, `AUDIO_POST_CALIBRATION`;
- RTAC calibration ioctls;
- any literal `ioctl` use in planned shell commands;
- `tinymix`, `tinypcminfo`, `tinyplay`, PCM write/playback markers;
- Android/Magisk execution (`su -c`, `app_process`, `am start`, `magisk --install-module`);
- block/forbidden partition tokens.

The planned commands mark `uses_audio_ioctl=false`, `uses_acdb_payload=false`, and `uses_playback=false`. This is still only metadata; the real guard is the argv token scan plus focused tests.

## Magisk-module direction

V2412 keeps the V2411 boundary:

- **M0 transient helper remains default** for Android-good measurement if another Android capture is needed.
- **M1 temporary boot module is reserved only** if M0 misses early `/dev/msm_audio_cal` ioctl payloads.
- **No Magisk artifact is a native-init runtime dependency.** V2412 does not call Magisk, Android framework playback, ADB, or any Android handoff.

This preserves the Wi-Fi-style pattern: use Android/Magisk to learn missing vendor behavior when necessary, then port only bounded, source-reviewed facts into native init.

## Validation

Commands run:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py \
  tests/test_native_audio_msm_audio_cal_preflight_gate_v2412.py
python3 -m unittest discover -s tests -p 'test_native_audio_msm_audio_cal_preflight_gate_v2412.py'
python3 workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py --dry-run
```

Focused test result:

```text
Ran 8 tests in 0.666s
OK
```

Full suite and whitespace validation are recorded in the commit context for this unit.

## Next unit

V2413 can run the first exact-gated live AUD-5C preflight if the device/bridge state is healthy. The only allowed live outcome target is `msm_audio_cal` reachability/open-only classification. Do not send calibration ioctls or ACDB payloads in V2413.

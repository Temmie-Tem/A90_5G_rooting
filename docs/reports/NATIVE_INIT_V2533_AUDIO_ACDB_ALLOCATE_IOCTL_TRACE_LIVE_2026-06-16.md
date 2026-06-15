# NATIVE_INIT_V2533_AUDIO_ACDB_ALLOCATE_IOCTL_TRACE_LIVE_2026-06-16

## Scope

V2533 fixed the V2532 Android post-handoff staging race and reran the own-process ACDB GET helper with the V2531 `ioctl()` trace preload enabled.

The target was narrow: capture the exact `/dev/msm_audio_cal` `AUDIO_ALLOCATE_CALIBRATION` ioctl return/errno and AVC context around `acdb_loader_init_v3`. This remained measurement-only.

## Safety Boundary

- No native ACDB replay was attempted.
- No `/dev/msm_audio_cal` SET ioctl was issued.
- No HAL injection, HAL restart, AudioTrack stimulus, or speaker route write was used.
- The own-process helper ran once under Android Magisk `su`.
- Rollback to V2321 completed through the checked helper.
- Final native V2321 health check: `selftest fail=0`.

## Code Change

The V2490 runner now wraps only the early Android staging phase with bounded ADB transport retry:

- covered: `ownget-setup`, helper/preload/dependency pushes, chmod, execution-context probe, and logcat clear;
- trigger: transport-only failures such as `error: closed`, `no devices/emulators found`, `device offline`, `failed to get feature set`, or `protocol fault`;
- recovery: `adb wait-for-device`, boot-complete recheck, and `su -c id` before retry;
- semantic failures still fail closed;
- `ownget-run-helper` remains one-shot and is not retried after execution starts.

V2533 did not need the retry on this run; all early staging steps succeeded on attempt 1.

## Private Evidence

- Run directory: `workspace/private/runs/audio/v2533-acdb-allocate-ioctl-trace-20260616-055714/`
- Pulled artifact directory: `workspace/private/runs/audio/v2533-acdb-allocate-ioctl-trace-20260616-055714/ownget-device-artifacts/`
- Private trace SHA256:
  - `ioctl-trace-events.jsonl`: `5b63d36c35de946180ebaafdf7ac79dafc081db6369fd702160ce64b4187c4b4`
  - `acdb-ownget-events.jsonl`: `dc254e85ccf11db0fec124e7da7628f63c4b61274a60ec93dc2d0480a9fa71e6`
  - `logcat-acdb-loader.txt`: `f36fc5a0ca0c43abbf079d6b0c208d8e0036786fb159bac9671e8fc253ed8960`

Raw output buffers remain private and are not committed.

## Live Result

Runner decision:

```text
v2490-acdb-get-dispatch-ret-failed-zero-outbuf-before-rollback-rollback-pass
```

Summary:

| Field | Value |
| --- | --- |
| `row_count` | `40` |
| `target_4916_count` | `20` |
| successful ACDB GET rows | `0` |
| `ret` values from GET rows | `[-2]` |
| zero output buffers | `40` |
| `SHA256(4 x 0x00)` | `df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119` |
| `SHA256(4916 x 0x00)` | `9af4895ee511379e7a2d0620ea158c535f88c853de6df2eb2cd32f0cb4a2cb8c` |
| `operator_valuable` | `true` |

The zero-buffer false-positive discriminator is working: no `ret==0` and non-zero `out_len==4916` payload was captured.

## Allocate Ioctl Evidence

The V2531 preload captured exactly one `AUDIO_ALLOCATE_CALIBRATION` ioctl and one cleanup deallocate:

```json
{"event":"ioctl_trace","pid":4149,"tid":4149,"fd":6,"request":"0xc00461c8","name":"AUDIO_ALLOCATE_CALIBRATION","arg":"0xff95cae8","ret":-1,"errno":22}
{"event":"ioctl_trace","pid":4149,"tid":4149,"fd":6,"request":"0xc00461c9","name":"AUDIO_DEALLOCATE_CALIBRATION","arg":"0xff95b508","ret":0,"errno":0}
```

There were no `AUDIO_SET_CALIBRATION` ioctl records:

```text
audio_set_ioctl_count=0
```

The exact errno is therefore:

```text
AUDIO_ALLOCATE_CALIBRATION -> ret=-1 errno=22 (EINVAL)
```

## AVC / Denial Evidence

The captured filters contain generic Android boot denials, but no relevant `avc` / `denied` line for the helper PID, `magisk`, `/dev/msm_audio_cal`, `audio_device`, ACDB, or the allocate ioctl path.

Targeted grep over `dmesg-avc-acdb-filter.txt`, `logcat-avc-acdb-filter.txt`, and `logcat-acdb-loader.txt` for:

```text
4149|ACDB|AUDIO_ALLOCATE|msm_audio_cal|audio_device|magisk|ioctl|avc:.*(audio|msm|magisk|4149)|denied.*(audio|msm|magisk|4149)
```

returned no relevant AVC/denial lines from dmesg and only ACDB loader/helper application logs from logcat.

Relevant ACDB loader lines:

```text
06-16 05:58:47.738  4149  4149 E ACDB-LOADER: ACDB -> Error: Sending AUDIO_ALLOCATE_CALIBRATION, result = -1
06-16 05:58:47.738  4149  4149 E ACDB-LOADER: ACDB -> allocate_cal_block failed!
06-16 05:58:47.738  4149  4149 E ACDB-LOADER: ACDB -> Cannot allocate memory!
```

The loader's `Cannot allocate memory!` log is generic at this layer; the traced syscall-level errno is `EINVAL`, not `ENOMEM`.

## Interpretation

V2533 rules down the prime SELinux-ioctl-filter hypothesis for this own-process run: open and ioctl dispatch reached the kernel, and the observed failing ioctl returned `EINVAL` without a relevant AVC.

The current blocker is kernel-side argument/state rejection of `AUDIO_ALLOCATE_CALIBRATION`, not ACDB GET command selection. Because `acdb_loader_init_v3` fails at allocation, the ACDB engine stays uninitialized and every subsequent GET returns `ret=-2` with untouched zero buffers.

The next design step should focus on the allocate request geometry/state rather than replay or GET:

1. Decode the `AUDIO_ALLOCATE_CALIBRATION` argument struct passed at `0xff95cae8` from libaudcal / kernel headers and compare against the kernel's expected msm audio calibration ABI.
2. Determine whether the rejection is caused by the ION heap/fd/mem-handle shape, missing audio-cal kernel state, or conflict with an already-held live Android audioserver allocation.
3. Keep native replay blocked until allocate succeeds and the allocation/deallocate ownership policy is pinned.

## Validation

Static validation before the live run:

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py
PYTHONPATH=tests python3 -m unittest tests.test_native_audio_acdb_ownprocess_get_live_handoff_v2490
PYTHONPATH=tests python3 -m unittest tests.test_build_android_ioctl_trace_preload_v2531 tests.test_native_audio_acdb_ownprocess_get_live_handoff_v2490
```

Result:

```text
28 tests OK
```

Post-rollback native checks:

```text
version: 0.9.285 build=v2321-usb-clean-identity-rodata
selftest: pass=11 warn=1 fail=0
```

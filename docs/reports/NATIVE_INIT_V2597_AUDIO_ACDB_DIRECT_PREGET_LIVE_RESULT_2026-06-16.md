# NATIVE_INIT V2597 — ACDB direct pre-GET live result

Date: 2026-06-16

## Scope

Live Android-good own-process ACDB direct metadata probe using the V2596 runner and V2595
helper/preload artifacts. The probe bypassed real common-topology execution, patched the
initialized flag for the short metadata call, issued exactly the first `send_audio_cal_v5`
dispatcher GET geometry, and exited before the loader init tail.

This was a measurement-only run:

- no native speaker write;
- no raw ACDB payload committed;
- no real `AUDIO_SET_CALIBRATION` pass-through; and
- checked rollback to V2321 after artifact pull.

## Result

- decision: `v2596-direct-preget-ret0-nonzero-rollback-pass`
- ok: `True`
- run_dir: `workspace/private/runs/audio/v2597-acdb-direct-preget-20260616-163648`
- direct classification: `v2596-direct-preget-ret0-nonzero`
- `acdb_ioctl` command: `0x0001122e`
- input word: `0x00011135`
- `in_len`: `4`
- `out_len`: `4`
- `ret`: `0`
- output word: `0x10005000`
- output nonzero: `True`

## Artifact Identity

- helper SHA256: `5cc7b9c6f2bacdb7c4789bb9f9f62ec2f2ec7488e9124e97b0364b3644af023d`
- preload SHA256: `7019b5d44fa6d8bedd9065f42368354f67e5c57d97b863ec62a456cd307c255a`

The artifacts were staged privately under the Android-good handoff run directory and were not
committed.

## Observed Helper Stages

The pulled private event stream contained six ordered helper stages:

1. `entered_common_topology_hook`
2. `skip_real_common_topology`
3. `patch_initialized_flag_return`
4. `before_direct_preget`
5. `direct_preget_return`
6. `exit_before_init_tail`

The direct pre-GET row was present at `direct_preget_return` with `ret==0` and a nonzero
4-byte output word.

## Safety Counters

- fake `AUDIO_ALLOCATE_CALIBRATION`: `25`
- fake `AUDIO_DEALLOCATE_CALIBRATION`: `0`
- fake `AUDIO_SET_CALIBRATION`: `0`
- real `AUDIO_SET_CALIBRATION` pass-through: `0`
- raw ACDB payload files committed: `0`

The run produced no full topology/per-device payload; this unit only proved the direct
metadata GET geometry can return a valid nonzero 4-byte value after the V2595 short-circuit.

## Rollback

- Android handoff completed.
- Private artifacts were pulled.
- Temporary Android paths were cleaned.
- V2321 rollback image SHA was verified by the checked flash helper.
- Final native-init rollback version: `0.9.285 (v2321-usb-clean-identity-rodata)`.
- Final rollback selftest: `fail=0`.

## Interpretation

V2597 confirms that the first `send_audio_cal_v5` pre-GET geometry pinned in V2594 is live
under Android-good when executed after ACDB initialization/fake allocation setup:

```text
acdb_ioctl(0x1122e, &0x11135, 4, out, 4) -> ret=0, out=0x10005000
```

This is not a payload capture. It is a useful live discriminator showing that the ACDB engine
can return nonzero metadata for the first per-device dispatcher path when the helper avoids the
previous init-tail crash window.

## Next Unit

Implement the operator handover for a post-init armed `acdb_ioctl` capture:

- keep the combined preload and fake allocation;
- do no dump/file IO while unarmed during init;
- arm immediately after `acdb_loader_init_v3` returns;
- call the real `acdb_loader_send_common_custom_topology()`;
- while armed, dump `out_len>0` records; and
- on the first `ret==0`, non-all-zero `out_len==4916` record, flush and `_exit(0)` before
  downstream SET/crash-prone code.


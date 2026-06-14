# Native Init V2335 Audio `/dev/snd` Nodes Preflight Runner Source

## Summary

- Cycle: `V2335`
- Track: audio AUD-3 preflight runner, source-only.
- Decision: `v2335-audio-snd-nodes-preflight-runner-source-pass`
- Result: PASS
- Device flash: `no`.
- Device action: `none`.
- Script: `workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py`
- Candidate artifact: `workspace/private/inputs/boot_images/boot_linux_v2334_audio_snd_nodes_preflight.img`
- Candidate SHA256: `53b1130cd912ca4019a3d76835eb721804bae0460b920eb7fdfad5509a2dfcac`
- Rollback target: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`

## Scope

V2335 does not run the live AUD-3 preflight. It prepares the exact live handoff script for the next operator-gated unit.

The script refuses live execution unless `--run-live` is paired with this exact approval phrase:

```text
AUD-3-preflight go: materialize ALSA /dev/snd nodes only on V2334, no open/ioctl/mixer/playback, rollback to V2321
```

## Implemented Live Flow

If later approved, the runner performs this bounded sequence:

1. Verify the V2334 candidate, V2321 rollback, V2237 fallback, and V48 fallback exist and match the pinned hashes where applicable.
2. Verify the currently resident V2321 checkpoint through `native_init_flash.py --verify-only` and `selftest verbose`.
3. Flash only the V2334 boot image through `native_init_flash.py --expect-sha256 ... --from-native`.
4. Confirm V2334 `version`, `status`, and `selftest verbose` with `fail=0`.
5. Run `audio adsp-status` and `audio snd-status` before mutation.
6. If the ALSA card/control evidence is not already present, run exactly one `audio adsp-boot-once AUD2_ONE_SHOT_ADSP_BOOT` using `--hide-on-busy`.
7. Poll `audio adsp-status` and `audio snd-status` until `sm8150-tavil-snd-card` plus sound-class control evidence appears, bounded by timeout.
8. Run `audio snd-status` before materialization.
9. Run exactly one `audio snd-materialize-once AUD3_DEV_SND_MATERIALIZE_ONLY`.
10. Run `audio snd-status` after materialization and require a `/dev/snd/controlC*` result.
11. Confirm candidate `selftest verbose` remains `fail=0`.
12. Always attempt rollback to V2321 after candidate flash, then confirm V2321 version and `selftest fail=0`.

## Safety Boundary

The runner explicitly keeps this unit below playback:

- No ALSA node open or ioctl.
- No mixer, `tinymix`, tinyalsa, `tinyplay`, PCM payload, or audio HAL.
- No `adsprpc` invoke/ioctl.
- No `/dev/subsys_adsp` open.
- One `audio snd-materialize-once` command maximum.
- All private evidence goes under `workspace/private/runs/audio/v2335-snd-nodes-preflight-*`.
- No live action occurs in `--dry-run` mode.

## Dry-run Result

`--dry-run` validated local artifacts and produced the intended command plan:

```text
ok: true
candidate sha256_ok: true
rollback sha256_ok: true
fallback_v2237 sha256_ok: true
fallback_v48 exists: true
```

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py`: PASS.
- `python3 workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py --dry-run`: PASS.
- Live refusal guard: PASS (`--run-live` without exact `--approval` exits before bridge/flash).
- `python3 -m unittest discover -s tests -p 'test_*.py'`: PASS (`996` tests).
- `git diff --check`: PASS.

## Next Step

The next live unit is V2336 or an explicitly named live execution of this V2335 runner, but only after the exact `AUD-3-preflight` approval phrase. The previously given AUD-2 approval is not sufficient for this materialization step.

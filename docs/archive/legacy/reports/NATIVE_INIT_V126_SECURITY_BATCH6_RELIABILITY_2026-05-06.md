# A90 Native Init v126 Security Batch 6 Reliability

Date: 2026-05-06
Build: `A90 Linux init 0.9.26 (v126)`
Marker: `0.9.26 v126 SECURITY BATCH6`

## Summary

v126 completes Security Batch 6 historical reproducibility and retained-source
reliability cleanup. The latest runtime now rejects non-`event[0-9]+` input event
names, retained v88/v89 source snapshots regain HUD metrics compatibility,
retained v84 changelog routing renders the v84 detail screen, and retained v42
`run`/`runandroid` no longer gives child processes the same stdin that the parent
uses for q/Ctrl-C cancellation.

## Changes

- Added strict input event validation for latest v126 `inputinfo`, `inputcaps`, and `readinput` command paths.
- Added the same strict validation to retained historical `init_v10.c` input helpers.
- Added `a90_hud_*` metrics compatibility wrappers in `a90_hud.h` so retained v88/v89 source snapshots compile against the current shared headers.
- Fixed retained v84 changelog routing by including `SCREEN_APP_CHANGELOG_0815` in About draw and auto-HUD active app dispatch.
- Fixed retained v42 child stdio setup so `run`/`runandroid` children receive `/dev/null` stdin while stdout/stderr stay on the console.
- Updated `native_soak_validate.py` default expected version to v126.

## Finding Coverage

| finding | result |
|---|---|
| F026 | Mitigated: v88/v89 retained source object builds compile with HUD metrics compatibility wrappers. |
| F027 | Mitigated: v84 changelog detail route includes the v84 `0815` app id. |
| F028 | Mitigated: v42 retained source no longer gives child stdin to the same console stream polled by the parent cancel loop. |
| F029 | Mitigated: latest v126 and retained v10 input helpers reject traversal/non-numeric event names. |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v126` | `516588bd944a0ddb5804f5475b8f3755e405bf07cf4b513a41d83503dee0b57c` |
| `stage3/ramdisk_v126.cpio` | `d55b162fbd2912e8ce3fa297b57dff085334ae2db92eb0ecc3db6a4e678df689` |
| `stage3/boot_linux_v126.img` | `0ef8c9f1dc59f8ecbd394f38c6ff644a36a3dabf43daf1ef0e2df551546cede9` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.26 (v126)`, `A90v126`, and `0.9.26 v126 SECURITY BATCH6` — PASS.
- host Python `py_compile` for control/diagnostic scripts and `mkbootimg/gki/certify_bootimg.py` — PASS.
- shell syntax checks for archived legacy scripts and revalidation shell scripts — PASS.
- retained v88/v89 object compile checks — PASS with pre-existing switch warnings only.
- Batch 5 safe tar/zip traversal/link checks re-run — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v126.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.26 (v126)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.

### Runtime Checks

- `inputinfo event/../../owned` — PASS, rejected with `rc=-22 errno=22`.
- `inputcaps event/../../owned` — PASS, rejected with `rc=-22 errno=22`.
- `readinput event/../../owned 1` after `hide` — PASS, rejected with `rc=-22 errno=22`.
- `inputinfo event0` — PASS, normal event node path still works.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0`.
- `status` — PASS, reports `A90 Linux init 0.9.26 (v126)`.
- `hudlog status` — PASS, remains off by default.

## Notes

- Batch 6 intentionally fixes retained historical source snapshots without making them the latest supported boot target.
- Latest verified runtime is now v126; local artifact retention should keep v126 latest, v125 rollback, and v48 known-good.

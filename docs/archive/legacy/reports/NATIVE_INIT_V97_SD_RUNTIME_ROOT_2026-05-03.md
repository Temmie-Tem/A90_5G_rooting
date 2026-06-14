# Native Init v97 SD Runtime Root Report

Date: `2026-05-03`

## Summary

- Version: `A90 Linux init 0.8.28 (v97)` / `0.8.28 v97 SD RUNTIME ROOT`
- Goal: promote the verified SD workspace `/mnt/sdext/a90` into the primary native runtime root.
- Result: PASS on local build, boot image generation, flash, `cmdv1 version/status`, runtime, selftest, storage, HUD/menu, and netservice status regression.
- User-facing feature changes: `runtime` command and runtime root health in `status`, `bootstatus`, HUD storage line, and selftest.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v97` | `f0868caa0f6b4b2bbc086870facb93f72ac3983b064dc43991871d678e445c78` |
| `stage3/ramdisk_v97.cpio` | `9bc749822729f29a6653d5d3b6eb60fcba0038ccb7162c359bada046bdff0473` |
| `stage3/boot_linux_v97.img` | `e170ec5b3d3eed6ddeb753471feac077b8afa57e450ee4ea37df5219ba28bd5b` |

## Changes

- Copied v96 source layout to `stage3/linux_init/init_v97.c` and `stage3/linux_init/v97/*.inc.c`.
- Updated version/build markers to `0.8.28` / `v97` and boot marker strings to `A90v97`.
- Added `a90_runtime.c/h` for runtime root selection, directory contracts, RW probes, shell output, logs, and timeline records.
- Promoted healthy SD storage to runtime root:
  - root: `/mnt/sdext/a90`
  - subdirs: `bin`, `etc`, `logs`, `tmp`, `state`, `pkg`, `run`
  - fallback: `/cache/a90-runtime`
- Added `runtime` shell command.
- Added runtime root summary to `status` and `bootstatus`.
- Added runtime selftest entry while keeping the selftest policy non-destructive and warn-only.
- Routed HUD storage status through runtime status when runtime is initialized.
- Added ABOUT/changelog/menu entry for `0.8.28 v97 SD RUNTIME ROOT`.

## Local Validation

- Static ARM64 build with `-Wall -Wextra`: PASS
- `stage3/ramdisk_v97.cpio` generated with:
  - `/init`
  - `/bin/a90sleep`
  - `/bin/a90_cpustress`
- `stage3/boot_linux_v97.img` generated from v96 boot image args with ramdisk swapped.
- Marker strings present:
  - `A90 Linux init 0.8.28 (v97)`
  - `A90v97`
  - `0.8.28 v97 SD RUNTIME ROOT`
- `git diff --check`: PASS
- Host Python compile: PASS

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v97.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.28 (v97)" \
  --verify-protocol auto
```

Result:

- local image marker: PASS
- local image sha256: `e170ec5b3d3eed6ddeb753471feac077b8afa57e450ee4ea37df5219ba28bd5b`
- remote pushed image sha256: `e170ec5b3d3eed6ddeb753471feac077b8afa57e450ee4ea37df5219ba28bd5b`
- boot partition prefix sha256: `e170ec5b3d3eed6ddeb753471feac077b8afa57e450ee4ea37df5219ba28bd5b`
- post-boot `cmdv1 version/status`: PASS

Regression:

| command | result |
|---|---|
| `version` | PASS, `A90 Linux init 0.8.28 (v97)` |
| `status` | PASS, runtime `backend=sd root=/mnt/sdext/a90 fallback=no writable=yes` |
| `bootstatus` | PASS, `BOOT OK shell 4.1s` and runtime summary |
| `runtime` | PASS, all runtime directories under `/mnt/sdext/a90` reported |
| `selftest verbose` | PASS, `pass=9 warn=0 fail=0` |
| `storage` | PASS, SD backend `/mnt/sdext/a90`, fallback `no` |
| `mountsd status` | PASS, SD mounted rw, UUID match |
| `statushud` | PASS, framebuffer presented |
| `autohud 2` | PASS |
| `screenmenu` | PASS, nonblocking show request |
| `hide` | PASS |
| `netservice status` | PASS, disabled |

## Acceptance

- SD runtime root is selected on known-good SD and visible from shell/status/HUD/selftest.
- Cache runtime fallback remains available for unsafe or missing SD.
- Boot selftest remains known-good with `fail=0`.
- No BusyBox deployment, remote shell, Wi-Fi, or package manager behavior was added.
- v98 can start from a formal runtime root contract and focus on helper deployment/package manifest.

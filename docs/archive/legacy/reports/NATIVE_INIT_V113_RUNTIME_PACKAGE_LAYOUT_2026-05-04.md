# Native Init v113 Runtime Package Layout

Date: `2026-05-04`
Build: `A90 Linux init 0.9.13 (v113)`
Marker: `0.9.13 v113 RUNTIME PACKAGE LAYOUT`
Baseline: `A90 Linux init 0.9.12 (v112)`

## Summary

v113 makes the SD runtime root more package-friendly without destructive migration.
It extends the runtime status model and `runtime` command output with package, manifest, helper state, and service-state paths under `/mnt/sdext/a90`.

No automatic package manager, remote download, or SD format/migration was added.

## Source Changes

- Added `stage3/linux_init/init_v113.c` and `stage3/linux_init/v113/*.inc.c` from v112.
- Updated `stage3/linux_init/a90_config.h` to `0.9.13` / `v113`.
- Extended runtime constants with package layout paths:
  - `pkg/bin`
  - `pkg/helpers`
  - `pkg/services`
  - `pkg/manifests`
  - `state/services`
- Extended `struct a90_runtime_status` and `runtime` output with package/helper path fields.
- Updated helper manifest lookup to prefer `pkg/manifests/helpers.manifest` while preserving fallback to the legacy `pkg/helpers.manifest` if present.
- Added v113 ABOUT/changelog entries.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v113` | `fba1e76552f7bde7cbb66da6545384c882700f170932e0f9165183f6564ff2cb` |
| `stage3/ramdisk_v113.cpio` | `0913c9ad4b6a2aeb51ad40152f5f425426043e11c0fc457b240037864acfc5a9` |
| `stage3/boot_linux_v113.img` | `becfecf749b677fb8d7edd1235282cd416dd78b4f38aba3be73d837528c9ee1d` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.13 (v113)`
  - `A90v113`
  - `0.9.13 v113 RUNTIME PACKAGE LAYOUT`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, and `native_soak_validate.py` — PASS.
- v113 include tree stale marker check for `A90v112`, `_v112`, and `init_v112` — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v113.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.13 (v113)" \
  --verify-protocol auto
```

Result:

- Native bridge v112 to TWRP recovery path succeeded.
- Boot partition prefix SHA matched `stage3/boot_linux_v113.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.13 (v113)` — PASS.
- Boot selftest reported `pass=11 warn=0 fail=0` — PASS.

Runtime/package checks:

| Command | Result |
|---|---|
| `runtime` | PASS, `backend=sd`, `root=/mnt/sdext/a90`, `fallback=no`, `writable=yes` |
| `runtime` package fields | PASS, `pkg_bin`, `pkg_helpers`, `pkg_services`, `pkg_manifests`, `state_services` printed |
| `runtime` helper state fields | PASS, `helper_manifest`, `helper_state`, `helper_deploy_log` printed |
| `helpers verbose` | PASS, manifest path is `/mnt/sdext/a90/pkg/manifests/helpers.manifest` and fallback helpers remain valid |
| `userland` | PASS, `busybox=ready toybox=ready warn=0` |
| `mountsd status` | PASS, expected SD UUID match and workspace mounted RW |
| `bootstatus` | PASS, runtime summary present |
| `selftest verbose` | PASS, `pass=11 warn=0 fail=0` |

## Soak Regression

Command:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.13 (v113)" \
  --out tmp/soak/v113-runtime-layout.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- New package directories are created under the existing runtime root only; no SD formatting or data migration is performed.
- Existing helper fallback paths remain valid.
- v114 should build on this by improving helper deployment/hash/manifest visibility.

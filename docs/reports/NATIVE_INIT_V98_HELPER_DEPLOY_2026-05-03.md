# Native Init v98 Helper Deploy Report

Date: `2026-05-03`

## Summary

- Version: `A90 Linux init 0.8.29 (v98)` / `0.8.29 v98 HELPER DEPLOY`
- Goal: add a safe helper inventory/deployment model on top of the v97 runtime root.
- Result: PASS on local build, boot image generation, flash, `cmdv1 version/status`, helper inventory, selftest, cpustress, HUD/menu, and host helper-deploy checks.
- User-facing feature changes: `helpers` command, helper summary in `status`/`bootstatus`, helper selftest entry, and `helper_deploy.py` host helper.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v98` | `0d55f6b70d71eba4524790fa72d4276694512806bc515f878a10a0693f0beac3` |
| `stage3/ramdisk_v98.cpio` | `9b578bd02a0df42534381694ebcfd77d9943e746be3eff998c123bcb9c03ee8a` |
| `stage3/boot_linux_v98.img` | `c341bc56cfd881bceaf61cb6a30193329ee65f32d686979a236a2e3322039d2e` |

## Changes

- Copied v97 source layout to `stage3/linux_init/init_v98.c` and `stage3/linux_init/v98/*.inc.c`.
- Updated version/build markers to `0.8.29` / `v98` and boot marker strings to `A90v98`.
- Added `a90_helper.c/h` for helper inventory, manifest path discovery, preferred helper path selection, and `helpers` command handling.
- Added helper candidates:
  - `a90_cpustress`
  - `a90sleep`
  - `a90_usbnet`
  - `a90_tcpctl`
  - `toybox`
- Added runtime-root manifest path:
  - `/mnt/sdext/a90/pkg/helpers.manifest`
- Added helper summary to `status` and `bootstatus`.
- Added helper selftest entry while keeping missing manifest safe and non-blocking.
- Changed `cpustress` to select the preferred helper path through `a90_helper_preferred_path()` and fall back to ramdisk `/bin/a90_cpustress`.
- Added `scripts/revalidation/helper_deploy.py` with `status`, `manifest`, `verify`, `push`, and `rollback` subcommands.
- Added ABOUT/changelog/menu entry for `0.8.29 v98 HELPER DEPLOY`.

## Manifest Policy

- Manifest file: `/mnt/sdext/a90/pkg/helpers.manifest`.
- Format: `name path role required sha256 mode size`.
- Device-side v98 checks presence, regular-file mode, executable bit, size, required flag, and preferred fallback path.
- Device-side SHA256 is intentionally not implemented in PID1 yet; manifest SHA fields are reported as unchecked and remain host-side validation material.
- Missing manifest is PASS because helper deployment is optional in v98.
- Optional helper mismatch is WARN.
- Required helper mismatch is FAIL for `helpers verify` and selftest.

## Local Validation

- Static ARM64 build with `-Wall -Wextra`: PASS
- Host Python compile including `helper_deploy.py`: PASS
- `stage3/ramdisk_v98.cpio` generated with:
  - `/init`
  - `/bin/a90sleep`
  - `/bin/a90_cpustress`
- `stage3/boot_linux_v98.img` generated from v97 boot image args with ramdisk swapped.
- Marker strings present:
  - `A90 Linux init 0.8.29 (v98)`
  - `A90v98`
  - `0.8.29 v98 HELPER DEPLOY`
- `git diff --check`: PASS

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v98.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.29 (v98)" \
  --verify-protocol auto
```

Result:

- local image marker: PASS
- local image sha256: `c341bc56cfd881bceaf61cb6a30193329ee65f32d686979a236a2e3322039d2e`
- remote pushed image sha256: `c341bc56cfd881bceaf61cb6a30193329ee65f32d686979a236a2e3322039d2e`
- boot partition prefix sha256: `c341bc56cfd881bceaf61cb6a30193329ee65f32d686979a236a2e3322039d2e`
- post-boot `cmdv1 version/status`: PASS

Regression:

| command | result |
|---|---|
| `version` | PASS, `A90 Linux init 0.8.29 (v98)` |
| `status` | PASS, helpers `entries=5 warn=0 fail=0 manifest=no` |
| `bootstatus` | PASS, helper summary present |
| `runtime` | PASS, SD runtime root `/mnt/sdext/a90` |
| `helpers` | PASS, manifest path `/mnt/sdext/a90/pkg/helpers.manifest` |
| `helpers verbose` | PASS |
| `helpers path a90_cpustress` | PASS, preferred `/bin/a90_cpustress`, SD path fallback visible |
| `selftest verbose` | PASS, `pass=10 warn=0 fail=0`, helper entry PASS |
| `storage` | PASS |
| `mountsd status` | PASS |
| `cpustress 3 2` | PASS, helper completed in `3104ms` |
| `statushud` | PASS |
| `autohud 2` | PASS |
| `screenmenu` | PASS |
| `hide` | PASS |
| `netservice status` | PASS, disabled |
| `helper_deploy.py status` | PASS |
| `helper_deploy.py manifest` | PASS, prints manifest lines for local ramdisk helpers and comments missing optional local helpers |
| `helper_deploy.py verify` | PASS |

## Acceptance

- v98 boot image flashes and verifies with `cmdv1 version/status`.
- Missing helper manifest does not block boot.
- `helpers` command reports runtime root manifest path and helper inventory.
- Helper selftest remains known-good with `fail=0`.
- `cpustress` still works through helper path selection and ramdisk fallback.
- Netservice remains compatible with v97 behavior.
- v99 can start BusyBox/static userland evaluation without changing the v98 helper inventory contract.

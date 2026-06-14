# Native Init v114 Helper Deployment 2

Date: `2026-05-04`
Build: `A90 Linux init 0.9.14 (v114)`
Marker: `0.9.14 v114 HELPER DEPLOY 2`
Baseline: `A90 Linux init 0.9.13 (v113)`

## Summary

v114 improves helper deployment visibility on top of the v113 runtime package layout.
It adds helper manifest/deploy-log path reporting and a manifest template/plan command so helper promotion to SD can be audited before any manual copy/update.

No automatic download, remote install, or destructive runtime migration was added.

## Source Changes

- Added `stage3/linux_init/init_v114.c` and `stage3/linux_init/v114/*.inc.c` from v113.
- Updated `stage3/linux_init/a90_config.h` to `0.9.14` / `v114`.
- Extended `a90_helper.c/h` with:
  - `a90_helper_deploy_log_path()`
  - `a90_helper_print_manifest_template()`
  - `helpers manifest` and `helpers plan` command aliases
- `helpers verbose` now prints `deploy_log` next to `manifest_path`.
- Added v114 ABOUT/changelog entries.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v114` | `7a92b4e088476c16c669cfce780eb26089d80f2cc2e9f0671f574debbf8bd170` |
| `stage3/ramdisk_v114.cpio` | `3bd53513e5c3a14f54a1d5905a2972de4bac07a89a1cb05abe1f0517dcd6c414` |
| `stage3/boot_linux_v114.img` | `029ed973f3e72d72451f23505445ca34bc90be47ecb5fb47bdc65217576c3e8d` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.14 (v114)`
  - `A90v114`
  - `0.9.14 v114 HELPER DEPLOY 2`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, and `native_soak_validate.py` — PASS.
- v114 include tree stale marker check for `A90v113`, `_v113`, and `init_v113` — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v114.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.14 (v114)" \
  --verify-protocol auto
```

Result:

- Native bridge v113 to TWRP recovery path succeeded.
- Boot partition prefix SHA matched `stage3/boot_linux_v114.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.14 (v114)` — PASS.
- Boot selftest reported `pass=11 warn=0 fail=0` — PASS.

Helper deployment checks:

| Command | Result |
|---|---|
| `helpers manifest` | PASS, prints manifest path, deploy log path, line format, helper manifest lines, and copy plan hints |
| `helpers verbose` | PASS, prints `manifest_path=/mnt/sdext/a90/pkg/manifests/helpers.manifest` and `deploy_log=/mnt/sdext/a90/logs/helper-deploy.log` |
| `helpers verify` | PASS, `entries=7 warn=0 fail=0 manifest=no` |
| `runtime` | PASS, package/runtime paths remain visible |
| `userland` | PASS, `busybox=ready toybox=ready warn=0` |
| `selftest verbose` | PASS, `pass=11 warn=0 fail=0` |

## Soak Regression

Command:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.14 (v114)" \
  --out tmp/soak/v114-helper-deploy.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- `helpers manifest` is an audit/planning view, not an automatic installer.
- Helper hashes are still manifest-driven; absent manifests keep `sha=-` and do not create warnings.
- v115 should harden custom remote shell behavior over verified USB NCM.

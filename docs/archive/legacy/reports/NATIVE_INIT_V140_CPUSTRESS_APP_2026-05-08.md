# Native Init v140 CPU Stress App Module Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.40 (v140)` / `0.9.40 v140 CPUSTRESS APP API`
Baseline: `A90 Linux init 0.9.39 (v139)`

## Summary

- v140 avoids network-facing expansion while cloud security scan results are pending.
- Added `a90_app_cpustress.c/h` and moved CPU stress screen app lifecycle/renderer ownership out of `v140/40_menu_apps.inc.c`.
- Preserved shell `cpustress`, menu routing, controller policy, storage, exposure, rshell, and netservice behavior.
- During validation, the first v140 ramdisk was found to miss `/bin/a90_cpustress`; the final v140 ramdisk includes both `/bin/a90_cpustress` and `/bin/a90_rshell`.
- Real-device flash, direct CPU stress run, integrated validation, quick soak, and local targeted security rescan passed.

## Code Changes

- Added `stage3/linux_init/init_v140.c` and `stage3/linux_init/v140/*.inc.c` copied from v139.
- Updated `stage3/linux_init/a90_config.h` to `0.9.40` / `v140`.
- Added `stage3/linux_init/a90_app_cpustress.c` and `stage3/linux_init/a90_app_cpustress.h`.
- `stage3/linux_init/v140/40_menu_apps.inc.c` now stores `struct a90_app_cpustress_state` and calls `a90_app_cpustress_start()`, `a90_app_cpustress_tick()`, `a90_app_cpustress_draw()`, and `a90_app_cpustress_stop()`.
- Updated host validation defaults to expect v140.
- Updated local targeted security scan to inspect the active v140 tree.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v140` | `4459db62341d19a6c7eb547da79f2329674d265ac7e4ff10dbc130ec9989f829` |
| `stage3/ramdisk_v140.cpio` | `f9f0815008df2c53c2cea54708733916cf8e8b0187fd6e5d77ba593d278d47b8` |
| `stage3/boot_linux_v140.img` | `e2d8c6ae4212f41cac3d5b82611c33a6d74c617cedca61afbe5e158c75eb1cc5` |

## Static Validation

- Static ARM64 build with `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS.
- Marker strings in init and boot image — PASS:
  - `A90 Linux init 0.9.40 (v140)`
  - `A90v140`
  - `0.9.40 v140 CPUSTRESS APP API`
- `git diff --check` — PASS.
- Host Python `py_compile` — PASS.
- Old v140 include-tree CPU stress helper lifecycle symbols removed from `40_menu_apps.inc.c` — PASS.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v140.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.40 (v140)" \
  --verify-protocol auto
```

Result: PASS.

- Local image marker and SHA check — PASS.
- Recovery ADB push and remote SHA check — PASS.
- Boot partition prefix SHA matched `stage3/boot_linux_v140.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

Direct CPU stress regression:

```bash
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py cpustress 3 2
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
```

Result: PASS. `cpustress 3 2` returned `rc=0` after `/bin/a90_cpustress` completed.

Integrated validation:

```bash
python3 scripts/revalidation/native_integrated_validate.py \
  --expect-version "A90 Linux init 0.9.40 (v140)" \
  --out tmp/validation/native-integrated-v140.txt \
  --json-out tmp/validation/native-integrated-v140.json
```

Result: `PASS commands=25`.

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.40 (v140)" \
  --out tmp/soak/v140-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- The first v140 flash exposed a packaging regression: copied v139 ramdisk lacked `/bin/a90_cpustress`. The final v140 ramdisk explicitly includes `/bin/a90_cpustress` and `/bin/a90_rshell`.
- The accepted local-control warning remains unchanged: USB ACM root shell and localhost serial bridge are intentionally present in the trusted lab boundary.
- Next work should wait for fresh Codex Cloud scan results when possible; otherwise continue with non-network UI/app split work.

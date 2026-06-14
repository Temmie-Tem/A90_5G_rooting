# A90 Native Init v117 PID1 Slim Roadmap Baseline

Date: 2026-05-05
Build: `A90 Linux init 0.9.17 (v117)`
Marker: `0.9.17 v117 PID1 SLIM ROADMAP`

## Summary

v117 starts the v117-v122 cycle from the verified v116 baseline. The runtime behavior is intentionally unchanged; the purpose is to anchor the next cycle around PID 1 slimdown before any further Wi-Fi bring-up work.

Roadmap: `docs/plans/NATIVE_INIT_V117_V122_ROADMAP_2026-05-05.md`

## Changes

- Added `init_v117.c` and `v117/*.inc.c` from v116.
- Updated version/build markers to `0.9.17` / `v117`.
- Added changelog/About entry `0.9.17 v117 PID1 SLIM ROADMAP`.
- Added v117-v122 roadmap with guardrails and version-by-version targets.
- No shell, storage, service, KMS, input, NCM, rshell, or Wi-Fi behavior change.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v117` | `eed37baf7dd63ac5703ec8a0f6bc9f5c668cebcb29cf237d43942a2b0a73dcca` |
| `stage3/ramdisk_v117.cpio` | `765b0ad1f9a6b27106f244266faab36659a460b98cbf0438995c015df9c76a63` |
| `stage3/boot_linux_v117.img` | `dcd8d4cfcb729a3c9ebfed0eee9a141675492600de5742087476fc96beb683bc` |
| `tmp/soak/v117-quick-soak.txt` | `327c5bb75131388edc35ea5bfb0f94c501c502b6a70242898a60432b871ef9f5` |

## Validation

### Static

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS
- `strings` marker check for `A90 Linux init 0.9.17 (v117)`, `A90v117`, `0.9.17 v117 PID1 SLIM ROADMAP` — PASS
- `git diff --check` — PASS
- host Python `py_compile` for flash/control scripts — PASS

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v117.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.17 (v117)" \
  --verify-protocol auto
```

Result: PASS

Evidence:

- local image marker and SHA256 verified
- TWRP `adb push` and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Regression

- `bootstatus` — PASS
- `selftest verbose` — PASS (`pass=11 warn=0 fail=0`)
- `storage` — PASS (`backend=sd`, fallback `no`)
- `mountsd status` — PASS (`state=mounted mode=rw`)
- `diag summary` — PASS
- `statushud` — PASS
- `autohud 2` — PASS
- `screenmenu` — PASS, nonblocking
- `hide` — PASS
- `native_soak_validate.py --cycles 3 --sleep 2` — PASS (`cycles=3 commands=14`)

## Next

Proceed to v118 `SHELL META API`:

- keep command handler bodies/table stable,
- move low-risk command metadata/count/report helpers into `a90_shell.c/h`,
- verify `help`, `last`, `cmdv1`, unknown command, and busy result behavior unchanged.

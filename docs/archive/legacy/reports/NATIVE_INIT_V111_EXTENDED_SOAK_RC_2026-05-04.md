# Native Init v111 Extended Soak RC

Date: `2026-05-04`
Build: `A90 Linux init 0.9.11 (v111)`
Marker: `0.9.11 v111 EXTENDED SOAK RC`
Baseline: `A90 Linux init 0.9.10 (v110)`

## Summary

v111 is a release-candidate style stability checkpoint after v109-v110 structure cleanup.
It keeps the v110 runtime behavior and records a longer host-driven soak before USB/service/runtime expansion.

No runtime feature was added.

## Source Changes

- Added `stage3/linux_init/init_v111.c` and `stage3/linux_init/v111/*.inc.c` from v110.
- Updated `stage3/linux_init/a90_config.h` to `0.9.11` / `v111`.
- Added v111 ABOUT/changelog entries.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v111` | `94549da2a4bcf15e1b70165cd4ccceb816a5da9fa88b061b240d9b2afcb9a6a1` |
| `stage3/ramdisk_v111.cpio` | `8b155d91f06044a112f22b1e5368a1f1181be7528415505b0e78790ff23b70c4` |
| `stage3/boot_linux_v111.img` | `bdd8d871a442731b101be001501288da2930b22c9aab37057732008cb14a656e` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.11 (v111)`
  - `A90v111`
  - `0.9.11 v111 EXTENDED SOAK RC`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `native_soak_validate.py`, `diag_collect.py` — PASS.
- v111 include tree stale marker check for `A90v110`, `_v110`, and `init_v110.c` — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v111.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.11 (v111)" \
  --verify-protocol auto
```

Result:

- Native bridge v110 to TWRP recovery path succeeded.
- Boot partition prefix SHA matched `stage3/boot_linux_v111.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.11 (v111)` — PASS.

Extended soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 10 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.11 (v111)" \
  --out tmp/soak/v111-extended-soak.txt
```

Result: `PASS cycles=10 commands=14`.

Final state checks after soak:

| Check | Result |
|---|---|
| `status` | PASS, uptime about 83s, autohud running, netservice disabled |
| `service list` | PASS, autohud running, tcpctl/adbd/rshell stopped |
| `bootstatus` | PASS, `pass=11 warn=0 fail=0` |
| `selftest verbose` | PASS, `pass=11 warn=0 fail=0` |

## Notes

- This is not a 30-60 minute physical soak; it is a bounded host-driven extended soak suitable for this development cycle.
- v112 should focus on opt-in USB/NCM service soak and rollback behavior.

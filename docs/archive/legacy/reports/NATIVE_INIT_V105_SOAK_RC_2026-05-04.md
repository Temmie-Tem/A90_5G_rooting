# Native Init v105 Soak RC Report

Date: `2026-05-04`

## Summary

- Version: `A90 Linux init 0.9.5 (v105)` / `0.9.5 v105 SOAK RC`.
- Baseline: v104 Wi-Fi feasibility gate.
- v105 is a stabilization/release-candidate build for the v96-v104 stack.
- Behavior is intentionally conservative: no Wi-Fi enablement, no rfkill writes, no module load/unload, no firmware/vendor mutation, and no partition formatting.
- Added `scripts/revalidation/native_soak_validate.py` for bounded serial-bridge soak validation.

## Key Changes

- Added `stage3/linux_init/init_v105.c` and `stage3/linux_init/v105/*.inc.c`.
- Updated `stage3/linux_init/a90_config.h` to `0.9.5` / `v105`.
- Updated kmsg marker and ABOUT/changelog strings to `A90v105` and `0.9.5 v105 SOAK RC`.
- Added `scripts/revalidation/native_soak_validate.py`.
- Preserved v104 runtime, storage, service, Wi-Fi inventory, and Wi-Fi feasibility behavior.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v105` | `624242bafb44598feaddf636a60b64a996d44f5e05dc622f64b79518706a8209` |
| `stage3/ramdisk_v105.cpio` | `6733a511a5cc8a5a79c09333510c0d1913219ed13e15b3a2cbd1e7550be27726` |
| `stage3/boot_linux_v105.img` | `2dcda57156385c2d092a0865ea31bd7853399287df5633d39b08ae4b01d53338` |

Ramdisk entries:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- Static ARM64 init build with `-Wall -Wextra` — PASS.
- `stage3/ramdisk_v105.cpio` and `stage3/boot_linux_v105.img` generated from v104 boot args with only ramdisk replaced — PASS.
- Boot image markers found:
  - `A90 Linux init 0.9.5 (v105)`
  - `A90v105`
  - `0.9.5 v105 SOAK RC`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `diag_collect.py`, `wifi_inventory_collect.py`, and `native_soak_validate.py` — PASS.
- v105 stale marker scan for current-version v104 strings in `init_v105.c`, `v105/*.inc.c`, and `a90_config.h` — PASS.

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v105.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.5 (v105)" \
  --verify-protocol auto
```

Result:

- Local image marker and SHA256 check — PASS.
- TWRP push and remote SHA256 check — PASS.
- boot partition prefix SHA256 matched `stage3/boot_linux_v105.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

## Device Validation

- `version`: PASS, `A90 Linux init 0.9.5 (v105)`.
- `status`: PASS, `selftest pass=11 warn=0 fail=0`, SD runtime, autohud running, netservice disabled, rshell stopped.
- `bootstatus`: PASS, `BOOT OK shell 4.1s`.
- `selftest verbose`: PASS, `pass=11 warn=0 fail=0`.
- `diag`: PASS, compact summary includes v105 version and diagnostics coverage.
- `runtime`: PASS, SD runtime root `/mnt/sdext/a90`, fallback `no`, writable `yes`.
- `storage`: PASS, expected SD UUID matched and writable.
- `mountsd status`: PASS.
- `service list`: PASS, autohud running, tcpctl/adbd/rshell stopped.
- `netservice status`: PASS after `hide`; an initial attempt correctly hit menu busy gate while auto menu was active.
- `wifiinv`: PASS, no native WLAN/rfkill/module evidence.
- `wififeas gate`: PASS, decision remains `baseline-required` in default native state.
- `statushud`: PASS.
- `autohud 2`: PASS.
- `screenmenu`: PASS, nonblocking.
- `hide`: PASS.
- `cpustress 3 2`: PASS, `/bin/a90_cpustress` completed.

Captured host logs:

- `tmp/soak/v105-device-validation.txt`
- `tmp/soak/v105-quick-soak.txt`
- `tmp/soak/v105-post-soak-status.txt`

## Quick Soak Validation

Command:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 10 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.5 (v105)" \
  --out tmp/soak/v105-quick-soak.txt
```

Result:

- 10 cycles — PASS.
- 14 commands per cycle — PASS.
- Commands covered:
  - `version`
  - `status`
  - `bootstatus`
  - `selftest verbose`
  - `runtime`
  - `storage`
  - `service list`
  - `diag`
  - `wififeas gate`
  - `statushud`
  - `autohud 2`
  - `screenmenu`
  - `hide`
  - `netservice status`
- Final status after soak: PASS, `selftest pass=11 warn=0 fail=0`, netservice disabled, tcpctl stopped, rshell stopped.
- Final service list after soak: PASS, autohud running, tcpctl/adbd/rshell stopped.

## Notes

- v105 does not change Wi-Fi bring-up policy. v104 evidence still blocks native Wi-Fi enablement until kernel-facing WLAN/rfkill/module prerequisites are visible.
- The quick soak is bounded and non-destructive. Longer physical USB reconnect, NCM/tcpctl, remote shell, and recovery transition soaks remain optional/manual follow-up checks.
- The initial `netservice status` busy result during manual validation was expected menu busy-gate behavior and was rerun successfully after `hide`.

## Current Baseline

`A90 Linux init 0.9.5 (v105)` is now the latest verified native init baseline and the v96-v105 roadmap release-candidate endpoint.

Recommended next direction: perform optional longer soak/reconnect checks, then choose the next cycle separately instead of expanding v105 further.

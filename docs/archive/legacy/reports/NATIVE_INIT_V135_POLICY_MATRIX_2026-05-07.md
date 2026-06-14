# A90 Native Init v135 Policy Matrix

Date: 2026-05-07
Build: `A90 Linux init 0.9.35 (v135)`
Marker: `0.9.35 v135 POLICY MATRIX`
Status: real-device flash verified

## Summary

v135 adds a non-destructive controller policy matrix for menu-visible and
power-page command safety decisions. It does not add a listener, does not broaden
network exposure, and does not change existing command behavior except for adding
the read-only `policycheck [status|run|verbose]` observation command.

The purpose is to prevent another absent-subcommand or allowlist drift class like
the previous bare `mountsd` menu-visible side effect.

## Changes

- Copied v134 into `init_v135.c` and `v135/*.inc.c`.
- Bumped version/build to `0.9.35` / `v135`.
- Added `0.9.35 v135 POLICY MATRIX` to the shared changelog table.
- Added controller policy matrix state and runner to `a90_controller.c/h`.
- Added `policycheck [status|run|verbose]` shell command.
- Updated `local_security_rescan.py` to active v135 and added policy matrix wiring check.
- Updated default soak expected version to v135.

## Matrix Coverage

| scope | examples |
|---|---|
| menu-visible allow | `version`, `status`, `exposure status`, `policycheck run`, `mountsd status`, `service status tcpctl`, `diag summary`, `wifiinv paths` |
| menu-visible block | bare `mountsd`, `mountsd rw`, `netservice start`, `rshell start`, `service start tcpctl`, `run`, `writefile`, `mountfs`, `reboot` |
| power-page allow | `help`, `status`, `exposure status`, `policycheck`, `storage`, `timeline`, `logpath`, `inputlayout`, `reattach`, `stophud`, `hide` |
| power-page block | network/service mutation, filesystem mutation, process execution, `reboot`, `recovery`, `poweroff` from serial |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v135` | `76a3797194726b3a6e6ea43ed2645a238175fece5f1fce57a05d486f42e1d246` |
| `stage3/ramdisk_v135.cpio` | `1678c350509df511b29d6870b146fd8ee2ce374d5dd1a2825dab0ddf274fdfaa` |
| `stage3/boot_linux_v135.img` | `e265c09f2a62efeb8bbe9520fe8119e631fcb7ad5f2d77bf1efa6f17962e6718` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.35 (v135)`, `A90v135`, `0.9.35 v135 POLICY MATRIX`, and `policycheck [status|run|verbose]` — PASS.
- Boot image repack from v134 boot image args with only ramdisk replaced — PASS.
- host Python `py_compile` for revalidation scripts — PASS.
- stale v134 marker scan in `init_v135.c`, `v135/*.inc.c`, and v135 soak default — PASS.
- `git diff --check` — PASS.
- local targeted v135 security rescan — PASS 16 / WARN 1 / FAIL 0.

### Device

Flash command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v135.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.35 (v135)" \
  --verify-protocol auto
```

Result:

- TWRP/recovery ADB push and boot partition write — PASS.
- Remote boot block prefix hash matched local image prefix — PASS.
- Native init post-boot `cmdv1 version/status` verification — PASS.
- Verified version: `A90 Linux init 0.9.35 (v135)`.

Runtime checks:

```sh
python3 scripts/revalidation/a90ctl.py policycheck run
python3 scripts/revalidation/a90ctl.py policycheck verbose
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py mountsd
python3 scripts/revalidation/a90ctl.py mountsd status
python3 scripts/revalidation/a90ctl.py netservice start
python3 scripts/revalidation/a90ctl.py service start tcpctl
python3 scripts/revalidation/a90ctl.py run /bin/a90sleep 1
python3 scripts/revalidation/a90ctl.py writefile /tmp/x y
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py exposure guard
python3 scripts/revalidation/native_soak_validate.py --cycles 3 --sleep 1
```

Observed:

- `policycheck run`: `cases=91 pass=91 fail=0 allowed=45 blocked=46`.
- `policycheck verbose`: all entries PASS.
- `screenmenu`: immediate nonblocking rc=0/status=ok.
- menu-visible bare `mountsd`: blocked with rc=-16/status=busy.
- menu-visible `mountsd status`: allowed rc=0/status=ok.
- menu-visible `netservice start`, `service start tcpctl`, `run`, `writefile`: blocked rc=-16/status=busy.
- `hide`: immediate rc=0/status=ok.
- `exposure guard`: rc=0/status=ok.
- quick native soak: PASS cycles=3 commands=14.

## Notes

- v135 remains a control-policy hardening release, not a feature release.
- README/latest verified docs now point to v135.
- The remaining security warning is still the accepted USB-local/localhost root-control boundary.

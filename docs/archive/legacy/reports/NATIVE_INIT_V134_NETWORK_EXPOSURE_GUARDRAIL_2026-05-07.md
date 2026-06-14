# A90 Native Init v134 Network Exposure Guardrail

Date: 2026-05-07
Build: `A90 Linux init 0.9.34 (v134)`
Marker: `0.9.34 v134 EXPOSURE GUARDRAIL`
Status: real-device flash verified

## Summary

v134 adds a read-only network exposure guardrail layer before any broader network or Wi-Fi work. It does not add a new listener, does not start services automatically, and does not change the trusted-lab USB ACM control boundary. The new `exposure [status|verbose|guard]` command summarizes ACM/NCM/tcpctl/rshell exposure state and returns non-zero only when a guardrail failure is detected.

## Changes

- Copied v133 into `init_v134.c` and `v134/*.inc.c`.
- Bumped version/build to `0.9.34` / `v134`.
- Added `a90_exposure.c/h` for read-only exposure snapshots, summaries, guard checks, and console output.
- Added `exposure [status|verbose|guard]` to the v134 shell table.
- Added compact exposure summaries to `status` and `bootstatus`.
- Added `[exposure]` section to `diag` output without token values.
- Added `0.9.34 v134 EXPOSURE GUARDRAIL` to the shared changelog table.
- Updated local security rescan to active v134 and added an exposure wiring check.

## Guardrail Coverage

| surface | evidence |
|---|---|
| USB ACM shell | reports presence and trusted-lab-only boundary |
| Host bridge | reports localhost and identity-pinning expectation |
| NCM | reports interface, IP, netservice flag, and running state |
| tcpctl | reports running state, pid, bind address, port, token presence/mode, auth-required expectation |
| rshell | reports enabled/running state, bind address, port, flag/token path, token presence/mode |
| diagnostics | `diag` emits `[exposure]` with `token_value=hidden` |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v134` | `df2bcfb51e292cad0408d391beb43e4550ada7dad82a43c8482494db49b8b7d8` |
| `stage3/ramdisk_v134.cpio` | `fa94087feb39f7b8d5438938a596f56348c354c7f37e563460e7419511c5f269` |
| `stage3/boot_linux_v134.img` | `b5b6554590366ee6d1cab796d5be88cfedbdcaca67027c09a18143a3d44d17f6` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.34 (v134)`, `A90v134`, `0.9.34 v134 EXPOSURE GUARDRAIL`, and `exposure [status|verbose|guard]` — PASS.
- Boot image repack from v133 boot image args with only ramdisk replaced — PASS.
- host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `local_security_rescan.py`, and `native_soak_validate.py` — PASS.
- stale v133 marker scan in `init_v134.c` and `v134/*.inc.c` — PASS.
- `git diff --check` — PASS.
- local targeted v134 security rescan — PASS 15 / WARN 1 / FAIL 0.

### Device

Flash command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v134.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.34 (v134)" \
  --verify-protocol auto
```

Result:

- TWRP/recovery ADB push and boot partition write — PASS.
- Remote boot block prefix hash matched local image prefix — PASS.
- Native init post-boot `cmdv1 version/status` verification — PASS.
- Verified version: `A90 Linux init 0.9.34 (v134)`.

Runtime checks:

```sh
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py exposure status
python3 scripts/revalidation/a90ctl.py exposure verbose
python3 scripts/revalidation/a90ctl.py exposure guard
python3 scripts/revalidation/a90ctl.py diag
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
```

Observed:

- `status`/`bootstatus`: `exposure: guard=ok warn=0 fail=0 ncm=absent tcpctl=stopped rshell=stopped boundary=usb-local`.
- `exposure status|verbose|guard`: rc=0/status=ok and guardrails report tcpctl/rshell bind/auth/token state.
- `diag`: `[exposure]` is present and token fields are reported as `token_value=hidden`.
- `screenmenu`: immediate nonblocking rc=0/status=ok; `status` remains responsive while menu is visible.
- `hide`: immediate rc=0/status=ok.

## Notes

- README/latest verified docs now point to v134.
- F021/F030 remain accepted trusted-lab-boundary items only while USB ACM and host bridge remain USB-local/localhost-only.
- F032/F033 follow-up fixes are present in the v134 source tree because v134 was copied from the patched v133 tree.

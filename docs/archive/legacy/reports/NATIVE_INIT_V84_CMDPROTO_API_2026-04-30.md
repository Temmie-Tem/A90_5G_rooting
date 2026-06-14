# Native Init v84 Cmdproto API Report (2026-04-30)

## Summary

- Build: `A90 Linux init 0.8.15 (v84)`
- Source: `stage3/linux_init/init_v84.c` + `stage3/linux_init/v84/*.inc.c`
- New module: `stage3/linux_init/a90_cmdproto.c/h`
- Boot image: `stage3/boot_linux_v84.img`
- Result: PASS — TWRP flash, post-boot `cmdv1 version/status`, protocol regressions, storage/display regressions, and cancel paths verified.

## Changes

- Added `a90_cmdproto.c/h` for `cmdv1/cmdv1x` protocol ownership.
- Moved `A90P1 BEGIN/END` frame formatting and `ok/error/unknown/busy` status mapping out of shell dispatch.
- Moved `cmdv1x` `len:hex` argv decoding out of the include-tree boot services file.
- Kept command table, busy gate, `last_result`, `shell_protocol_seq`, and `shell_loop()` in the v84 include tree to avoid behavior drift.
- Added on-device changelog entry `0.8.15 v84 CMDPROTO API`.

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v84` | `e52d034cbd3a741841e7be9ed45b8c9a54d5c2db491075fde022097374879886` |
| `stage3/ramdisk_v84.cpio` | `8223b1c31d4ccca2521647feb9d50d864dd2332a260cc79f2272d5e74547763f` |
| `stage3/boot_linux_v84.img` | `0a0be54d12489d7aa08437cb7e1aa3537448ddfed49393538a144e71f084bdcd` |

## Validation

- Local build: static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Static checks: `git diff --check`, `py_compile` for `a90ctl.py` and `native_init_flash.py` — PASS
- Boot image markers: `A90 Linux init 0.8.15 (v84)`, `A90v84`, `0.8.15 v84 CMDPROTO API` — PASS
- Flash: native bridge → TWRP → boot partition write/readback → v84 boot — PASS
- Post-boot verify: `cmdv1 version/status`, `rc=0`, `status=ok` — PASS
- Protocol regression:
  - `cmdv1 version/status` — PASS
  - `cmdv1 does-not-exist` → `status=unknown` — PASS
  - malformed `cmdv1x bad` → framed `status=error` — PASS
  - `a90ctl.py --json echo "hello world"` → `cmdv1x` whitespace argv decode — PASS
  - active-menu `waitkey 1` gate → `status=busy` — PASS
- Runtime regression:
  - `logpath`, `timeline`, `bootstatus`, `storage`, `mountsd status` — PASS
  - `displaytest safe`, `autohud 2` — PASS
  - `run /bin/a90sleep 1`, `cpustress 3 2`, `watchhud 1 2` — PASS
  - q cancel for `run`, `cpustress`, `watchhud` — PASS
  - `reattach`, `usbacmreset` — PASS

## Notes

- `a90_cmdproto.c/h` does not know the shell command table, menu state, storage state, or command busy policy.
- Reboot/destructive raw-control behavior is unchanged.
- Next module candidate is v85 `run/service/netservice management`.

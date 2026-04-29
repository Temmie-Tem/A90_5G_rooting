# Native Init v85 Run/Service API Report (2026-04-30)

## Summary

- Build: `A90 Linux init 0.8.16 (v85)`
- Source: `stage3/linux_init/init_v85.c` + `stage3/linux_init/v85/*.inc.c`
- New modules: `stage3/linux_init/a90_run.c/h`, `stage3/linux_init/a90_service.c/h`
- Boot image: `stage3/boot_linux_v85.img`
- Result: PASS — TWRP flash, post-boot `cmdv1 version/status`, run/service regressions, and q cancel paths verified.

## Changes

- Added `a90_run.c/h` for shared fork/exec/wait/timeout/cancel/reap/stop handling.
- Added `a90_service.c/h` for static PID registry of `autohud`, `tcpctl`, and `adbd`.
- Replaced duplicated `run`/`runandroid` child wait/cancel code with `a90_run`.
- Replaced netservice helper wait and `tcpctl` lifecycle with `a90_run` + `a90_service`.
- Replaced direct `hud_pid`, `tcpctl_pid`, and `adbd_pid` globals with service registry calls.
- Kept netservice command semantics, shell dispatch, storage, KMS/HUD/menu, and cpustress worker behavior stable.

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v85` | `ca227754279f8f23484dce6db4b0b8df9c6cb0412deec916be32dd9a028c31f2` |
| `stage3/ramdisk_v85.cpio` | `5d35a08d472906b6ae9ad6e0dc0a364a6b1a08e42bc0de51674073901a19fc68` |
| `stage3/boot_linux_v85.img` | `9e3da0ffd0616292b563c06acee9977de402db84f1de6994db0feb6cf6cf367e` |

## Validation

- Local build: static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Static checks: `git diff --check`, `py_compile` for `a90ctl.py`, `native_init_flash.py`, `tcpctl_host.py`, `netservice_reconnect_soak.py` — PASS
- Boot image markers: `A90 Linux init 0.8.16 (v85)`, `A90v85`, `0.8.16 v85 RUN SERVICE API` — PASS
- Flash: native bridge → TWRP → boot partition write/readback → v85 boot — PASS
- Post-boot verify: `cmdv1 version/status`, `rc=0`, `status=ok` — PASS
- Runtime regression:
  - `logpath`, `timeline`, `bootstatus`, `storage`, `mountsd status` — PASS
  - `run /bin/a90sleep 1`, `runandroid /system/bin/toybox true` — PASS
  - `cpustress 3 2`, `watchhud 1 2`, `autohud 2`, `stophud` — PASS
  - q cancel for `run /bin/a90sleep 10`, `cpustress 10 2`, `watchhud 1 10` — PASS
  - `startadbd`, `status` stale PID tracking, `stopadbd`, serial recovery — PASS
  - `netservice status`, raw `netservice start`, `tcpctl=running`, raw `netservice stop`, `tcpctl=stopped` — PASS
- NCM host-side ping: device NCM/tcpctl reached `running`, but host IP setup required interactive `sudo`; run `sudo ip addr replace 192.168.7.1/24 dev <enx...>` before host ping/tcpctl host tests.

## Notes

- `netservice start|stop` can still disconnect the framed command stream during USB re-enumeration; use raw bridge or verify with a follow-up `cmdv1 status`.
- `a90_service` is intentionally small and only tracks process IDs for the current PID1 process.
- Next module candidate is v86 `KMS/draw/HUD/input/menu UI layering`.

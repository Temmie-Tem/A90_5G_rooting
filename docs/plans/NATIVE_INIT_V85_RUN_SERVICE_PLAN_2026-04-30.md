# Native Init v85 Run/Service Plan (2026-04-30)

## Summary

- Target: `A90 Linux init 0.8.16 (v85)`
- Theme: `0.8.16 v85 RUN SERVICE API`
- Scope: safe process lifecycle refactor only.
- Baseline: v84 `a90_cmdproto.c/h` verified build.

## Key Changes

- Add `a90_run.c/h` for shared fork/exec/wait/timeout/cancel/reap/stop handling.
- Add `a90_service.c/h` for PID registry of `autohud`, `tcpctl`, and `adbd`.
- Move `run`, `runandroid`, `netservice` helper execution, `tcpctl` spawn/stop, and `adbd` spawn/stop onto the shared APIs.
- Keep shell dispatch, netservice policy, KMS/HUD/menu, storage, and cpustress worker behavior unchanged.
- Keep `netservice start|stop` raw-control friendly because USB re-enumeration can disconnect the framed command stream.

## Validation Plan

- Build `init_v85.c` with `a90_util`, `a90_log`, `a90_timeline`, `a90_console`, `a90_cmdproto`, `a90_run`, and `a90_service`.
- Verify markers: `A90 Linux init 0.8.16 (v85)`, `A90v85`, `0.8.16 v85 RUN SERVICE API`.
- Flash from native init through TWRP using `native_init_flash.py --verify-protocol auto`.
- Regress `version`, `status`, `logpath`, `timeline`, `bootstatus`, `storage`, `mountsd status`.
- Regress `run`, `runandroid`, `cpustress`, `watchhud`, `autohud`, `stophud`, `startadbd`, `stopadbd`, `netservice status/start/stop`.
- Confirm q cancel for `run`, `cpustress`, and `watchhud`.

## Assumptions

- v85 does not add user-facing features beyond more reliable PID/process lifecycle management.
- `a90_service` owns only PID state and does not know netservice policy.
- `a90_run` may depend on console/log/util but not shell/menu/storage policy.
- Full `a90_netservice.c/h` and UI layer split remain v86+ candidates.

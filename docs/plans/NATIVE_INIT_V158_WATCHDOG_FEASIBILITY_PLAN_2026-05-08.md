# Native Init v158 Watchdog Read-only Feasibility Plan (2026-05-08)

## Summary

- target build: `A90 Linux init 0.9.58 (v158)`
- marker: `0.9.58 v158 WATCHDOG FEASIBILITY`
- 목적은 watchdog 기능 존재 여부와 sysfs 노출 상태를 read-only로 확인하는 것이다.
- v158은 `/dev/watchdog*`를 open하지 않는다.

## Scope

- `a90_watchdoginv.c/h`를 추가한다.
- `watchdoginv [summary|full|paths]` command를 추가한다.
- `status`와 `bootstatus`에 watchdog summary를 추가한다.
- `scripts/revalidation/watchdog_feas_collect.py` host collector를 추가한다.

## Read-only Rules

- 허용: `/sys/class/watchdog`, `/dev/watchdog*` lstat, `/proc/cmdline` 조회.
- 허용: readable sysfs watchdog attributes 출력.
- 금지: `/dev/watchdog*` open.
- 금지: timeout/pretimeout/nowayout write.
- 금지: watchdog ping, start, stop, ioctl.

## Validation

- local static ARM64 build.
- `strings` marker 확인.
- `git diff --check`.
- host Python `py_compile`.
- real-device flash with `native_init_flash.py --verify-protocol auto`.
- `watchdoginv`, `watchdoginv full`, `watchdoginv paths`.
- `watchdog_feas_collect.py --expect-version "A90 Linux init 0.9.58 (v158)"`.
- `native_integrated_validate.py --expect-version "A90 Linux init 0.9.58 (v158)"`.

## Acceptance

- known-good A90에서 watchdog command rc=0.
- `/dev/watchdog*` open 없이 device node/class/sysfs 상태를 판정한다.
- host collector output은 private file handling을 유지한다.
- watchdog state 변화나 reboot risk가 없다.


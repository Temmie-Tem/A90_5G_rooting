# Native Init v159 Tracefs/Ftrace Feasibility Plan (2026-05-08)

## Summary

- target build: `A90 Linux init 0.9.59 (v159)`
- marker: `0.9.59 v159 TRACEFS FEASIBILITY`
- 목적은 tracefs/ftrace 사용 가능성을 read-only로 확인하는 것이다.
- v159은 tracefs mount, `tracing_on` write, `current_tracer` write를 수행하지 않는다.

## Scope

- `a90_tracefs.c/h`를 추가한다.
- `tracefs [summary|full|paths]` command를 추가한다.
- `status`와 `bootstatus`에 tracefs summary를 추가한다.
- `scripts/revalidation/tracefs_feas_collect.py` host collector를 추가한다.

## Read-only Rules

- 허용: `/proc/filesystems`, `/proc/mounts`, `/sys/kernel/tracing`, `/sys/kernel/debug/tracing` 조회.
- 허용: mounted state와 readable `current_tracer`, `tracing_on`, `available_tracers`, `available_events` sample 출력.
- 금지: tracefs/debugfs mount.
- 금지: `tracing_on` 변경.
- 금지: `current_tracer`, events, filters, trace buffer write.

## Validation

- local static ARM64 build.
- `strings` marker 확인.
- `git diff --check`.
- host Python `py_compile`.
- real-device flash with `native_init_flash.py --verify-protocol auto`.
- `tracefs`, `tracefs full`, `tracefs paths`.
- `tracefs_feas_collect.py --expect-version "A90 Linux init 0.9.59 (v159)"`.
- `native_integrated_validate.py --expect-version "A90 Linux init 0.9.59 (v159)"`.

## Acceptance

- known-good A90에서 tracefs command rc=0.
- tracefs/debugfs support와 current mounted/readable state가 한 번에 판정 가능하다.
- host collector output은 private file handling을 유지한다.
- tracing state를 변경하지 않는다.


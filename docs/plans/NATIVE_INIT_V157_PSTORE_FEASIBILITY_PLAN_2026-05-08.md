# Native Init v157 Pstore/Ramoops Feasibility Plan (2026-05-08)

## Summary

- target build: `A90 Linux init 0.9.57 (v157)`
- marker: `0.9.57 v157 PSTORE FEASIBILITY`
- 목적은 pstore/ramoops crash log 보존 가능성을 read-only로 판정할 근거를 모으는 것이다.
- v157은 pstore mount, reboot, crash trigger, persistence write를 수행하지 않는다.

## Scope

- `a90_pstore.c/h`를 추가한다.
- `pstore [summary|full|paths]` command를 추가한다.
- `status`와 `bootstatus`에 pstore feasibility summary를 추가한다.
- `scripts/revalidation/pstore_feas_collect.py` host collector를 추가한다.

## Read-only Rules

- 허용: `/proc/filesystems`, `/proc/mounts`, `/proc/cmdline`, `/sys/fs/pstore`, `/sys/module/ramoops` 조회.
- 허용: pstore fs support, mounted state, entry count, entry class count, ramoops cmdline/module hint 출력.
- 금지: pstore mount.
- 금지: panic/reboot 보존성 테스트.
- 금지: pstore entry 삭제/쓰기.

## Validation

- local static ARM64 build.
- `strings` marker 확인.
- `git diff --check`.
- host Python `py_compile`.
- real-device flash with `native_init_flash.py --verify-protocol auto`.
- `pstore`, `pstore full`, `pstore paths`.
- `pstore_feas_collect.py --expect-version "A90 Linux init 0.9.57 (v157)"`.
- `native_integrated_validate.py --expect-version "A90 Linux init 0.9.57 (v157)"`.

## Acceptance

- known-good A90에서 pstore command rc=0.
- support/mount/entry/module/cmdline 상태가 한 번에 판정 가능하다.
- host collector output은 private file handling을 유지한다.
- pstore mount와 reboot persistence 검증은 v157에서 발생하지 않는다.


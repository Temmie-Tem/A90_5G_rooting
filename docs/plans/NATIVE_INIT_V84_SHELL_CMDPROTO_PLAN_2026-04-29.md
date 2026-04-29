# v84 Plan: Shell/Cmdproto Boundary (2026-04-29)

## Summary

- 기준 버전은 `A90 Linux init 0.8.14 (v83)`, 구현 버전은 `A90 Linux init 0.8.15 (v84)`로 간다.
- v84의 핵심은 **host tooling이 의존하는 `cmdv1/cmdv1x` framed protocol을 shell dispatch에서 분리**하는 것이다.
- 전체 shell을 한 번에 `.c/.h`로 빼지 않는다. 먼저 `cmdproto`를 API화하고, command table/dispatch는 v84 include tree에 남긴다.
- 목적은 기능 추가가 아니라 `A90P1` frame, `cmdv1x` argv decode, status 문자열 판정을 한 계층으로 모아 v85 이후 shell/run 분리를 쉽게 만드는 것이다.

## Why This Split Comes First

v83에서 `a90_console.c/h`가 console fd, attach/reattach, readline, cancel polling을 소유하게 됐다. 그 다음으로 위험도가 낮고 검증 가치가 큰 경계는 `cmdproto`다.

- `native_init_flash.py`와 `a90ctl.py`가 `cmdv1/cmdv1x` 결과를 신뢰하므로 host 검증 안정성에 직접 연결된다.
- `cmdv1x` length-prefixed argv decode는 command handler와 무관한 protocol 책임이다.
- `A90P1 BEGIN/END` 출력은 shell execution 결과를 감싸는 protocol 책임이며, command table 내부에 계속 섞이면 v85 `run/service` 분리 때 다시 풀어야 한다.
- `reboot`, `recovery`, `poweroff`처럼 연결 종료가 정상 결과인 raw-control 명령은 계속 raw path 특성을 유지한다.

## Scope

### In Scope

- `stage3/linux_init/init_v84.c` 생성
- `stage3/linux_init/v84/*.inc.c` 생성
- `stage3/linux_init/a90_cmdproto.c/h` 추가
- version/build/changelog를 `0.8.15 v84 CMDPROTO API`로 갱신
- `cmdv1x` token decode helper 이동
- `A90P1 BEGIN/END` frame 출력 helper 이동
- protocol status 판정 helper 이동
- v84 call site에서 새 API 사용
- 기존 `cmdv1`, `cmdv1x`, raw command 동작 유지

### Out Of Scope

- command table 전체를 `a90_shell.c/h`로 이동
- `last_result`, busy gate, `execute_shell_command()`, `shell_loop()`의 소유권 변경
- `run`, timeout, cancel, zombie reap 공통화
- KMS/HUD/menu/input 분리
- storage/netservice 분리
- boot image flash 자동화 방식 변경

## Target Files

```text
stage3/linux_init/
├── init_v84.c
├── a90_cmdproto.c
├── a90_cmdproto.h
└── v84/
    ├── 00_prelude.inc.c
    ├── 10_core_log_console.inc.c
    ├── 20_device_display.inc.c
    ├── 40_menu_apps.inc.c
    ├── 50_boot_services.inc.c
    ├── 60_shell_basic_commands.inc.c
    ├── 70_storage_android_net.inc.c
    ├── 80_shell_dispatch.inc.c
    └── 90_main.inc.c
```

## Proposed API

`a90_cmdproto.h`는 protocol 구현만 공개한다. command dispatch나 command table은 공개하지 않는다.

```c
struct a90_cmdproto_decoded {
    char *argv[CMDV1X_MAX_ARGS];
    char buffer[512];
    int argc;
};

const char *a90_cmdproto_status(int result, bool unknown, bool busy);
void a90_cmdproto_begin(unsigned long seq,
                        const char *command,
                        int argc,
                        unsigned int flags);
void a90_cmdproto_end(unsigned long seq,
                      const char *command,
                      int result,
                      int result_errno,
                      long duration_ms,
                      unsigned int flags,
                      const char *status);
int a90_cmdproto_decode_v1x(char **tokens,
                            int token_count,
                            struct a90_cmdproto_decoded *decoded);
void a90_cmdproto_print_decode_error(unsigned long seq,
                                     int result,
                                     void (*save_result)(const char *command,
                                                         int code,
                                                         int saved_errno,
                                                         long duration_ms,
                                                         unsigned int flags));
```

구현 중 callback이 과하면 `print_decode_error`는 shell include tree에 남겨도 된다. 단, `hex_digit_value`, token parse, decode buffer ownership은 `a90_cmdproto.c`로 이동한다.

## Ownership Rules

- `a90_cmdproto.c`
  - `cmdv1x` `len:hex` token parsing
  - decoded argv buffer ownership
  - `A90P1 BEGIN/END` frame formatting
  - `ok/error/unknown/busy` status string mapping
- `v84/80_shell_dispatch.inc.c`
  - command table
  - command lookup
  - busy gate
  - `last_result`
  - protocol sequence counter
  - `execute_shell_command()`
  - `shell_loop()`
- `a90_console.c`
  - actual serial write/printf/readline
  - no protocol parsing
- `a90ctl.py` / `native_init_flash.py`
  - unchanged, but validation must prove v84 emits the same parseable `A90P1` records

## Implementation Steps

1. Copy v83 sources to v84.
   - `init_v83.c` -> `init_v84.c`
   - `v83/` -> `v84/`
2. Bump version constants.
   - `INIT_VERSION` -> `0.8.15`
   - `INIT_BUILD` -> `v84`
   - boot marker -> `A90v84`
   - changelog entry -> `0.8.15 v84 CMDPROTO API`
3. Add `a90_cmdproto.c/h`.
   - Depend on `a90_console.h`, `a90_util.h`, standard C headers.
   - Avoid depending on shell command table or menu state.
4. Move decode helpers.
   - From `v83/50_boot_services.inc.c`: `hex_digit_value()`, `parse_cmdv1x_token()`, `decode_cmdv1x_args()`
   - Into `a90_cmdproto.c`: renamed `a90_cmdproto_decode_v1x()`
5. Move frame helpers.
   - From `v83/80_shell_dispatch.inc.c`: `shell_protocol_status()`, `shell_protocol_begin()`, `shell_protocol_end()`
   - Into `a90_cmdproto.c`: renamed `a90_cmdproto_status()`, `a90_cmdproto_begin()`, `a90_cmdproto_end()`
6. Keep shell ownership stable.
   - `shell_protocol_seq` stays in `v84/80_shell_dispatch.inc.c`.
   - `save_last_result()` stays in `v84/80_shell_dispatch.inc.c`.
   - `print_cmdv1x_error()` may stay in shell if it owns `last_result`, but it must call cmdproto frame helpers.
7. Update `init_v84.c` build instructions and docs.

## Validation

### Local Build

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v84 \
  stage3/linux_init/init_v84.c \
  stage3/linux_init/a90_util.c \
  stage3/linux_init/a90_log.c \
  stage3/linux_init/a90_timeline.c \
  stage3/linux_init/a90_console.c \
  stage3/linux_init/a90_cmdproto.c
```

Check markers:

```bash
strings stage3/linux_init/init_v84 | rg 'A90 Linux init 0.8.15|A90v84|0.8.15 v84 CMDPROTO API'
sha256sum stage3/linux_init/init_v84 stage3/ramdisk_v84.cpio stage3/boot_linux_v84.img
```

### Static Checks

```bash
git diff --check
python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py
```

### Device Validation

```bash
python3 scripts/revalidation/native_init_flash.py stage3/boot_linux_v84.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.15 (v84)" \
  --verify-protocol auto \
  --recovery-timeout 180 \
  --bridge-timeout 240
```

Bridge and protocol checks:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py --json status
python3 scripts/revalidation/a90ctl.py 'echo hello world'
python3 scripts/revalidation/a90ctl.py 'logpath'
python3 scripts/revalidation/a90ctl.py 'timeline'
python3 scripts/revalidation/a90ctl.py 'bootstatus'
python3 scripts/revalidation/a90ctl.py 'storage'
python3 scripts/revalidation/a90ctl.py 'mountsd status'
python3 scripts/revalidation/a90ctl.py 'displaytest safe'
python3 scripts/revalidation/a90ctl.py 'autohud 2'
```

Regression checks:

- `cmdv1 version` emits `A90P1 BEGIN` and `A90P1 END` with `status=ok`.
- `cmdv1 does-not-exist` emits `status=unknown`.
- menu-active blocked command emits `status=busy`.
- malformed `cmdv1x` emits one framed error result, not a raw partial line.
- `cmdv1x` with spaces in argv still reaches the intended command.
- `run /bin/a90sleep 1`, `cpustress 3 2`, `watchhud 1 2`, q cancel, `reattach`, `usbacmreset` remain working.

## Acceptance Criteria

- `a90_cmdproto.c/h` owns protocol parsing/framing without direct command table knowledge.
- `v84/80_shell_dispatch.inc.c` no longer contains raw `A90P1 BEGIN/END` formatting helpers.
- `v84/50_boot_services.inc.c` no longer contains `cmdv1x` hex/token decoder helpers.
- Host tools parse v84 framed output exactly as they parsed v83.
- 실기 flash 후 `cmdv1 version/status`, storage, display, console cancel regression이 모두 PASS다.

## Risks

- `cmdv1x` decode buffer lifetime이 짧으면 decoded argv가 command 실행 중 깨질 수 있다.
- frame helper가 shell result 저장과 섞이면 `cmdproto -> shell` 의존이 생긴다.
- malformed `cmdv1x` error path에서 `A90P1 END`가 누락되면 `a90ctl.py`가 timeout으로 보일 수 있다.
- protocol sequence counter를 cmdproto로 이동하면 shell과 error path의 ordering drift가 생길 수 있으므로 v84에서는 shell에 남긴다.

## Next After v84

- v85: `run`, timeout, cancel, zombie reap, `netservice`/long-running helper를 service 관리 계층으로 정리한다.
- v86: KMS/draw/HUD/input/menu를 UI 계층으로 분리한다.
- 이후: `helpers/a90_cpustress` 외부 프로세스화, BusyBox/dropbear, SD workspace helper 운영 정책을 검토한다.

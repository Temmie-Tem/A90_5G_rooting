# v100 계획: Remote Shell Prototype

Date: `2026-05-03`

## Summary

- v100은 `A90 Linux init 0.9.0 (v100)` / `0.9.0 v100 REMOTE SHELL`로 진행한다.
- 기준은 v99 verified: SD runtime root, helper inventory, static BusyBox/toybox userland, USB NCM/tcpctl, serial bridge rescue가 모두 확인된 상태다.
- 1차 구현은 **custom TCP shell helper 우선**으로 한다. Dropbear SSH는 더 안전한 인증/PTY/host-key 조건을 충족한 뒤 v101+ 또는 별도 후보로 재평가한다.
- 기본 정책은 **disabled by default**, **NCM-only**, **explicit enable**, **serial ACM rescue 유지**, **no Wi-Fi exposure**다.

## Why Custom TCP Shell First

Dropbear는 장기적으로 더 올바른 SSH 경로지만 v100에서 바로 올리기에는 다음 선행 조건이 부족하다.

- SSH host key 생성/보존 위치와 권한 정책이 아직 정해지지 않았다.
- `authorized_keys`, root login, password disable, forced command, port forwarding disable 등 인증 정책을 먼저 고정해야 한다.
- PTY, `/dev/pts`, environment, login shell 경로가 아직 native init runtime contract에 포함되지 않았다.
- 문제가 생겼을 때 디버깅 범위가 Dropbear 자체, crypto, key format, shell environment까지 커진다.

반면 custom TCP shell은 기존 `a90_tcpctl`, `a90_run`, `a90_service`, `a90_userland`, USB NCM 검증 위에 얇게 붙일 수 있다. v100에서는 이것으로 remote shell UX와 lifecycle만 먼저 검증하고, Dropbear는 다음 단계에서 보안/키/PTY 요구사항이 충족될 때 승격한다.

## Reference Notes

- Dropbear 공식 페이지: https://matt.ucc.asn.au/dropbear/dropbear.html
- Dropbear manpage 기준점:
  - `-p [address:]port`로 listen 주소/포트 지정 가능.
  - `-F`, `-E`, `-P`로 foreground/log/pidfile 운영 가능.
  - `-s`, `-g`, `-w`, `-j`, `-k`, `-I`로 password/root/forwarding/idle 정책을 제한 가능.
  - `authorized_keys`와 `~/.ssh` 권한이 느슨하면 public key login을 거부한다.
- BusyBox 공식 페이지는 embedded multi-call userland 기준점이며, v99에서 BusyBox 1.36.1 static ARM64 실행을 확인했다: https://www.busybox.net/
- netcat 계열은 TCP 연결 테스트에는 유용하지만 인증 없는 `nc -e sh` 스타일은 v100 기본 구현으로 사용하지 않는다.

## Target Architecture

```text
host
  -> USB NCM 192.168.7.1/24
    -> device ncm0 192.168.7.2
      -> a90_rshell helper :2326
        -> BusyBox sh -i or command loop
          -> SD runtime root /mnt/sdext/a90

serial ACM bridge remains rescue/control channel
```

## Key Changes

### Version And Source

- v99를 복사해 `stage3/linux_init/init_v100.c`와 `stage3/linux_init/v100/*.inc.c`를 만든다.
- `a90_config.h` version/build/marker를 다음으로 갱신한다.
  - `INIT_VERSION "0.9.0"`
  - `INIT_BUILD "v100"`
  - `0.9.0 v100 REMOTE SHELL`
- ABOUT/changelog/menu detail에 `0.9.0 v100 REMOTE SHELL` 항목을 추가한다.

### New Helper

- `stage3/linux_init/helpers/a90_rshell.c`를 추가한다.
- 빌드 산출물은 optional SD helper로 배치한다.
  - preferred: `/mnt/sdext/a90/bin/a90_rshell`
  - fallback candidate: `/cache/bin/a90_rshell`
- helper role은 `remote-shell`로 `a90_helper` inventory에 등록한다.

### Remote Shell Modes

v100은 두 mode 중 하나 또는 둘 다를 단계적으로 검증한다.

1. **exec mode**
   - TCP line protocol로 명령 한 줄을 받아 BusyBox `sh -c <line>` 실행.
   - stdout/stderr를 socket으로 반환하고 종료 코드를 명시한다.
   - interactive TTY가 없어도 안정적으로 검증 가능하다.
2. **interactive mode**
   - BusyBox `sh -i`를 socket stdio에 연결.
   - PTY 없이 동작 가능한 범위만 v100에서 확인한다.
   - line editing/job control/TTY signal은 v100 성공 기준에서 제외한다.

권장 구현 순서는 `exec mode` 먼저, 그 다음 `interactive mode` opt-in이다.

### Shell Commands

- `rshell [status|start|stop|enable|disable|token|rotate-token]`
  - `status`: enabled flag, helper presence, NCM state, pid, port, token state 출력.
  - `start`: netservice/NCM 준비 후 `a90_rshell` 시작.
  - `stop`: helper 종료, NCM은 사용자가 별도로 stop하지 않는 한 유지.
  - `enable`: `/mnt/sdext/a90/state/remote-shell.enabled` 또는 `/cache` fallback flag 생성 후 start.
  - `disable`: flag 제거 후 stop.
  - `token`: 현재 token file 존재/권한/길이 상태만 표시하고 값은 기본 출력하지 않음.
  - `rotate-token`: 새 token 생성 또는 host-provided token 입력 방식은 계획 중 선택.
- `status`, `bootstatus`, `selftest verbose`, network menu에 remote shell 요약을 추가한다.

### Host Tooling

- `scripts/revalidation/rshell_host.py` 추가.
- 후보 명령:
  - `status`: serial bridge로 `rshell status`, NCM ping, TCP port open 여부 확인.
  - `start`: serial bridge로 `rshell start`, host NCM 설정, port connect 확인.
  - `exec <cmd>`: token auth 후 one-shot command 실행.
  - `smoke`: `echo`, `uname`, `busybox sh -c`, exit-code check.
  - `stop`: serial bridge로 `rshell stop`.
- 기존 `ncm_host_setup.py`와 `tcpctl_host.py`를 참고하되, 인증/token handling은 별도 명확히 둔다.

### Service Tracking

- 새 service id 후보: `A90_SERVICE_RSHELL`.
- `a90_service`가 helper pid를 추적한다.
- `a90_run` process-group stop을 사용해 helper와 child shell을 함께 종료한다.
- stale pid reap은 `rshell status`와 `status`에서 수행한다.

### Security Policy

- 기본값은 disabled다.
- listen address는 `192.168.7.2` 또는 `ncm0`로 제한한다.
- Wi-Fi, cellular, all-interface bind 금지.
- token 없이는 start 실패 또는 connection refuse를 기본 정책으로 한다.
- token file 권한은 `0600`, runtime root owner 기준으로 제한한다.
- host token 출력은 명시 요청일 때만 허용하고, 일반 `status`에는 token value를 표시하지 않는다.
- v100에서는 password login, telnetd, unauthenticated `nc -e sh`를 구현하지 않는다.
- Dropbear를 실험하더라도 password login disabled, root password disabled, forwarding disabled, NCM-only bind가 기본 조건이다.

## Non-Goals

- Wi-Fi remote shell.
- internet-facing service.
- SSH를 기본 enabled로 만드는 것.
- Dropbear를 latest verified로 승격.
- PTY/job-control 완전 구현.
- Android userspace login/session 재구현.
- package manager 또는 distro bootstrap.

## Implementation Steps

1. v99 → v100 source copy and version marker update.
2. `a90_rshell.c` helper scaffold: TCP bind/listen, single-client accept, idle timeout, clean shutdown.
3. `a90_run`/`a90_service` integration for `A90_SERVICE_RSHELL`.
4. `a90_helper` inventory에 `a90_rshell` optional helper 추가.
5. `rshell` shell command and status summaries 추가.
6. Host `rshell_host.py` 작성.
7. Local static build and helper build.
8. Boot image build and real-device flash.
9. NCM setup, `rshell smoke`, serial rescue regression, stop/disable rollback.
10. Report/latest docs update after real-device PASS only.

## Test Plan

### Local Build

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/helpers/a90_rshell \
  stage3/linux_init/helpers/a90_rshell.c
```

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v100 \
  stage3/linux_init/init_v100.c \
  stage3/linux_init/a90_util.c \
  stage3/linux_init/a90_log.c \
  stage3/linux_init/a90_timeline.c \
  stage3/linux_init/a90_console.c \
  stage3/linux_init/a90_cmdproto.c \
  stage3/linux_init/a90_run.c \
  stage3/linux_init/a90_service.c \
  stage3/linux_init/a90_kms.c \
  stage3/linux_init/a90_draw.c \
  stage3/linux_init/a90_input.c \
  stage3/linux_init/a90_hud.c \
  stage3/linux_init/a90_menu.c \
  stage3/linux_init/a90_metrics.c \
  stage3/linux_init/a90_shell.c \
  stage3/linux_init/a90_controller.c \
  stage3/linux_init/a90_storage.c \
  stage3/linux_init/a90_selftest.c \
  stage3/linux_init/a90_usb_gadget.c \
  stage3/linux_init/a90_netservice.c \
  stage3/linux_init/a90_runtime.c \
  stage3/linux_init/a90_helper.c \
  stage3/linux_init/a90_userland.c
```

- `strings` 확인:
  - `A90 Linux init 0.9.0 (v100)`
  - `A90v100`
  - `0.9.0 v100 REMOTE SHELL`

### Static Checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/ncm_host_setup.py \
  scripts/revalidation/tcpctl_host.py \
  scripts/revalidation/rshell_host.py
```

### Device Validation

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v100.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.0 (v100)" \
  --verify-protocol auto
```

Baseline regression:

```bash
python3 scripts/revalidation/a90ctl.py version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py selftest verbose
python3 scripts/revalidation/a90ctl.py runtime
python3 scripts/revalidation/a90ctl.py helpers verbose
python3 scripts/revalidation/a90ctl.py userland verbose
python3 scripts/revalidation/a90ctl.py storage
python3 scripts/revalidation/a90ctl.py 'mountsd status'
python3 scripts/revalidation/a90ctl.py statushud
python3 scripts/revalidation/a90ctl.py 'autohud 2'
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
```

Remote shell validation:

```bash
python3 scripts/revalidation/a90ctl.py 'rshell status'
python3 scripts/revalidation/a90ctl.py 'rshell start'
python3 scripts/revalidation/ncm_host_setup.py setup
python3 scripts/revalidation/rshell_host.py smoke
python3 scripts/revalidation/rshell_host.py exec 'echo A90_RSHELL_OK'
python3 scripts/revalidation/rshell_host.py exec 'busybox uname -a'
python3 scripts/revalidation/a90ctl.py 'rshell stop'
python3 scripts/revalidation/a90ctl.py 'rshell disable'
python3 scripts/revalidation/a90ctl.py 'netservice status'
```

Rescue/regression:

- serial ACM bridge must still answer `version/status` while remote shell is enabled.
- `screenmenu` nonblocking behavior remains intact.
- `netservice stop/start` does not leave stale `a90_rshell` children.
- physical or software USB reconnect does not leave remote shell enabled unexpectedly.
- `selftest` remains `FAIL=0`; remote shell missing/disabled is warning-only or status-only unless explicitly enabled.

## Acceptance

- v100 boots and reports `A90 Linux init 0.9.0 (v100)`.
- Remote shell remains disabled by default.
- Explicit `rshell start` works only when NCM path is available and token policy is satisfied.
- Host can run at least `echo`, `uname`, and BusyBox shell command through the remote shell path.
- `rshell stop/disable` returns to serial-only or netservice-only safe state without orphan child processes.
- ACM serial bridge remains the primary rescue channel throughout.
- README/latest verified/report/task queue are updated only after real-device flash and regression PASS.

## Deferred

- Dropbear static build and key management.
- `/dev/pts` and PTY-backed interactive SSH/session support.
- SSH authorized_keys setup UI.
- service manager integration beyond minimal `A90_SERVICE_RSHELL` tracking.
- Wi-Fi exposure or Wi-Fi remote access.

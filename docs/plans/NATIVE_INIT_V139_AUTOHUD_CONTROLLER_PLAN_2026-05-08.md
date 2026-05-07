# v139 Plan: Auto-HUD/Menu Controller Cleanup

기준 버전: `A90 Linux init 0.9.38 (v138)`
목표 버전: `A90 Linux init 0.9.39 (v139)`
Marker: `0.9.39 v139 AUTOHUD CONTROLLER`

## Summary

v139는 기능 추가가 아니라 `auto_hud_loop()` 주변의 controller/state
정리 버전이다. v138에서 integrated validation, quick soak, RC soak가 모두
통과했으므로, 가장 큰 남은 UI/controller hotspot인
`stage3/linux_init/v138/40_menu_apps.inc.c`를 안전하게 작게 정리한다.

목표는 `screenmenu`, `hide`, `autohud`, ABOUT/changelog, displaytest,
inputmonitor, CPU stress 앱의 UX를 유지하면서 auto-HUD child가 가진 상태 전환
책임을 명확히 나누는 것이다.

## Current Problem

`40_menu_apps.inc.c`는 여전히 auto-HUD loop, menu request consume, menu/app
rendering, hold-repeat timer, physical button gesture routing, app transition,
CPU stress screen state를 한 파일에서 조합한다. 이 구조는 지금 동작하지만,
다음 문제가 있다.

- menu visible 상태와 controller busy gate 상태를 맞추는 코드가 여러 곳에
  반복된다.
- `active_app`, `menu_active`, ABOUT page index, hold timer, stress pid 같은
  상태가 한 loop 안에서 직접 변경된다.
- `screenmenu` nonblocking UX, `hide` 복구, long-hold repeat, app back transition
  회귀를 한눈에 추적하기 어렵다.
- v138 RC soak는 통과했지만, 이 파일이 이후 UI 기능 추가의 가장 큰 변경 위험
  지점으로 남아 있다.

## Scope

v139 범위는 "얇은 controller cleanup"으로 고정한다.

- v138을 복사해 `init_v139.c`와 `v139/*.inc.c`를 만든다.
- `a90_config.h`, kmsg marker, ABOUT/changelog를 `0.9.39` / `v139`로 올린다.
- `v139/40_menu_apps.inc.c` 안에 작은 state/helper 경계를 만든다.
- 기존 module API (`a90_controller`, `a90_menu`, `a90_input`, `a90_hud`)의 의미는
  바꾸지 않는다.
- 새 사용자 기능은 추가하지 않는다.

## Key Changes

### 1. Auto-HUD state 구조화

`auto_hud_loop()` 지역 상태를 `struct auto_hud_state` 또는 동등한 include-local
구조로 모은다.

후보 필드:

- `bool menu_active`
- `enum screen_app_id active_app`
- `struct a90_menu_state menu_state`
- `size_t about_changelog_index`
- `size_t about_page_index`
- `pid_t stress_pid`
- `long stress_end_ms`
- `unsigned int menu_hold_code`
- `long menu_hold_next_ms`

이 구조는 v139 include tree 내부 구현 세부로 두고, 별도 public API로 노출하지
않는다.

### 2. 반복 상태 전환 helper 추가

다음 전환은 helper로 묶는다.

- `auto_hud_state_init()`
- `auto_hud_show_menu()`
- `auto_hud_hide_menu()`
- `auto_hud_enter_app(app)`
- `auto_hud_leave_app_to_menu()`
- `auto_hud_reset_hold_timer()`
- `auto_hud_arm_hold_timer(code)`

핵심 기준:

- menu visible 상태가 바뀌는 곳은 항상 `a90_controller_set_menu_active()`와
  함께 움직인다.
- app 전환이나 hide/back 전환에서는 hold timer를 항상 정리한다.
- ABOUT/changelog page index 초기화 규칙을 한 곳으로 모은다.

### 3. Loop 단계 helper 분리

`auto_hud_loop()`를 아래 흐름으로 읽히게 정리한다.

1. request consume
2. service/app progress update
3. current screen draw
4. poll timeout 계산
5. timeout 처리
6. input event 처리
7. gesture/action dispatch

후보 helper:

- `auto_hud_apply_pending_request()`
- `auto_hud_update_background_tasks()`
- `auto_hud_draw_current_screen()`
- `auto_hud_compute_poll_timeout()`
- `auto_hud_handle_poll_timeout()`
- `auto_hud_handle_key_event()`
- `auto_hud_handle_menu_action()`
- `auto_hud_handle_app_gesture()`

### 4. Security/availability regression guard 유지

v131/v132 이후 확인한 hold-repeat timer와 menu busy policy 회귀를 유지한다.

- repeat action을 소비하지 못하는 화면에서는 hold timer가 spin하지 않아야 한다.
- `mountsd` bare command는 menu-visible 상태에서 side effect로 허용되면 안 된다.
- `screenmenu`는 shell을 점유하지 않고 즉시 반환해야 한다.
- `hide`/`hidemenu`/`resume`은 menu visible 상태와 무관하게 복구 명령으로
  동작해야 한다.

## Non-goals

- `a90_menu.c/h` public API 재설계
- displaytest/cutoutcal/about/inputmonitor app renderer 분리
- shell command table 이동
- network-facing 기능 추가
- Wi-Fi bring-up
- storage/netservice 정책 변경
- `screenmenu`/`blindmenu` UX 변경

## Test Plan

### Local build

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v139 \
  stage3/linux_init/init_v139.c \
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
  stage3/linux_init/a90_pid1_guard.c \
  stage3/linux_init/a90_runtime.c \
  stage3/linux_init/a90_helper.c \
  stage3/linux_init/a90_userland.c \
  stage3/linux_init/a90_diag.c \
  stage3/linux_init/a90_exposure.c \
  stage3/linux_init/a90_wifiinv.c \
  stage3/linux_init/a90_wififeas.c \
  stage3/linux_init/a90_changelog.c \
  stage3/linux_init/a90_app_about.c \
  stage3/linux_init/a90_app_displaytest.c \
  stage3/linux_init/a90_app_inputmon.c
```

확인:

```bash
strings stage3/linux_init/init_v139 | rg 'A90 Linux init 0.9.39|A90v139|0.9.39 v139 AUTOHUD CONTROLLER'
```

### Static checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/native_integrated_validate.py \
  scripts/revalidation/native_soak_validate.py \
  scripts/revalidation/native_rc_soak.py
rg 'A90v138|0\.9\.38|init_v138|v138/|_v138' \
  stage3/linux_init/init_v139.c \
  stage3/linux_init/v139 \
  stage3/linux_init/a90_config.h
```

### Device validation

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v139.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.39 (v139)" \
  --verify-protocol auto

python3 scripts/revalidation/a90ctl.py version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py selftest verbose
python3 scripts/revalidation/a90ctl.py exposure guard
python3 scripts/revalidation/a90ctl.py policycheck run
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/a90ctl.py 'autohud 2'
python3 scripts/revalidation/a90ctl.py statushud
python3 scripts/revalidation/a90ctl.py 'displaytest safe'
python3 scripts/revalidation/a90ctl.py cutoutcal
python3 scripts/revalidation/a90ctl.py 'inputmonitor 0'
```

### Host harness

```bash
python3 scripts/revalidation/native_integrated_validate.py \
  --expect-version "A90 Linux init 0.9.39 (v139)"

python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --expect-version "A90 Linux init 0.9.39 (v139)"

python3 scripts/revalidation/native_rc_soak.py \
  --cycles 3 \
  --expect-version "A90 Linux init 0.9.39 (v139)"
```

### Manual physical regression

- VOL+/VOL-/POWER 단일 입력으로 menu 이동/선택 확인
- VOL+/VOL- long hold repeat 확인
- VOL+DN physical back shortcut 확인
- ABOUT/changelog series/page 이동 확인
- menu visible 상태에서 `status`, `logpath`, `timeline`, `storage` 응답 확인
- power page active 상태에서 dangerous command busy gate 확인

## Acceptance

- v139 boots as `A90 Linux init 0.9.39 (v139)`.
- `screenmenu` remains nonblocking and returns framed `rc=0`.
- `hide` clears menu-active state before storage/userland validation commands.
- Long-hold repeat does not spin on screens that cannot consume repeat steps.
- `native_integrated_validate.py`, quick soak, and RC soak all pass.
- Local targeted security rescan has no `FAIL`.
- `v139/40_menu_apps.inc.c` has clearer controller/state boundaries without
  changing user-visible behavior.

## Follow-up

- If v139 passes, the next candidates are:
  - network-facing decision after fresh cloud scan;
  - deeper app renderer split only if `40_menu_apps.inc.c` remains too large;
  - longer RC soak such as `native_rc_soak.py --cycles 10` before larger network
    changes.

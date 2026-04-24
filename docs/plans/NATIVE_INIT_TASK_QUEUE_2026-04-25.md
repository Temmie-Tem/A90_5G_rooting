# Native Init Task Queue (2026-04-25)

이 문서는 `A90 Linux init v44` 이후 바로 실행할 작업 큐다.
큰 방향은 “보이는 부팅 → 복구 가능한 로그 → 단독 조작 → 작은 userland” 순서다.

## 현재 고정 기준점

- latest native init: `A90 Linux init v44`
- latest source: `stage3/linux_init/init_v44.c`
- latest boot image: `stage3/boot_linux_v44.img`
- control channel: USB ACM serial bridge
- log: `/cache/native-init.log`
- verified:
  - shell result/errno/duration
  - boot/command file log
  - blocking command q/Ctrl-C cancel
  - boot readiness timeline
  - HUD boot summary
  - KMS HUD
  - VOL+/VOL-/POWER input

## 실행 큐

### V43. Boot Readiness Timeline — 완료

목표:

- 부팅 중 리소스가 언제 준비되는지 자동 기록한다.
- 화면/serial이 없어도 `/cache/native-init.log`로 원인을 추적할 수 있게 한다.

구현:

- boot step enum 또는 helper 추가
- 각 단계의 monotonic timestamp 기록
- `timeline` shell 명령 추가
- `/cache/native-init.log`에 동일 정보 기록

검증:

- `timeline` — PASS
- `logcat` replay — PASS
- `status` — PASS
- recovery 왕복 후 `/cache/native-init.log` 보존 확인은 별도 항목으로 유지

### V44. HUD Boot Progress/Error — 완료

목표:

- 부팅 화면에서 현재 단계와 마지막 에러를 직접 보이게 한다.

구현:

- boot timeline 정보를 HUD 상단/하단에 요약 표시
- 마지막 command result 또는 boot error를 짧게 표시
- 실패 시 검은 화면/정지처럼 보이지 않도록 error card 표시

검증:

- 정상 부팅 HUD에 `BOOT OK` 또는 현재 step 표시 — PASS
- `bootstatus`, `status`, `statushud`, `autohud 2` — PASS
- 고의 실패 가능한 display/sysfs 명령 후 HUD 복구 확인 — 보류

### V45. Log Preservation + Run Cancel Test

목표:

- `/cache/native-init.log`가 recovery 왕복 후 보존되는지 확인한다.
- `run` cancelable child wait를 실기 검증한다.

구현/준비:

- `/cache/bin` 또는 ramdisk에 안전한 static helper 준비
- long-running helper 실행 후 q/Ctrl-C cancel 확인
- recovery 재부팅 후 `cat /cache/native-init.log` 확인

검증:

- `run /cache/bin/<helper>` + q
- `last`
- `logcat`
- TWRP 왕복 후 log 보존

### V46. Safe Storage / Device Map Report

목표:

- 쓰기 가능한 안전 영역과 건드리면 안 되는 영역을 명확히 분리한다.

확인:

- `/cache`
- `/tmp`
- `/mnt/system` read-only
- `/data`는 보류
- `/efs`, modem, RPMB, keymaster 계열은 금지

산출:

- `docs/reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md`

### V47. On-screen Menu Draft

목표:

- serial 없이도 화면과 버튼만으로 최소 조작이 가능하게 한다.

구현:

- HUD 기반 menu 표시
- VOL+/VOL-/POWER 선택
- status/log/recovery/reboot/poweroff 우선

검증:

- 버튼 이동/선택
- safe default resume
- recovery 진입

## 보류 큐

- ADB 안정화 재검토
- USB RNDIS/NCM network
- dropbear SSH
- BusyBox/static userland 묶음
- Android framework 복구 시도

## 지금 바로 진행할 항목

1. V45 Log Preservation + Run Cancel Test
2. V46 Safe Storage / Device Map Report
3. V47 On-screen Menu Draft

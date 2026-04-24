# Samsung Galaxy A90 5G Native Init Workspace

이 저장소는 `Samsung Galaxy A90 5G (SM-A908N)`의 stock Android Linux kernel 위에서
Android userspace 대신 직접 만든 static `/init`를 실행하고,
그 위에 작은 Linux userspace/runtime을 쌓아 가는 실험 작업 공간입니다.

초기 목표였던 `native Linux rechallenge`의 핵심 진입점 확보 단계는 통과했고,
현재 프로젝트의 중심은 **Android kernel 기반 native init 환경을 안정화하고
서버형 임베디드 Linux 콘솔로 확장하는 것**입니다.

## Current State

- device: `SM-A908N`
- build: `A908NKSU5EWA3`
- kernel: Samsung stock Android kernel `Linux 4.14.190`
- recovery: TWRP 사용 가능
- latest native init: `A90 Linux init v45`
- latest source: `stage3/linux_init/init_v45.c`
- latest boot image: `stage3/boot_linux_v45.img`
- control channel: USB CDC ACM serial (`/dev/ttyGS0` ↔ `/dev/ttyACM0`)
- host bridge: `scripts/revalidation/serial_tcp_bridge.py --port 54321`
- display: KMS TEST pattern 후 상태 HUD 자동 전환
- input: VOL+/VOL-/POWER 버튼 입력 확인
- logging: `/cache/native-init.log` boot/command log 확인
- blocking cancel: `waitkey`/`readinput`/`watchhud`/`blindmenu` q/Ctrl-C 취소 확인
- boot timeline: `timeline` 명령과 log replay 확인
- HUD boot summary: `BOOT OK shell` 표시 확인
- run cancel: `/bin/a90sleep` helper로 q 취소 확인
- ADB: 보류. 현재 기준 제어 채널은 serial bridge

## Current Objective

현재 메인 목표는 `stock Android kernel 위의 자체 native userspace`를 만드는 것입니다.

구조는 다음과 같습니다.

```text
Samsung bootloader
  -> stock Android Linux kernel
    -> custom static /init (PID 1)
      -> serial shell
      -> display HUD
      -> input/button handling
      -> sensor/sysfs reader
      -> logging/runtime layer
      -> optional BusyBox/network/SSH layer
```

즉 이 프로젝트는 더 이상 단순히 “Linux 진입이 가능한가?”를 확인하는 단계가 아니라,
확보한 진입점을 기반으로 **반복 운용 가능한 최소 Linux 콘솔/서버 환경**을 만드는 단계입니다.

## What This Is

- Android kernel과 Samsung vendor driver를 그대로 활용하는 native userspace 실험
- boot ramdisk의 `/init`를 교체해 PID 1부터 직접 구성하는 작업
- USB serial, KMS display, input, battery/thermal sysfs를 사용하는 임베디드 콘솔
- 장기적으로 BusyBox, USB network, dropbear SSH 같은 서버형 구성으로 확장할 수 있는 기반

## What This Is Not

- 일반 Debian/Ubuntu/Red Hat 배포판 포팅 완료 상태가 아님
- Android framework, 앱, SurfaceFlinger, Zygote를 복구하는 프로젝트가 아님
- 커널 교체나 커널 드라이버 개발이 현재 목표가 아님
- 카메라, 모뎀, GPU 가속 등 vendor userspace 의존 기능을 즉시 지원하는 환경이 아님

## Near-Term Roadmap

1. shell result/return code를 신뢰 가능하게 정리 — v40 완료
2. `/cache/native-init.log` 기반 boot/command 로그 추가 — v41 완료
3. blocking command 취소 정책 통일 — v42 완료
4. boot readiness timeline 자동 기록 — v43 완료
5. HUD에 boot progress/error 상태 표시 — v44 완료
6. recovery log preservation + `run` cancel helper — v45 완료
7. 버튼 기반 on-screen menu 초안 구현
8. safe storage/device/sysfs map 문서화
9. BusyBox와 USB network/SSH 가능성 검토

## Repository Layout

- `docs/`
  현재 문서 인덱스, 프로젝트 상태, v39/v40/v41/v42 상태 보고서, 다음 작업 목록
- `stage3/`
  native init 소스, 빌드 산출물, boot image 실험 파일
- `scripts/`
  serial bridge, console, revalidation helper
- `firmware/`
  stock firmware, patched AP, TWRP 이미지
- `mkbootimg/`
  boot/recovery/vendor_boot 분석과 repack에 쓰는 도구
- `backups/`
  known-good boot/recovery/vbmeta 등 복구 기준점

## Active Documents

- `docs/overview/PROJECT_STATUS.md`
- `docs/reports/NATIVE_INIT_V42_CANCEL_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V43_TIMELINE_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V44_HUD_BOOT_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V45_RUN_LOG_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V41_LOGGING_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V39_STATUS_2026-04-25.md`
- `docs/plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md`
- `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md`
- `docs/overview/PROGRESS_LOG.md`
- `docs/plans/NATIVE_LINUX_RECHALLENGE_PLAN.md`
- `docs/plans/REVALIDATION_PLAN.md`
- `docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md`

이 중 `NATIVE_LINUX_RECHALLENGE_PLAN.md`와 `REVALIDATION_PLAN.md`는
진입점 확보 이전의 부트체인 재검증 기록으로 남기고,
현재 진행 기준은 `NATIVE_INIT_NEXT_WORK_2026-04-25.md`를 따른다.

## Working Rules

- known-good boot image와 TWRP recovery 복구 경로를 항상 유지한다.
- 한 번에 하나의 boot/init 변수만 바꾼다.
- 새 boot image는 version, source path, SHA256, 실기 관찰 결과를 기록한다.
- USB ACM serial bridge를 기준 제어 채널로 사용한다.
- `/efs`, modem, RPMB, keymaster, keystore, bootloader 계열에는 쓰기 작업을 하지 않는다.
- `/data` 암호화 영역은 명확한 목적과 복구 계획 없이는 건드리지 않는다.
- 로그와 실험 산출물은 우선 `/cache` 또는 repo 문서에 남긴다.
- ADB 안정화는 후순위로 두고, serial/HUD/log/menu 안정화를 먼저 진행한다.

## Safety Note

이 저장소에는 실제 플래시 대상 바이너리와 Samsung 전용 이미지가 포함될 수 있습니다.
실험 전에는 항상 현재 boot/recovery/vbmeta 상태와 복구 가능한 known-good 이미지를
확인한 뒤 진행합니다.

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
- latest verified build: `A90 Linux init 0.8.12 (v81)`
- official version: `0.8.12`
- build tag: `v81`
- creator: `made by temmie0214`
- latest verified source: `stage3/linux_init/init_v81.c` + `stage3/linux_init/v81/*.inc.c` + `stage3/linux_init/a90_config.h` + `stage3/linux_init/a90_util.c/h`
- latest verified boot image: `stage3/boot_linux_v81.img`
- previous verified source-layout baseline: `stage3/linux_init/init_v80.c` + `stage3/linux_init/v80/*.inc.c`
- known-good fallback: `stage3/boot_linux_v48.img`
- control channel: USB CDC ACM serial (`/dev/ttyGS0` ↔ `/dev/ttyACM0`)
- host bridge: `scripts/revalidation/serial_tcp_bridge.py --port 54321`
- display: custom boot splash 후 상태 HUD/menu 자동 전환
- input: VOL+/VOL-/POWER 단일/더블/롱/조합 입력 layout과 input monitor 확인
- logging: SD 정상 시 `/mnt/sdext/a90/logs/native-init.log`, fallback 시 `/cache/native-init.log`
- blocking cancel: `waitkey`/`readinput`/`watchhud`/`blindmenu` q/Ctrl-C 취소 확인
- boot timeline: `timeline` 명령과 log replay 확인
- HUD boot summary: `BOOT OK shell` 표시 확인
- run cancel: `/bin/a90sleep` helper로 q 취소 확인
- storage: `/cache` safe write, ext4 SD workspace `/mnt/sdext/a90`, critical partitions do-not-touch
- screen menu: 자동 메뉴, 앱 폴더, CPU stress app, serial `hide`/busy gate 확인
- USB map: ACM-only gadget `04e8:6861` / host `cdc_acm` 기준 문서화
- userland: `toybox 0.8.13` static ARM64 build와 `/cache/bin/toybox` 실기 실행 확인
- USB reattach: v48에서 ACM rebind 후 serial console 재연결 확인
- USB NCM: persistent composite, device `ncm0`, IPv4 ping, IPv6 link-local ping, host→device netcat 확인
- NCM ops: host interface 자동 탐지, ping, static TCP nettest 양방향 payload 검증 완료
- TCP control: NCM 위에서 `a90_tcpctl` ping/status/run/shutdown 검증 완료
- TCP wrapper: `tcpctl_host.py smoke`로 launch/client/stop 자동 검증 완료
- TCP soak: `tcpctl_host.py soak` 5분/30사이클 안정성 검증 완료
- physical USB reconnect: 실제 케이블 unplug/replug 후 ACM bridge, NCM ping, tcpctl 복구 확인
- serial noise: unsolicited `AT` modem probe line 무시 확인
- boot netservice: `/cache/native-init-netservice` opt-in flag 기반 NCM/tcpctl 부팅 자동 시작 검증 완료
- reconnect: v60 `netservice stop/start` software UDC 재열거 후 NCM/TCP 복구 확인
- HUD metrics: CPU/GPU 온도와 사용률 `%` 표시, CPU stress 검증 확인
- dev nodes: `/dev/null`/`/dev/zero` boot-time char device guard 확인
- app menu: APPS/MONITORING/TOOLS/LOGS/NETWORK/POWER 계층 메뉴, CPU stress, input monitor 확인
- boot splash: TEST 패턴 대신 `A90 NATIVE INIT` custom splash 표시 후 HUD 전환 확인
- splash layout: v65에서 긴 문구/footer 잘림 방지를 위해 안전 여백과 자동 축소 적용
- display test: v77에서 color/font/safe-area/layout preview 4페이지로 분리, `cutoutcal` 펀치홀 보정 추가
- SD workspace: `mountsd [status|ro|rw|off|init]`로 ext4 SD `/mnt/sdext/a90` 운영 검증
- boot storage: v79에서 SD boot health check 후 정상 SD는 main runtime storage, 실패 시 `/cache` fallback
- source layout: v80에서 PID1 source를 기능별 include module로 분리
- base modules: v81에서 `a90_config.h`와 `a90_util.c/h`를 실제 `.c/.h` API로 분리
- about app: `APPS / ABOUT`에서 version, changelog 목록/상세, credits 표시
- input layout: `inputlayout`, `waitgesture`, `screenmenu`/`blindmenu` gesture action 확인
- input monitor: `TOOLS / INPUT MONITOR`와 `inputmonitor [events]` raw/gesture trace 확인
- log tail panel: HUD hidden 상태와 menu visible 상태에서 최근 native log 표시 확인
- serial reattach log: v75에서 idle-timeout 성공 로그를 억제해 LOG TAIL noise 감소
- serial noise: v76에서 짧은 `A`/`T`/`ATAT` fragment를 unknown command 없이 무시
- menu gate: 메뉴 표시 중 위험 명령 `[busy]` 차단, 관찰 명령 허용
- shell protocol: `cmdv1`/`A90P1` framed one-shot result와 `a90ctl.py` host wrapper 검증
- shell protocol: v74 `cmdv1x` length-prefixed argv encoding verified for whitespace args
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
7. safe storage/partition map 문서화 — v46 완료
8. 버튼 기반 on-screen menu 초안 구현 — v47 완료
9. USB gadget/device/sysfs map 문서화 — 완료
10. Toybox/static userland build + device validation — 완료
11. USB ACM reattach + NCM probe — v48 완료
12. 상태 HUD/menu TUI 개선 — v52 실기 표시 확인
13. menu-active serial busy gate + flash auto-hide — v53 완료
14. USB NCM persistent link + IPv4/IPv6 ping + host→device netcat 검증 — 완료
15. NCM host setup helper + TCP nettest helper — 완료
16. NCM TCP control helper — 완료
17. TCP control host wrapper — 완료
18. NCM + TCP control 5분 soak — 완료
19. unsolicited `AT` serial noise filter — v59 완료
20. opt-in boot-time NCM/tcpctl netservice — v60 완료
21. netservice stop/start UDC reconnect recovery — v60 완료
22. HUD CPU/GPU usage percent 표시 — v61 완료
23. CPU stress usage gauge + `/dev/null`/`/dev/zero` guard — v62 완료
24. 계층형 앱 메뉴 + CPU stress screen app — v63 완료
25. TEST 부팅 화면을 custom boot splash로 교체 — v64 완료
26. boot splash 잘림 방지 safe layout — v65 완료
27. semantic version + ABOUT/changelog/credits app — v66 완료
28. compact ABOUT typography + per-version changelog detail — v67 완료
29. HUD log tail + expanded changelog history — v68 완료
30. physical-button input gesture layout — v69 완료
31. input monitor app + raw/gesture trace — v70 완료
32. HUD/menu live log tail panel — v71 완료
33. display test screen + framebuffer color fix — v72 완료
34. shell protocol v1 + host wrapper — v73 완료
35. cmdv1x argument encoding — v74 완료
36. idle serial reattach log quieting — v75 완료
37. AT fragment serial noise hardening — v76 완료
38. display test multi-page app + cutout calibration — v77 완료
39. ext4 SD workspace + `mountsd` storage manager — v78 완료
40. boot-time SD health check + `/cache` fallback — v79 완료
41. PID1 source layout split into include modules — v80 완료
42. Config/util true `.c/.h` base module extraction — v81 완료

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

전체 문서 목록과 읽는 순서는 `docs/README.md`를 기준으로 한다.

바로 볼 문서:

- `docs/README.md`
- `docs/overview/PROJECT_STATUS.md`
- `docs/overview/PROGRESS_LOG.md`
- `docs/overview/VERSIONING.md`
- `CHANGELOG.md`
- `docs/operations/NATIVE_INIT_FLASH_AND_BRIDGE_GUIDE.md`
- `docs/operations/CLAUDE_NATIVE_INIT_RUNBOOK.md`
- `docs/plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md`
- `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V54_NCM_LINK_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V55_NCM_OPS_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V57_TCPCTL_HOST_WRAPPER_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V58_TCPCTL_SOAK_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V59_AT_NOISE_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V60_NETSERVICE_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V60_RECONNECT_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V61_CPU_GPU_USAGE_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V62_CPUSTRESS_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V63_APP_MENU_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V64_BOOT_SPLASH_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V65_SPLASH_SAFE_LAYOUT_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V66_ABOUT_VERSIONING_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V67_CHANGELOG_DETAILS_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V69_INPUT_LAYOUT_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V70_INPUT_MONITOR_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V72_DISPLAY_TEST_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V73_CMDV1_PROTOCOL_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V74_CMDV1X_ARG_ENCODING_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V75_QUIET_IDLE_REATTACH_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V76_AT_FRAGMENT_FILTER_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V77_DISPLAY_TEST_PAGES_2026-04-27.md`

`docs/plans/NATIVE_LINUX_RECHALLENGE_PLAN.md`와 `docs/plans/REVALIDATION_PLAN.md`는
진입점 확보 이전의 부트체인 재검증 기록으로 보존한다.

## Working Rules

- known-good boot image와 TWRP recovery 복구 경로를 항상 유지한다.
- 한 번에 하나의 boot/init 변수만 바꾼다.
- 새 boot image는 version, source path, SHA256, 실기 관찰 결과를 기록한다.
- USB ACM serial bridge를 기준 제어 채널로 사용한다.
- `/efs`, modem, RPMB, keymaster, keystore, bootloader 계열에는 쓰기 작업을 하지 않는다.
- `/data` 암호화 영역은 명확한 목적과 복구 계획 없이는 건드리지 않는다.
- 파티션은 by-name과 `/sys/class/block/<name>/dev` 기준으로 식별하고 major/minor를 hardcode하지 않는다.
- 로그와 실험 산출물은 우선 `/cache` 또는 repo 문서에 남긴다.
- ADB 안정화는 후순위로 두고, serial/HUD/log/menu 안정화를 먼저 진행한다.

## Safety Note

이 저장소에는 실제 플래시 대상 바이너리와 Samsung 전용 이미지가 포함될 수 있습니다.
실험 전에는 항상 현재 boot/recovery/vbmeta 상태와 복구 가능한 known-good 이미지를
확인한 뒤 진행합니다.

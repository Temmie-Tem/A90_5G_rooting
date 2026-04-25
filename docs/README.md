# Samsung Galaxy A90 5G - 현재 문서 인덱스

이 문서 트리는 `2026-04-26` 기준으로 다시 정렬했습니다.

초기 `native Linux rechallenge`의 핵심 진입점 확보 단계는 통과했고,
현재 문서의 중심은 **stock Android kernel 위에서 custom static `/init`를 실행해
작은 native userspace/runtime을 만드는 작업**입니다.

상단 `docs/`는 이제 다음 흐름에 필요한 문서를 유지합니다.

1. native init v65 기준 상태 고정
2. shell/HUD/log/menu 운영 안정화
3. 필요한 하드웨어/커널 경로만 역추적
4. BusyBox/network/SSH 같은 서버형 확장 가능성 검토

## 현재 기준점

- 디바이스: `SM-A908N`
- 빌드: `A908NKSU5EWA3`
- kernel: Samsung stock Android kernel `Linux 4.14.190`
- recovery: TWRP 사용 가능
- latest verified native init: `A90 Linux init v65`
- latest source: `stage3/linux_init/init_v65.c`
- latest boot image: `stage3/boot_linux_v65.img`
- known-good fallback: `stage3/boot_linux_v48.img`
- control channel: USB CDC ACM serial bridge
- display: custom boot splash 후 상태 HUD/menu 자동 전환
- input: VOL+/VOL-/POWER 버튼 확인
- logging: `/cache/native-init.log` 확인
- blocking cancel: q/Ctrl-C 취소 확인
- boot timeline: `timeline` 명령 확인
- HUD boot summary: `BOOT OK shell` 표시 확인
- run cancel: `/bin/a90sleep` helper 확인
- storage: `/cache` safe write, `userdata` conditional, critical partitions do-not-touch
- screen menu: 자동 메뉴, 앱 폴더, CPU stress app, serial `hide`/busy gate 확인
- USB map: ACM-only gadget `04e8:6861` / host `cdc_acm` 기준 문서화
- userland: `toybox 0.8.13` static ARM64 build와 `/cache/bin/toybox` 실기 실행 확인
- USB reattach: v48에서 ACM rebind 후 serial console 재연결 확인
- USB NCM: persistent composite, device `ncm0`, IPv4 ping, IPv6 link-local ping, host→device netcat 확인
- NCM ops: host interface 자동 탐지, ping, static TCP nettest 양방향 payload 검증 완료
- TCP control: NCM 위에서 `a90_tcpctl` ping/status/run/shutdown 검증 완료
- TCP wrapper/soak: `tcpctl_host.py smoke`와 5분/30사이클 `soak` 검증 완료
- serial noise: unsolicited `AT` modem probe line 무시 확인
- boot netservice: opt-in flag 기반 NCM/tcpctl 부팅 자동 시작과 rollback 검증 완료
- reconnect: v60 `netservice stop/start` software UDC 재열거 후 NCM/TCP 복구 확인
- HUD metrics: CPU/GPU 온도와 사용률 `%` 표시, CPU stress 검증 확인
- dev nodes: `/dev/null`/`/dev/zero` boot-time char device guard 확인
- app menu: APPS/MONITORING/TOOLS/LOGS/NETWORK/POWER 계층 메뉴와 CPU stress 시간 선택 확인
- boot splash: TEST 패턴 대신 `A90 NATIVE INIT` custom splash 표시 후 HUD 전환 확인
- splash layout: v65에서 긴 문구/footer 잘림 방지를 위해 안전 여백과 자동 축소 적용
- ADB: 보류

## 문서 읽는 순서

### 빠른 시작

1. `overview/PROJECT_STATUS.md` – 현재 상태와 다음 후보를 본다.
2. `operations/NATIVE_INIT_FLASH_AND_BRIDGE_GUIDE.md` – flash/bridge 조작 절차를 따른다.
3. `operations/CLAUDE_NATIVE_INIT_RUNBOOK.md` – 에이전트가 실수하지 않도록 운영 규칙을 확인한다.
4. `plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md` – 바로 이어서 할 작업 큐를 본다.

### 새 에이전트 인계

1. `operations/CLAUDE_HANDOFF_PROMPT.md`
2. `operations/CLAUDE_NATIVE_INIT_RUNBOOK.md`
3. `overview/PROJECT_STATUS.md`
4. `docs/README.md`

## 문서 카테고리

### 1. Overview

- `overview/PROJECT_STATUS.md` – 현재 기준점, 성공/실패 조건, 다음 작업 링크
- `overview/PROGRESS_LOG.md` – 날짜순 진행 로그

### 2. Operations

- `operations/CLAUDE_NATIVE_INIT_RUNBOOK.md` – 에이전트용 bridge/TWRP/custom init 작업 런북
- `operations/NATIVE_INIT_FLASH_AND_BRIDGE_GUIDE.md` – 사람이 직접 따라 하는 flash/bridge 운영 절차서
- `operations/CLAUDE_HANDOFF_PROMPT.md` – Claude에게 그대로 붙여 넣는 안전 작업 프롬프트

### 3. Plans

- `plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md` – v42 이후 역추적/셸/HUD/로그/네트워크 작업 목록
- `plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md` – v47 이후 바로 실행할 작업 큐
- `plans/MINIMAL_BOOT_ALLOWLIST_2026-04-22.txt` – 현재 최소 부팅 allowlist
- `plans/MINIMAL_BOOT_DELETE_CANDIDATES_2026-04-22.txt` – allowlist 기준 삭제 후보 스냅샷
- `plans/NATIVE_LINUX_RECHALLENGE_PLAN.md` – native init 진입점 확보 이전 로드맵, 보존 기록
- `plans/REVALIDATION_PLAN.md` – 부트체인 재검증 실행 체크리스트, 보존 기록

### 4. Current Native Init Reports

- `reports/NATIVE_INIT_V54_NCM_LINK_2026-04-25.md` – USB NCM persistent link, IPv4/IPv6 ping, host→device netcat 검증
- `reports/NATIVE_INIT_V55_NCM_OPS_2026-04-25.md` – NCM host setup helper와 양방향 TCP nettest helper 검증
- `reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md` – NCM 위의 작은 TCP command service helper 검증
- `reports/NATIVE_INIT_V57_TCPCTL_HOST_WRAPPER_2026-04-26.md` – TCP control host wrapper 검증
- `reports/NATIVE_INIT_V58_TCPCTL_SOAK_2026-04-26.md` – NCM + TCP control 5분 soak 검증
- `reports/NATIVE_INIT_V59_AT_NOISE_2026-04-26.md` – unsolicited `AT` serial noise filter 검증
- `reports/NATIVE_INIT_V60_NETSERVICE_2026-04-26.md` – opt-in boot-time NCM/tcpctl netservice 검증
- `reports/NATIVE_INIT_V60_RECONNECT_2026-04-26.md` – netservice stop/start UDC 재열거 복구 검증
- `reports/NATIVE_INIT_V61_CPU_GPU_USAGE_2026-04-26.md` – HUD/status CPU/GPU 사용률 `%` 표시 검증
- `reports/NATIVE_INIT_V62_CPUSTRESS_2026-04-26.md` – CPU stress 사용률 게이지와 `/dev/null`/`/dev/zero` guard 검증
- `reports/NATIVE_INIT_V63_APP_MENU_2026-04-26.md` – 계층형 앱 메뉴와 CPU stress screen app 검증
- `reports/NATIVE_INIT_V64_BOOT_SPLASH_2026-04-26.md` – TEST 화면을 custom boot splash로 교체한 검증
- `reports/NATIVE_INIT_V65_SPLASH_SAFE_LAYOUT_2026-04-26.md` – boot splash 잘림 방지 safe layout 검증
- `reports/NATIVE_INIT_V53_MENU_BUSY_2026-04-25.md` – menu-active serial busy gate와 flash auto-hide 검증
- `reports/NATIVE_INIT_V48_USB_REATTACH_NCM_2026-04-25.md` – USB reattach와 NCM probe 실기 검증
- `reports/NATIVE_INIT_USERLAND_CANDIDATES_2026-04-25.md` – static userland/BusyBox/toybox 후보 보고서
- `reports/NATIVE_INIT_USB_GADGET_MAP_2026-04-25.md` – USB gadget/host descriptor/ADB·network 후보 지도
- `reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md` – 저장소/파티션 안전 등급 보고서
- `reports/NATIVE_INIT_V47_SCREEN_MENU_2026-04-25.md` – 화면 메뉴 초안 실기 검증
- `reports/NATIVE_INIT_V45_RUN_LOG_2026-04-25.md` – `run` cancel과 log preservation 검증
- `reports/NATIVE_INIT_V44_HUD_BOOT_2026-04-25.md` – HUD boot summary 검증
- `reports/NATIVE_INIT_V43_TIMELINE_2026-04-25.md` – boot readiness timeline 검증
- `reports/NATIVE_INIT_V42_CANCEL_2026-04-25.md` – blocking command 취소 정책 검증
- `reports/NATIVE_INIT_V41_LOGGING_2026-04-25.md` – `/cache/native-init.log` 검증
- `reports/NATIVE_INIT_V40_BUILD_2026-04-25.md` – shell return code 정밀화 검증
- `reports/NATIVE_INIT_V39_STATUS_2026-04-25.md` – native init 기준 상태 보고서

### 5. Historical / Android Baseline Reports

- `reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md` – 기본 4조합, KG, fallback, Linux 후보 기록 시트
- `reports/STAGE3_EXPERIMENT_LOG_2026-04-23.md` – Stage 3 native init 진입 실험 로그
- `reports/NATIVE_INIT_SHELL_PROBE_2026-04-23.md` – 초기 USB ACM shell probe 기록
- `reports/ADB_FROM_LINUX_INIT_LOG_2026-04-23.md` – Linux init에서 ADB 시도 기록
- `reports/MINIMAL_BOOT_STATUS_2026-04-22.md` – 최소 부팅 상태와 남은 예외 패키지
- `reports/ADB_DEBLOAT_RESEARCH_2026-04-22.md` – 패키지별 제거 판단 근거
- `reports/ADB_DEBLOAT_2026-04-22.md` – debloat 적용 기록
- `reports/MINIMAL_BOOT_DELETE_RUN_2026-04-22.log` – 최소 부팅 삭제 실행 로그
- `reports/MINIMAL_BOOT_DELETE_RUN_AFTER_ROOT_2026-04-22.log` – root 이후 재실행 로그

### 6. Archive

- `archive/README.md` – 아카이브 인덱스
- `archive/legacy/` – 기존 2025 방향 문서 일괄 보관

## 현재 우선순위

1. shell return code 정밀화 — v40 완료
2. `/cache/native-init.log` 추가 — v41 완료
3. blocking command 취소 정책 통일 — v42 완료
4. boot readiness timeline 자동 기록 — v43 완료
5. HUD boot progress/error 표시 — v44 완료
6. recovery log preservation + `run` cancel helper — v45 완료
7. safe storage/partition map 문서화 — v46 완료
8. on-screen menu 초안 — v47 완료
9. USB gadget/device/sysfs map 문서화 — 완료
10. Toybox/static userland build + device validation — 완료
11. USB ACM reattach + NCM probe — v48 완료
12. v49 HUD image 격리 — boot prefix readback은 맞지만 Android userspace로 진입
13. 상태 HUD/menu TUI 개선 — v52 실기 표시 확인
14. menu-active serial busy gate + flash auto-hide — v53 완료
15. USB NCM persistent link + IPv4/IPv6 ping + host→device netcat 검증 — 완료
16. NCM host setup helper + TCP nettest helper — 완료
17. NCM TCP control helper — 완료
18. TCP control host wrapper — 완료
19. NCM + TCP control 5분 soak — 완료
20. unsolicited `AT` serial noise filter — v59 완료
21. opt-in boot-time NCM/tcpctl netservice — v60 완료
22. netservice stop/start UDC reconnect recovery — v60 완료
23. HUD CPU/GPU usage percent 표시 — v61 완료
24. CPU stress usage gauge + `/dev/null`/`/dev/zero` guard — v62 완료
25. 계층형 앱 메뉴 + CPU stress screen app — v63 완료
26. TEST 부팅 화면을 custom boot splash로 교체 — v64 완료
27. boot splash 잘림 방지 safe layout — v65 완료

패키지 최소화와 Android userspace 복구는 보조 실험으로만 다루고,
메인 목표는 **Android kernel 위에 반복 운용 가능한 native init 기반 최소 Linux 콘솔을 만드는 것**입니다.

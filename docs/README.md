# Samsung Galaxy A90 5G - 현재 문서 인덱스

이 문서 트리는 `2026-04-25` 기준으로 다시 정렬했습니다.

초기 `native Linux rechallenge`의 핵심 진입점 확보 단계는 통과했고,
현재 문서의 중심은 **stock Android kernel 위에서 custom static `/init`를 실행해
작은 native userspace/runtime을 만드는 작업**입니다.

상단 `docs/`는 이제 다음 흐름에 필요한 문서를 유지합니다.

1. native init v47 기준 상태 고정
2. shell/HUD/log/menu 운영 안정화
3. 필요한 하드웨어/커널 경로만 역추적
4. BusyBox/network/SSH 같은 서버형 확장 가능성 검토

## 현재 기준점

- 디바이스: `SM-A908N`
- 빌드: `A908NKSU5EWA3`
- kernel: Samsung stock Android kernel `Linux 4.14.190`
- recovery: TWRP 사용 가능
- latest native init: `A90 Linux init v47`
- latest source: `stage3/linux_init/init_v47.c`
- latest boot image: `stage3/boot_linux_v47.img`
- control channel: USB CDC ACM serial bridge
- display: TEST pattern 후 상태 HUD 자동 전환
- input: VOL+/VOL-/POWER 버튼 확인
- logging: `/cache/native-init.log` 확인
- blocking cancel: q/Ctrl-C 취소 확인
- boot timeline: `timeline` 명령 확인
- HUD boot summary: `BOOT OK shell` 표시 확인
- run cancel: `/bin/a90sleep` helper 확인
- storage: `/cache` safe write, `userdata` conditional, critical partitions do-not-touch
- screen menu: `menu`/`screenmenu` 화면 진입과 q 취소 확인
- USB map: ACM-only gadget `04e8:6861` / host `cdc_acm` 기준 문서화
- ADB: 보류

## 현재 작업 문서

### 1. Overview
- `overview/PROJECT_STATUS.md` – 현재 기준점, 성공/실패 조건, 다음 작업 링크
- `overview/PROGRESS_LOG.md` – 진행 로그

### 2. Plans
- `plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md` – v42 이후 역추적/셸/HUD/로그/네트워크 작업 목록
- `plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md` – v47 이후 바로 실행할 작업 큐
- `plans/NATIVE_LINUX_RECHALLENGE_PLAN.md` – native init 진입점 확보 이전 로드맵
- `plans/REVALIDATION_PLAN.md` – 부트체인 재검증 실행 체크리스트와 실험 절차
- `plans/MINIMAL_BOOT_ALLOWLIST_2026-04-22.txt` – 현재 최소 부팅 allowlist
- `plans/MINIMAL_BOOT_DELETE_CANDIDATES_2026-04-22.txt` – allowlist 기준 삭제 후보 스냅샷

### 3. Reports
- `reports/NATIVE_INIT_USB_GADGET_MAP_2026-04-25.md` – USB gadget/host descriptor/ADB·network 후보 지도
- `reports/NATIVE_INIT_V47_SCREEN_MENU_2026-04-25.md` – v47 화면 메뉴 초안 실기 검증 보고서
- `reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md` – v46 저장소/파티션 안전 등급 보고서
- `reports/NATIVE_INIT_V45_RUN_LOG_2026-04-25.md` – v45 `run` cancel과 log preservation 실기 검증 보고서
- `reports/NATIVE_INIT_V44_HUD_BOOT_2026-04-25.md` – v44 HUD boot summary 실기 검증 보고서
- `reports/NATIVE_INIT_V43_TIMELINE_2026-04-25.md` – v43 boot readiness timeline 실기 검증 보고서
- `reports/NATIVE_INIT_V42_CANCEL_2026-04-25.md` – v42 blocking command 취소 정책 실기 검증 보고서
- `reports/NATIVE_INIT_V41_LOGGING_2026-04-25.md` – v41 `/cache/native-init.log` 실기 검증 보고서
- `reports/NATIVE_INIT_V40_BUILD_2026-04-25.md` – v40 shell return code 정밀화 실기 검증 보고서
- `reports/NATIVE_INIT_V39_STATUS_2026-04-25.md` – v39 기준 native init 상태 보고서
- `reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md` – 기본 4조합, KG, fallback, Linux 후보 기록 시트
- `reports/MINIMAL_BOOT_STATUS_2026-04-22.md` – 최소 부팅 상태와 남은 예외 패키지
- `reports/ADB_DEBLOAT_RESEARCH_2026-04-22.md` – 패키지별 제거 판단 근거
- `reports/ADB_DEBLOAT_2026-04-22.md` – debloat 적용 기록

### 4. Archive
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

패키지 최소화와 Android userspace 복구는 보조 실험으로만 다루고,
메인 목표는 **Android kernel 위에 반복 운용 가능한 native init 기반 최소 Linux 콘솔을 만드는 것**입니다.

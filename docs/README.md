# Samsung Galaxy A90 5G - 현재 문서 인덱스

이 문서 트리는 `2026-04-23` 기준으로 리셋한 뒤,
이번 업데이트에서 `native Linux rechallenge` 중심으로 다시 정렬했습니다.

상단 `docs/`는 이제 다음 흐름에 필요한 문서만 유지합니다.

1. rooted baseline 고정
2. 부트체인 관찰 재구성
3. 보안 경계 분해
4. native Linux 진입 후보 재도전

## 현재 기준점

- 디바이스: `SM-A908N`
- 빌드: `A908NKSU5EWA3`
- Android 12 stock 기반
- patched AP 부팅 성공
- `Magisk 30.7` / `su` 동작 확인
- ADB 가능
- WPA2 Wi-Fi 등록 및 연결 가능
- 현재 `user 0` 패키지 수: `92`

## 현재 작업 문서

### 1. Overview
- `overview/PROJECT_STATUS.md` – 현재 기준점, 성공/실패 조건, 다음 작업
- `overview/PROGRESS_LOG.md` – 이번 rechallenge 트랙의 새 로그

### 2. Plans
- `plans/NATIVE_LINUX_RECHALLENGE_PLAN.md` – 이번 목표를 짧게 고정한 개요형 로드맵
- `plans/REVALIDATION_PLAN.md` – 단계 1~3 실행 체크리스트와 실험 절차
- `plans/MINIMAL_BOOT_ALLOWLIST_2026-04-22.txt` – 현재 최소 부팅 allowlist
- `plans/MINIMAL_BOOT_DELETE_CANDIDATES_2026-04-22.txt` – allowlist 기준 삭제 후보 스냅샷

### 3. Reports
- `reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md` – 기본 4조합, KG, fallback, Linux 후보 기록 시트
- `reports/MINIMAL_BOOT_STATUS_2026-04-22.md` – 최소 부팅 상태와 남은 예외 패키지
- `reports/ADB_DEBLOAT_RESEARCH_2026-04-22.md` – 패키지별 제거 판단 근거
- `reports/ADB_DEBLOAT_2026-04-22.md` – debloat 적용 기록

### 4. Archive
- `archive/README.md` – 아카이브 인덱스
- `archive/legacy/` – 기존 2025 방향 문서 일괄 보관

## 현재 우선순위

1. 기준점 A의 `boot`, `recovery`, `vbmeta`, 다운로드 모드 상태를 먼저 고정
2. `stock/patched AP` 와 `stock/TWRP recovery` 4조합을 같은 형식으로 재검증
3. `official binaries only`, `KG`, recovery fallback 조건을 다시 기록
4. 그 결과를 바탕으로 native Linux 진입 후보를 우선순위화

패키지 최소화는 보조 실험으로만 다루고,
메인 목표는 **rooted baseline 위에서 native Linux 경로를 다시 여는 것**입니다.

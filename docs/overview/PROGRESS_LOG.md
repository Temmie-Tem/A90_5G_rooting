# Native Linux Rechallenge Progress Log

## 2026-04-23

### 기준점 재설정
- 기존 2025 방향 문서를 `docs/archive/legacy/`로 이동
- 상단 문서 트리를 현재 rooted baseline 중심으로 재구성

### native Linux rechallenge 재개
- 공식 목표를 `부트체인 재검증 자체`에서 `native Linux 부팅 재도전`으로 다시 고정
- rooted baseline A를 모든 후속 실험의 유일한 출발점으로 설정
- debloat와 최소 패키지화는 메인 목표에서 분리하고 참고용 보조 실험으로 유지

### 실행 문서 정비
- `docs/plans/NATIVE_LINUX_RECHALLENGE_PLAN.md` 추가
- `docs/plans/REVALIDATION_PLAN.md`를 단계형 실행 체크리스트로 재작성
- `docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md` 작업 시트 추가
- `scripts/revalidation/`에 기준점 점검과 캡처용 헬퍼 추가

### 현재 rooted baseline
- patched AP 부팅 성공
- `Magisk 30.7` 확인
- `su` 동작 확인
- ADB 정상
- Wi-Fi 등록 및 연결 확인

### 최소 부팅 상태
- allowlist 재적용 후 `user 0` 패키지 수 `92`
- 남은 extra `3개`
  - `com.samsung.android.game.gos`
  - `com.samsung.android.themecenter`
  - `com.sec.android.sdhms`

### 비고
- `com.google.android.documentsui`는 `user 0` 제거 후 재부팅 유지 확인
- `com.google.android.partnersetup`는 제거 시도 후 재부팅 시 복귀
- `GOS`, `SDHMS`는 `pm uninstall --user 0` / `su -c` 모두 실질 제거 실패
- `ThemeCenter`는 `DELETE_FAILED_INTERNAL_ERROR`

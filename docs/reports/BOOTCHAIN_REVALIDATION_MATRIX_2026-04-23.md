# Bootchain Revalidation Matrix (2026-04-23)

이 문서는 `native Linux rechallenge`의 실제 작업 시트입니다.
자동 수집 가능한 값은 스크립트로 저장하고,
다운로드 모드 화면 값과 플래시 후 관찰값은 여기 수동으로 채웁니다.

## 기준점 A 스냅샷

현재 알려진 기준점:

- 디바이스: `SM-A908N`
- 빌드: `A908NKSU5EWA3`
- Android 12 stock 기반
- patched AP 부팅 성공
- `Magisk 30.7`
- ADB 가능
- `su` 가능
- Wi-Fi 가능
- `user 0` 패키지 수: `92`

다음 항목은 다음 실험 전 캡처 필요:

| Item | Value | Status |
| --- | --- | --- |
| boot backup path | | pending |
| recovery backup path | | pending |
| vbmeta backup path | | pending |
| KG | | pending |
| OEM LOCK | | pending |
| custom binary message | | pending |
| adb devices | rooted baseline confirmed | known |
| `sys.boot_completed` | rooted baseline confirmed | known |
| `su -c id` | rooted baseline confirmed | known |
| Wi-Fi status | rooted baseline confirmed | known |

권장 캡처 명령:

```bash
./scripts/revalidation/verify_device_state.sh
./scripts/revalidation/capture_baseline.sh --label baseline_a
```

## Stage 1: 기본 4조합 결과표

| ID | AP | Recovery | Factory reset | Flash result | Download mode / KG note | First boot | Recovery fallback | ADB | `su` | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | stock | stock | | pending | | | | | | |
| 2 | patched | stock | | pending | | | | | | |
| 3 | stock | TWRP | | pending | | | | | | |
| 4 | patched | TWRP | | pending | | | | | | |

## Stage 2: 보안 경계 분해

| Question | Observation | Conclusion |
| --- | --- | --- |
| boot image 수용 여부 | | pending |
| recovery 교체 허용 여부 | | pending |
| `official binaries only` 발생 조건 | | pending |
| KG 표기 변화와 결과 상관관계 | | pending |
| factory reset 영향 | | pending |

강제 결론 후보:

- `AP 변경은 허용, recovery 변경은 차단`
- `custom binary는 일부 경로에서만 허용`
- `KG/서명/복구 경계가 실제 차단 지점`

현재 선택 결론: `pending`

## Stage 3: native Linux 진입 후보

| Priority | Candidate path | Why it stays in scope | Result |
| --- | --- | --- | --- |
| 1 | `patched AP 유지 + Linux ramdisk/init 경로` | Stage 1~2 결과 반영 예정 | pending |
| 2 | `recovery 경로 활용` | Stage 1~2 결과 반영 예정 | pending |
| 3 | `vbmeta/부트 이미지 조합 변형` | Stage 1~2 결과 반영 예정 | pending |
| 4 | `TWRP` 기반 보조 경로 | 필요 시 사용 | pending |

## 종료 기준 추적

| Stage | Exit condition | Current state |
| --- | --- | --- |
| 1 | 4개 기본 조합 결과표 완성 | pending |
| 2 | 실제 차단 경계 결론 1개 이상 확보 | pending |
| 3 | Linux 진입 실증 또는 불가능 경계 재정의 | pending |

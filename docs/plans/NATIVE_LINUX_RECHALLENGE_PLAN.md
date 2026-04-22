# Samsung Galaxy A90 5G Native Linux Rechallenge Plan

## Summary

현재 프로젝트의 공식 목표는 `native Linux 부팅 재도전`으로 재설정합니다.
출발점은 이미 확보된 rooted baseline입니다.

기준점 A:

- `SM-A908N`
- `A908NKSU5EWA3`
- stock Android 12 기반
- patched AP 부팅 성공
- `Magisk 30.7` / `su` 가능
- ADB 가능
- Wi-Fi 가능

이 기준점 위에서, 먼저 `왜 어떤 조합은 통과하고 어떤 조합은 막히는지`를
부트체인 수준에서 다시 분해하고,
그 결과를 바탕으로 `native Linux 진입 가능 경로`를 다시 엽니다.

debloat와 패키지 최소화는 메인 목표가 아니라 참고용 보조 실험으로만 유지합니다.

상세 체크리스트는 `REVALIDATION_PLAN.md`,
실험 기록 시트는 `docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md`를 사용합니다.

## Implementation Plan

### 1. 기준점 고정

- 기준점 A를 모든 후속 실험의 유일한 출발점으로 고정
- 현재 `boot`, `recovery`, `vbmeta` 저장
- 다운로드 모드 화면의 `KG`, `OEM LOCK`, custom binary 문구 저장
- `adb`, `su`, `boot_completed`, `Wi-Fi` 상태 저장
- 기준점이 깨지면 즉시 `stock firmware + patched AP` 조합으로 복구

### 2. 1단계 재검증: 부트체인 관찰 재구성

같은 기록 형식으로 아래 조합을 다시 수행합니다.

1. `stock AP + stock recovery`
2. `patched AP + stock recovery`
3. `stock AP + TWRP`
4. `patched AP + TWRP`

각 조합에서 반드시 기록할 관찰값:

- 플래시 성공/실패
- 다운로드 모드 에러 문구
- 첫 부팅 성공 여부
- recovery fallback 여부
- ADB 여부
- `su` 여부

목표는 `안 된다`가 아니라 `어느 이미지 경계에서 차단되는지`를 표로 고정하는 것입니다.

### 3. 2단계 재검증: 보안 경계 분해

부트 실패 원인을 아래 층으로 나눠 기록합니다.

- boot image 수용 여부
- recovery 교체 허용 여부
- `official binaries only` 발생 조건
- KG 표기 변화와 결과 상관관계
- factory reset 유무가 결과에 미치는 영향

이 단계의 결론은 아래 셋 중 하나 이상으로 강제합니다.

- `AP 변경은 허용, recovery 변경은 차단`
- `custom binary는 일부 경로에서만 허용`
- `KG/서명/복구 경계가 실제 차단 지점`

### 4. 3단계 재도전: native Linux 진입 후보 실험

1, 2단계 결과를 바탕으로 native Linux 후보 경로를 우선순위화합니다.

우선순위는 다음 순서로 고정합니다.

1. `patched AP 유지 + Linux 진입 가능성 있는 ramdisk/init 경로`
2. `recovery 경로 활용`
3. `vbmeta/부트 이미지 조합 변형`
4. 필요 시 `TWRP` 기반 보조 진입 경로

이 단계의 목표는 완전 성공이 아니라 아래 셋 중 하나입니다.

- Android 대신 다른 초기 userspace를 실제로 실행
- recovery 기반으로 Linux 초기 진입 확인
- native 경로가 막히는 정확한 기술적 이유를 재현 가능한 형태로 확보

### 5. 보조 트랙

- debloat, 최소 패키지, RAM 절감은 메인 계획에서 분리
- 현재 `user 0 92개` 상태는 참고값으로만 보존
- 부트체인 실험 중 추가 삭제는 하지 않음
- 필요 시 기준점 비교 자료로만 사용

## Test Plan

모든 실험 공통 확인:

- `adb devices`
- `getprop sys.boot_completed`
- `adb shell su -c id`
- 필요 시 `cmd wifi status`

플래시 계열 실험 공통 판정:

- `PASS/FAIL`만 보지 않고 다운로드 모드 문구까지 기록
- 첫 부팅 성공 여부와 recovery fallback 여부를 분리 기록

단계별 종료 기준:

- 1단계 종료: 4개 기본 조합 결과표 완성
- 2단계 종료: 실제 차단 경계에 대한 결론 1개 이상 확보
- 3단계 종료: Linux 진입 후보 1개 이상 실증 또는 불가능 경계 재정의

## Assumptions

- rooted baseline은 현재 가장 신뢰할 수 있는 복구 앵커
- `stock firmware`와 `patched AP`로 복귀 가능하면 공격적인 테스트 허용
- `TWRP`, `vbmeta`, 비공식 이미지 테스트는 초기부터 계획에 포함
- `kgclient`, `klmsagent`, `knox.attestation`, telephony/IMS/network stack은 부트체인 실험 동안 유지
- 이번 문서는 짧은 개요형 로드맵으로 유지하고, 상세 체크리스트는 별도 실행 문서로 분리

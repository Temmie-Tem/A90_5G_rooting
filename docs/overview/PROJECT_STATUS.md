# Samsung Galaxy A90 5G - 현재 상태

## 기준점 A

**디바이스**: Samsung Galaxy A90 5G (`SM-A908N`)  
**빌드**: `A908NKSU5EWA3` / Android 12  
**루트 상태**: `Magisk 30.7`, `su` 동작 확인  
**ADB**: 정상  
**Wi-Fi**: ADB shell로 WPA2 네트워크 등록 및 연결 확인  
**현재 패키지 수**: `user 0` 기준 `92`

## 현재 확인된 사실

- stock 기반 Android 부팅 가능
- patched AP 부팅 가능
- `adb shell su -c id`로 root 획득 가능
- `getenforce`는 `Enforcing`
- 최소 부팅 allowlist 재적용 후에도 부팅 유지
- allowlist 밖에 남는 패키지는 현재 `3개`
  - `com.samsung.android.game.gos`
  - `com.samsung.android.themecenter`
  - `com.sec.android.sdhms`

## 현재 공식 목표

이번 트랙의 공식 목표는 `native Linux 부팅 재도전`입니다.

접근 순서는 고정합니다.

### 1. 기준점 유지
- 부팅 가능
- ADB 가능
- `su` 가능
- Wi-Fi 가능
- `stock firmware + patched AP`로 복구 가능

### 2. 1단계 재검증: 부트체인 관찰 재구성
- `stock AP + stock recovery`
- `patched AP + stock recovery`
- `stock AP + TWRP`
- `patched AP + TWRP`
- 각 조합에서 flash 결과, 다운로드 모드 문구, 첫 부팅, recovery fallback, ADB, `su`를 같은 형식으로 기록

### 3. 2단계 재검증: 보안 경계 분해
- boot image 수용 여부
- recovery 교체 허용 여부
- `official binaries only` 발생 조건
- KG 표기 변화와 결과 상관관계
- factory reset 유무 영향

### 4. 3단계 재도전: native Linux 진입 후보 실험
- `patched AP 유지 + Linux 진입 가능성 있는 ramdisk/init 경로`
- `recovery` 경로 활용
- `vbmeta/부트 이미지 조합 변형`
- 필요 시 `TWRP` 기반 보조 경로

## 성공 조건

- `adb devices` 정상
- `getprop sys.boot_completed = 1`
- `adb shell su -c id`가 `uid=0(root)`
- 필요 시 Wi-Fi 연결 가능

단계별 종료 기준:

- 1단계 종료: 4개 기본 조합 결과표 완성
- 2단계 종료: 실제 차단 경계에 대한 결론 1개 이상 확보
- 3단계 종료: 다른 초기 userspace 실행, recovery 기반 Linux 초기 진입, 또는 native 경로 차단 이유 중 하나를 재현 가능한 형태로 확보

## 실패 조건

- bootloop
- recovery fallback
- download mode로 자동 복귀
- ADB 상실
- `su` 상실

## 보류 대상

현재 기준점 안정성 때문에 아래 축은 우선 보류합니다.

- `kgclient`
- `klmsagent`
- `knox.attestation`
- `fmm`
- telephony / IMS / network stack

## 기준점 고정 항목

각 실험 시작 전 다음 값을 반드시 저장합니다.

- 현재 `boot`, `recovery`, `vbmeta`
- 다운로드 모드 화면의 `KG`, `OEM LOCK`, custom binary 문구
- `adb`, `su`, `boot_completed`, `Wi-Fi` 상태
- 필요 시 `ro.build.fingerprint`, `ro.boot.verifiedbootstate`

## 다음 작업

1. 기준점 A의 이미지와 다운로드 모드 값을 캡처
2. 4개 기본 조합 결과표를 `docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md`에 채우기
3. 1단계 결과로 보안 경계 결론을 강제
4. 그 결론을 바탕으로 native Linux 진입 후보 1개 이상 재시도
5. 기존 패키지 최소화는 참고값으로만 유지

# Bootchain Revalidation Execution Checklist

이 문서는 `native Linux rechallenge`를 위한 상세 실행 문서입니다.
개요형 로드맵은 `NATIVE_LINUX_RECHALLENGE_PLAN.md`에 두고,
여기서는 실제 실험 순서와 기록 방식을 고정합니다.

## 범위

현재 목표는 `안 된다`를 반복하는 것이 아니라,
`어느 이미지 경계에서 차단되는지`를 재현 가능한 형태로 고정하는 것입니다.

실험은 항상 기준점 A에서 시작합니다.

- `SM-A908N`
- `A908NKSU5EWA3`
- stock Android 12 기반
- patched AP 부팅 성공
- `Magisk 30.7`
- `su` 가능
- ADB 가능
- Wi-Fi 가능

## Stage 0: 기준점 캡처

실험 시작 전 아래 항목을 먼저 저장합니다.

1. 현재 `boot`, `recovery`, `vbmeta`
2. 다운로드 모드 화면의 `KG`, `OEM LOCK`, custom binary 문구
3. `adb`, `su`, `boot_completed`, `Wi-Fi` 상태
4. 필요 시 `ro.build.fingerprint`, `ro.boot.verifiedbootstate`

권장 순서:

```bash
./scripts/revalidation/verify_device_state.sh
./scripts/revalidation/capture_baseline.sh --label baseline_a
```

그리고 `docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md`의
기준점 섹션에 수동 관찰값을 채웁니다.

## Stage 1: 4개 기본 조합 재검증

아래 조합을 같은 형식으로 다시 수행합니다.

1. `stock AP + stock recovery`
2. `patched AP + stock recovery`
3. `stock AP + TWRP`
4. `patched AP + TWRP`

각 조합마다 반드시 기록할 값:

- flash 성공/실패
- 다운로드 모드 에러 문구
- 첫 부팅 성공 여부
- recovery fallback 여부
- ADB 여부
- `su` 여부
- factory reset 유무
- KG 표기 변화

기록 규칙:

- `PASS/FAIL`만 적지 않습니다.
- 다운로드 모드에 찍힌 실제 문구를 옮깁니다.
- 첫 부팅 실패와 recovery fallback을 별개로 기록합니다.
- 한 번에 하나의 변수만 바꿉니다.

## Stage 2: 보안 경계 분해

Stage 1 결과를 바탕으로 아래 층을 분리해 기록합니다.

1. boot image 수용 여부
2. recovery 교체 허용 여부
3. `official binaries only` 발생 조건
4. KG 표기 변화와 결과 상관관계
5. factory reset 유무가 결과에 미치는 영향

이 단계의 결론은 아래 셋 중 하나 이상으로 강제합니다.

- `AP 변경은 허용, recovery 변경은 차단`
- `custom binary는 일부 경로에서만 허용`
- `KG/서명/복구 경계가 실제 차단 지점`

## Stage 3: native Linux 진입 후보 재도전

Stage 1~2 결과가 정리되기 전에는 우선순위를 바꾸지 않습니다.

우선순위:

1. `patched AP 유지 + Linux 진입 가능성 있는 ramdisk/init 경로`
2. `recovery 경로 활용`
3. `vbmeta/부트 이미지 조합 변형`
4. 필요 시 `TWRP` 기반 보조 진입 경로

이 단계의 목표는 완전 성공만이 아닙니다.
아래 셋 중 하나를 얻으면 단계 종료로 봅니다.

- Android 대신 다른 초기 userspace를 실제로 실행
- recovery 기반으로 Linux 초기 진입 확인
- native 경로가 막히는 정확한 기술적 이유를 재현 가능한 형태로 확보

## 공통 확인 항목

모든 실험 공통 확인:

```bash
adb devices
adb shell getprop sys.boot_completed
adb shell su -c id
adb shell getprop ro.build.fingerprint
```

필요 시 추가:

```bash
adb shell cmd wifi status
adb shell ip addr show wlan0
adb shell getprop ro.boot.verifiedbootstate
adb shell getprop ro.boot.vbmeta.device_state
```

## 복구 규칙

기준점이 깨지면 즉시 다음 조합으로 복귀합니다.

- stock firmware 전체 플래시
- patched AP 재적용
- Magisk / `su` 재확인
- ADB / Wi-Fi 재확인

복구가 끝나기 전까지 다음 실험으로 넘어가지 않습니다.

## 보조 트랙

debloat, 최소 패키지화, RAM 절감은 메인 계획에서 분리합니다.

유지 원칙:

- 현재 `user 0 92개` 상태는 참고값으로만 보존
- 부트체인 실험 중 추가 삭제는 하지 않음
- 필요 시 기준점 비교 자료로만 사용
